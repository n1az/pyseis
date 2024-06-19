import numpy as np
import rasterio
from rasterio import features
from shapely.geometry import Point, LineString

def spatial_distance(stations, dem, topography=True, maps=True, matrix=True, aoi=None, verbose=False):
    """
    Calculate topography-corrected distances for seismic waves.

    The function calculates topography-corrected distances either between
    seismic stations or from seismic stations to pixels of an input raster.

    Topography correction is necessary because seismic waves can only travel
    on the direct path as long as they are within solid matter. When the
    direct path is through air, the wave can only travel along the surface
    of the landscape. The function accounts for this effect and returns the
    corrected travel distance data set.

    Parameters:
    stations (numpy.ndarray): Numeric matrix of length two, x- and y-coordinates
        of the seismic stations to be processed (column-wise organized). The
        coordinates must be in metric units, such as the UTM system and
        match with the reference system of the `dem`.
    dem (rasterio.io.DatasetReader): Digital elevation model (DEM) to be processed.
        The DEM must be in metric units, such as the UTM system and match with the
        reference system of the coordinates of `stations`.
    topography (bool, optional): Option to enable topography correction. Default is True.
    maps (bool, optional): Option to enable/disable calculation of distance maps. Default is True.
    matrix (bool, optional): Option to enable/disable calculation of interstation distances. Default is True.
    aoi (list or tuple, optional): Bounding coordinates of the area of interest to process, in the form
        [x0, x1, y0, y1].
    verbose (bool, optional): Option to show extended function information as the function is running.
        Default is False.

    Returns:
    dict: Dictionary containing distance maps (list of raster metadata dictionaries) and station distance matrix
        (numpy.ndarray).

    Author: Md Niaz Morshed

    Examples:
    >>> import rasterio
    >>> from scipy.ndimage import gaussian_filter
    >>> dem = gaussian_filter(np.fromfile('volcano.dat', sep="\n").reshape(99, 99), sigma=1)
    >>> dem = dem * 10
    >>> stations = np.array([[200, 220], [700, 700]])
    >>> result = spatial_distance(stations, dem)
    >>> print(result['matrix'])
    [[    0.          556.06398783]
     [556.06398783     0.        ]]
    """
    # PART 0 - check input data
    if not isinstance(dem, rasterio.io.DatasetReader):
        raise ValueError("DEM must be a rasterio.io.DatasetReader object!")

    dem_array = dem.read(1)
    if np.isnan(dem_array).any():
        raise ValueError("DEM contains NaN values!")

    xy_dem = rasterio.transform.xy(dem.transform, dem_array.shape)

    if np.any(np.min(stations[:, 0]) < np.min(xy_dem[:, 0])) or \
       np.any(np.max(stations[:, 0]) > np.max(xy_dem[:, 0])) or \
       np.any(np.min(stations[:, 1]) < np.min(xy_dem[:, 1])) or \
       np.any(np.max(stations[:, 1]) > np.max(xy_dem[:, 1])):
        raise ValueError("Some station coordinates are outside DEM extent!")

    if aoi is None:
        aoi_ext = [np.min(xy_dem[:, 0]), np.max(xy_dem[:, 0]), np.min(xy_dem[:, 1]), np.max(xy_dem[:, 1])]
    else:
        aoi_ext = aoi

    if np.any(aoi_ext[0] < np.min(xy_dem[:, 0])) or \
       np.any(aoi_ext[1] > np.max(xy_dem[:, 0])) or \
       np.any(aoi_ext[2] < np.min(xy_dem[:, 1])) or \
       np.any(aoi_ext[3] > np.max(xy_dem[:, 1])):
        raise ValueError("AOI extent is beyond DEM extent!")

    # PART 1 - calculate distance maps
    if maps:
        aoi_array = np.zeros_like(dem_array)
        aoi_array[(xy_dem[:, 0] >= aoi_ext[0]) & (xy_dem[:, 0] <= aoi_ext[1]) &
                  (xy_dem[:, 1] >= aoi_ext[2]) & (xy_dem[:, 1] <= aoi_ext[3])] = 1

        maps = []
        for i in range(stations.shape[0]):
            if verbose:
                print(f"Processing map for station {i+1}")

            xy_stat = stations[i]
            distances = []
            for j in range(dem_array.shape[0]):
                for k in range(dem_array.shape[1]):
                    if aoi_array[j, k] == 1:
                        line_length = np.sqrt((xy_stat[0] - xy_dem[j, k, 0]) ** 2 + (xy_stat[1] - xy_dem[j, k, 1]) ** 2)
                        n_int = round(line_length / dem.res[0])
                        if n_int == 0:
                            n_int = 1

                        xy_pts = np.array([np.linspace(xy_stat[0], xy_dem[j, k, 0], n_int),
                                           np.linspace(xy_stat[1], xy_dem[j, k, 1], n_int)]).T

                        z_int = [dem_array[rasterio.transform.rowcol(dem.transform, xy_pt[0], xy_pt[1])] for xy_pt in xy_pts]

                        z_dir = np.linspace(z_int[0], z_int[-1], n_int)

                        if topography:
                            z_dir[z_dir > np.array(z_int)] = np.array(z_int)[z_dir > np.array(z_int)]

                        line_length = np.sqrt((xy_stat[0] - xy_dem[j, k, 0]) ** 2 +
                                              (xy_stat[1] - xy_dem[j, k, 1]) ** 2 +
                                              np.sum(np.abs(np.diff(z_dir))) ** 2)
                    else:
                        line_length = np.nan

                    distances.append(line_length)

            maps.append({'crs': dem.crs,
                         'ext': dem.bounds,
                         'res': dem.res,
                         'val': np.array(distances).reshape(dem_array.shape)})
    else:
        maps = [None] * stations.shape[0]

    if matrix:
        if verbose:
            print("Processing station distances")

        station_points = [Point(x, y) for x, y in stations]
        xyz_stat = [(x, y, dem_array[rasterio.transform.rowcol(dem.transform, x, y)]) for x, y in xy_dem]

        M = np.zeros((stations.shape[0], stations.shape[0]))
        for i in range(len(xyz_stat)):
            dx_stations = [xyz_stat[j][0] - xyz_stat[i][0] for j in range(len(xyz_stat))]
            dy_stations = [xyz_stat[j][1] - xyz_stat[i][1] for j in range(len(xyz_stat))]
            dt_stations = [np.sqrt(dx ** 2 + dy ** 2) for dx, dy in zip(dx_stations, dy_stations)]

            for j in range(len(dt_stations)):
                n_int = round(dt_stations[j] / dem.res[0])
                if n_int == 0:
                    n_int = 1

                xy_pts = np.array([np.linspace(xyz_stat[i][0], xyz_stat[j][0], n_int),
                                   np.linspace(xyz_stat[i][1], xyz_stat[j][1], n_int)]).T

                z_int = [dem_array[rasterio.transform.rowcol(dem.transform, xy_pt[0], xy_pt[1])] for xy_pt in xy_pts]

                z_dir = np.linspace(z_int[0], z_int[-1], n_int)

                if topography:
                    z_dir[z_dir > np.array(z_int)] = np.array(z_int)[z_dir > np.array(z_int)]

                path_length = np.sum(np.sqrt(np.diff(xy_pts[:, 0]) ** 2 +
                                             np.diff(xy_pts[:, 1]) ** 2 +
                                             np.diff(z_dir) ** 2))

                M[i, j] = path_length
    else:
        M = None

    return {'maps': maps, 'matrix': M}

# Example
# if __name__ == "__main__":
#     # Example usage
#     import rasterio
#     from scipy.ndimage import gaussian_filter
#     import numpy as np

#     # Load example DEM
#     dem = gaussian_filter(np.fromfile('volcano.dat', sep="\n").reshape(99, 99), sigma=1)
#     dem = dem * 10
#     dem_dataset = rasterio.open('path/to/dem.tif', 'w', driver='GTiff',
#                                 height=dem.shape[0], width=dem.shape[1],
#                                 count=1, dtype=dem.dtype,
#                                 crs='+proj=utm +zone=10 +ellps=WGS84 +datum=WGS84 +units=m +no_defs',
#                                 transform=rasterio.transform.from_origin(0, 0, 10, 10))
#     dem_dataset.write(dem, 1)
#     dem_dataset.close()

#     # Define example stations
#     stations = np.array([[200, 220], [700, 700]])

#     # Calculate distance matrices and station distances
#     result = spatial_distance(stations, dem_dataset, verbose=True)

#     # Print station distance matrix
#     print(result['matrix'])