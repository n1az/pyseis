import rasterio
from scipy.ndimage import gaussian_filter
import numpy as np

# Load example DEM
dem = gaussian_filter(np.fromfile('volcano.dat', sep="\n").reshape(99, 99), sigma=1)
dem = dem * 10
dem_dataset = rasterio.open('path/to/dem.tif', 'w', driver='GTiff',
                            height=dem.shape[0], width=dem.shape[1],
                            count=1, dtype=dem.dtype,
                            crs='+proj=utm +zone=10 +ellps=WGS84 +datum=WGS84 +units=m +no_defs',
                            transform=rasterio.transform.from_origin(0, 0, 10, 10))
dem_dataset.write(dem, 1)
dem_dataset.close()

# Define example stations
stations = np.array([[200, 220], [700, 700]])

# Calculate distance matrices and station distances
result = spatial_distance(stations, dem_dataset, verbose=True)

# Print station distance matrix
print(result['matrix'])