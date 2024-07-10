library(terra)
library(eseis)
library(raster)
library(httpgd)

data("volcano")
data("rockfall")
setwd("/home/frieder/studium/SoSe24/RSE/pyseis/")

############### FMI ###############

## create 100 example reference parameter sets
ref_pars <- fmi_parameters(n = 10,
                            h_w = c(0.02, 1.20),
                            q_s = c(0.001, 8.000) / 2650,
                            d_s = 0.01,
                            s_s = 1.35,
                            r_s = 2650,
                            w_w = 6,
                            a_w = 0.0075,
                            f_min = 5,
                            f_max = 80,
                            r_0 = 6,
                            f_0 = 1,
                            q_0 = 10,
                            v_0 = 350,
                            p_0 = 0.55,
                            e_0 = 0.09,
                            n_0_a = 0.6,
                            n_0_b = 0.8,
                            res = 100)

write.csv(ref_pars, "R/output/R_fmi_par.csv")

## create corresponding reference spectra
ref_spectra <- fmi_spectra(parameters = ref_pars)

write.table(ref_spectra, "R/output/R_fmi_spec.csv")

## define water level and bedload flux time series
h <- c(0.01, 1.00, 0.84, 0.60, 0.43, 0.32, 0.24, 0.18, 0.14, 0.11)
q <- c(0.05, 5.00, 4.18, 3.01, 2.16, 1.58, 1.18, 0.89, 0.69, 0.54) / 2650
hq <- as.list(as.data.frame(rbind(h, q)))

## calculate synthetic spectrogram
psd <- do.call(cbind, lapply(hq, function(hq) {
    psd_turbulence <- eseis::model_turbulence(h_w = hq[1],
                                                d_s = 0.01,
                                                s_s = 1.35,
                                                r_s = 2650,
                                                w_w = 6,
                                                a_w = 0.0075,
                                                f = c(10, 70),
                                                r_0 = 5.5,
                                                f_0 = 1,
                                                q_0 = 18,
                                                v_0 = 450,
                                                p_0 = 0.34,
                                                e_0 = 0.0,
                                                n_0 = c(0.5, 0.8),
                                                res = 100,
                                                eseis = FALSE)$power
    psd_bedload <- eseis::model_bedload(h_w = hq[1],
                                        q_s = hq[2],
                                        d_s = 0.01,
                                        s_s = 1.35,
                                        r_s = 2650,
                                        w_w = 6,
                                        a_w = 0.0075,
                                        f = c(10, 70),
                                        r_0 = 5.5,
                                        f_0 = 1,
                                        q_0 = 18,
                                        v_0 = 450,
                                        x_0 = 0.34,
                                        e_0 = 0.0,
                                        n_0 = 0.5,
                                        res = 100,
                                        eseis = FALSE)$power

    ## combine spectra
    psd_sum <- psd_turbulence + psd_bedload

    ## return output
    return(10 * log10(psd_sum))
}))
# graphics::image(t(psd))

## invert empiric data set
X <- fmi_inversion(reference = ref_spectra, data = psd)

## plot model results
png("R/output/R_fmi_inversion0.png")
plot(X$parameters$q_s * 2650, type = "l")
dev.off()
png("R/output/R_fmi_inversion1.png")
plot(X$parameters$h_w, type = "l")
dev.off()

############### Spatial ###############

create_dem <- function(xmin, xmax, ymin, ymax, res, filepath) {
  width <- ceiling((xmax - xmin) / res[1])
  height <- ceiling((ymax - ymin) / res[2])
  print(paste("Creating DEM with dimensions:", width, "x", height))
  print(paste("DEM extent: (", xmin, ",", ymin, ") to (", xmax, ",", ymax, ")"))
  print(paste("Resolution:", paste(res, collapse = ", ")))
  
  dem <- matrix(0, nrow = height, ncol = width)
  x <- seq(0, 1, length.out = width)
  y <- seq(0, 1, length.out = height)
  X <- outer(y, x, FUN = function(a, b) b)
  Y <- outer(y, x, FUN = function(a, b) a)
  dem <- (sin(5 * X) * cos(5 * Y) +
            matrix(runif(height * width, min = 0, max = 0.1), 
            nrow = height)) * 100

  dem_raster <- raster(dem, xmn = xmin, xmx = xmax, ymn = ymin, ymx = ymax, 
                        crs = CRS("+proj=longlat +datum=WGS84"))
  writeRaster(dem_raster, filename = filepath, 
              format = "GTiff", overwrite = TRUE)

  print(paste("DEM created and saved to", filepath))
  return(filepath)
}

