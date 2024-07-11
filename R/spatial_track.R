library(eseis)
library(terra)

data("volcano")
dem <- terra::rast(volcano)
dem <- dem * 10
terra::ext(dem) <- terra::ext(dem) * 10
terra::ext(dem) <-terra::ext(dem) + c(510, 510, 510, 510)

## define example stations
stations <- cbind(c(200, 700), c(220, 700))

## plot example data
terra::plot(dem)
points(stations[,1], stations[,2])

## calculate distance matrices and stations distances
D <- spatial_distance(
    stations = stations,
    dem = dem
    )

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
}

terra::plot(maps[[1]])

## show station distance matrix
print(D$matrix)

## calculate with AOI and in verbose mode
aoi = c(0, 200, 0, 200)
D <- spatial_distance(
    stations = stations,
    dem = dem,
    verbose = TRUE,
    aoi = aoi
)
## plot distance map for station 2
terra::plot(maps[[1]])

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

# time step
dt = 2

spatial_track(
    data_df,
    coupling,
    window,
    overlap = 0,
    D$maps,
    v = 800,
    q = 40,
    f = 12,
    qt = 0.99,
    dt = dt,
    model = "SurfSpreadAtten",
    verbose = FALSE,
    plot = FALSE
)