# create example data
if (!file.exists("R/output/R_spatial_synth_dem.tif")) {
  dem_filepath <- create_dem(
    0, 100, 0, 100, res = c(1, 1),
    filepath <- "R/output/R_spatial_synth_dem.tif")
} else {
  dem_filepath <- "R/output/R_spatial_synth_dem.tif"
}
dem <- terra::rast(dem_filepath)

# Define station coordinates (in the same coordinate system as the DEM)
# in example code from manual: cbind but throws error
stations <- data.frame(x = c(25,50,75),
                       y = c(25,90,75)) 

## plot example data
png("R/output/R_spatial_dist_0.png")
terra::plot(dem)
points(stations[,1:2])
dev.off()

## calculate distance matrices and stations distances
D <- spatial_distance(stations = stations, dem = dem, verbose = TRUE)

# convert to SpatRaster
n_maps <- length(D$maps)
maps <- list()
for(i in 1:n_maps){
  r <- rast(nrows = (D$maps[[i]]$ext[4] - D$maps[[i]]$ext[3]) / D$maps[[i]]$res[2],
            ncols = (D$maps[[i]]$ext[2] - D$maps[[i]]$ext[1]) / D$maps[[i]]$res[1],
            xmin = D$maps[[i]]$ext[1], xmax = D$maps[[i]]$ext[2],
            ymin = D$maps[[i]]$ext[3], ymax = D$maps[[i]]$ext[4],
            vals = D$maps[[i]]$val)
  # Set the coordinate reference system
  crs(r) <- ""

  # Add the raster to the list
  maps[[i]] <- r

  png(paste("R/output/R_spatial_dist_",i,".png",sep=""))
  terra::plot(r)
  points(stations)
  dev.off()
}
## save station distance matrix
write.csv(D$matrix, file = "R/output/R_spatial_dist_matrix.csv")

## create synthetic signal (source in towards lower left corner of the DEM)
s <- rbind(dnorm(x = 1:1000, mean = 500, sd = 50) * 100,
          dnorm(x = 1:1000, mean = 500, sd = 50) * 2,
          dnorm(x = 1:1000, mean = 500, sd = 50) * 1)

e <- eseis::spatial_amplitude(data = s, d_map = D$maps, v = 500, q = 50, f = 10)

## get most likely location coordinates (example contains two equal points)
e_max <- eseis::spatial_pmax(data = e)

## plot output
png("R/output/R_spatial_ampl.png")
terra::plot(e)
points(e_max[1], e_max[2], pch = 20)
points(stations[,1:2])
dev.off()

# save result e_max
write.csv(e_max, file= "R/output/R_spatial_pmax.png")

## plot output
png("R/output/R_spatial_ampl2.png")
terra::plot(e)
points(e_max[1], e_max[2], pch = 20)
points(stations[,1:2])
dev.off()

print("spatial_clip")
## clip values to those > quantile 0.5
volcano <- terra::rast(volcano)
volcano_clip <- spatial_clip(data = volcano, quantile = 0.5)

## plot clipped data set
png("R/output/R_spatial_clip.png")
terra::plot(volcano_clip)
dev.off()

### spatial_convert
## create lat lon coordinates
xy <- c(13, 55)

## define output coordinate systems
proj_in <- "+proj=longlat +datum=WGS84"
proj_out <- "+proj=utm +zone=32 +datum=WGS84"

## convert coordinate pair
xy_convert <- spatial_convert(data = xy, from = proj_in, to = proj_out)
write.csv(xy_convert, file = "R/output/R_spatial_convert_pair.csv")

## define set of coordinates
df_xy <- data.frame(x = c(10, 11), y = c(54, 55))

## convert set of coordinates
spatial_convert(data = df_xy, from = proj_in, to = proj_out)
write.csv(df_xy, file = "R/output/R_spatial_convert_set.csv")

print("spatial_track")
# create artificial data set
# Set seed for reproducibility
set.seed(123)

# Generate sample seismic data
num_stations <- 3
data_length <- 1000  # Length of the seismic signal data
data <- matrix(
  rnorm(num_stations * data_length),
  nrow = num_stations,
  ncol = data_length)

# Convert the data to a data frame for easier plotting
data_df <- data.frame(t(data))
colnames(data_df) <- paste0("Station_", 1:num_stations)
data_df$Time <- 1:data_length

x <- spatial_track(
    data = data_df,
    window = 3,
    overlap = 0.5,
    d_map = D$maps,
    v = 800,
    q = 40,
    f = 12,
    qt = 0.99,
    dt = 2
    )

############### Modeling ###############

## model amplitude
model_amplitude(data = s,
                source = c(500, 600),
                d_map = D$maps,
                v = 500,
                q = 50,
                f = 10)
model_amplitude(data = s,
                distance = c(254, 8254, 9280, 11667),
                model = "SurfBodySpreadAtten",
                v = 500,
                q = 50,
                f = 10,
                k = 0.5)

## model bedload
## calculate spectrum (i.e., fig. 1b in Tsai et al., 2012)
p_bedload <- model_bedload(d_s = 0.7,
                            s_s = 0.1,
                            r_s = 2650,
                            q_s = 0.001,
                            h_w = 4,
                            w_w = 50,
                            a_w = 0.005,
                            f = c(0.1, 20),
                            r_0 = 600,
                            f_0 = 1,
                            q_0 = 20,
                            e_0 = 0,
                            v_0 = 1295,
                            x_0 = 0.374,
                            n_0 = 1,
                            res = 100,
                            eseis = TRUE)
## plot spectrum
plot_spectrum(data = p_bedload,
                ylim = c(-170, -110))
## define empiric grain-size distribution
gsd_empiric <- data.frame(d = c(0.70, 0.82, 0.94, 1.06, 1.18, 1.30),
                            p = c(0.02, 0.25, 0.45, 0.23, 0.04, 0.00))
## calculate spectrum
p_bedload <- model_bedload(gsd = gsd_empiric,
                            r_s = 2650,
                            q_s = 0.001,
                            h_w = 4,
                            w_w = 50,
                            a_w = 0.005,
                            f = c(0.1, 20),
                            r_0 = 600,
                            f_0 = 1,
                            q_0 = 20,
                            e_0 = 0,
                            v_0 = 1295,
                            x_0 = 0.374,
                            n_0 = 1,
                            res = 100,
                            eseis = TRUE)

## plot spectrum
plot_spectrum(data = p_bedload,
                ylim = c(-170, -110))
## define mean and sigma for parametric distribution function
d_50 <- 1
sigma <- 0.1
## define raised cosine distribution function following Tsai et al. (2012)
d_1 <- 10^seq(log10(d_50 - 5 * sigma),
        log10(d_50 + 5 * sigma),
        length.out = 20)

sigma_star <- sigma / sqrt(1 / 3 - 2 / pi^2)

p_1 <- (1 / (2 * sigma_star) *
        (1 + cos(pi * (log(d_1) - log(d_50)) / sigma_star))) / d_1

p_1[log(d_1) - log(d_50) > sigma_star] <- 0
p_1[log(d_1) - log(d_50) < -sigma_star] <- 0

p_1 <- p_1 / sum(p_1)

gsd_raised_cos <- data.frame(d = d_1, p = p_1)

## model the turbulence-related power spectrum
P <- model_turbulence(d_s = 0.03, # 3 cm mean grain-size
                        s_s = 1.35, # 1.35 log standard deviation
                        r_s = 2650, # 2.65 g/cm^3 sediment density
                        h_w = 0.8, # 80 cm water level
                        w_w = 40, # 40 m river width
                        a_w = 0.0075, # 0.0075 rad river inclination
                        f = c(1, 200), # 1-200 Hz frequency range
                        r_0 = 10, # 10 m distance to the river
                        f_0 = 1, # 1 Hz Null frequency
                        q_0 = 10, # 10 quality factor at f = 1 Hz
                        v_0 = 2175, # 2175 m/s phase velocity
                        p_0 = 0.48, # 0.48 power law variation coefficient
                        n_0 = c(0.6, 0.8), # Greens function estimates
                        res = 1000) # 1000 values build the output resolution

## plot the power spectrum
plot_spectrum(data = P)