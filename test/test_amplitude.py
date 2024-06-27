import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import rasterio
from rasterio.transform import from_origin
import os
import sys

# Add the parent directory to the path to import custom functions
script_directory = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_directory, '..'))

from bin import spatial_amplitude, spatial_distance, spatial_pmax

# Function to create a synthetic DEM and save it to a file
def create_dem(xmin, xmax, ymin, ymax, res, filepath):
    width = int((xmax - xmin) / res[0])
    height = int((ymax - ymin) / res[1])
    print(f"Creating DEM with dimensions: {width}x{height}")
    print(f"DEM extent: ({xmin}, {ymin}) to ({xmax}, {ymax})")
    print(f"Resolution: {res}")
    
    dem = np.zeros((height, width), dtype=np.float32)
    transform = from_origin(xmin, ymax, res[0], res[1])

    # Add some random terrain to make it more realistic
    x = np.linspace(0, 1, width)
    y = np.linspace(0, 1, height)
    X, Y = np.meshgrid(x, y)
    dem = (np.sin(5 * X) * np.cos(5 * Y) + np.random.rand(height, width) * 0.1) * 100

    with rasterio.open(
        filepath, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=dem.dtype,
        crs='+proj=latlong',
        transform=transform,
        bounds=(xmin, ymin, xmax, ymax)  # Explicitly set bounds
    ) as dst:
        dst.write(dem, 1)
    
    print(f"DEM created and saved to {filepath}")
    return filepath

# Main code
# Define station coordinates
sta = np.array([[1000, 1000], [9000, 1000], [5000, 9000]])
sta_ids = ['A', 'B', 'C']

# Create and save synthetic DEM
dem_filepath = create_dem(0, 10000, 0, 10000, res=(100, 100), filepath='synthetic_dem.tif')

# Read the DEM back in as a rasterio object
with rasterio.open(dem_filepath) as dem:
    print(f"Loaded DEM bounds: {dem.bounds}")
    print(f"Loaded DEM shape: {dem.shape}")
    print(f"Loaded DEM transform: {dem.transform}")
    


# Read the DEM back in as a rasterio object
with rasterio.open(dem_filepath) as dem:
    transform = dem.transform

    # Ensure station coordinates are within DEM bounds
    dem_bounds = dem.bounds
    for coord in sta:
        if not (dem_bounds.left <= coord[0] <= dem_bounds.right and dem_bounds.bottom <= coord[1] <= dem_bounds.top):
            raise ValueError("Some station coordinates are outside DEM extent!")
    # After creating the transform in create_dem function
    print(f"Created transform: {transform}")

    # Create synthetic signal
    x = np.arange(1, 1001)
    s = np.vstack([
        norm.pdf(x, 500, 50) * 100,
        norm.pdf(x, 500, 50) * 2,
        norm.pdf(x, 500, 50) * 1
    ])

    # Plot DEM and stations
    plt.figure(figsize=(10, 10))
    plt.imshow(dem.read(1), extent=(dem_bounds.left, dem_bounds.right, dem_bounds.bottom, dem_bounds.top), origin='lower', cmap='terrain')
    for i, (x, y) in enumerate(sta):
        plt.plot(x, y, 'ro')
        plt.text(x, y, sta_ids[i], color='white', fontsize=12, ha='right', va='bottom')
    plt.colorbar(label='Elevation')
    plt.title('DEM with Station Locations')
    plt.xlabel('X coordinate')
    plt.ylabel('Y coordinate')
    plt.show()
    
    print(f"Main code - DEM bounds: {dem.bounds}")
    print(f"Main code - Station coordinates:\n{sta}")

    # Calculate spatial distance maps and inter-station distances
    D = spatial_distance.spatial_distance(sta, dem)

    # Locate signal
    e = spatial_amplitude.spatial_amplitude(s, D, v=500, q=50, f=10)

    # Get most likely location coordinates
    e_max = spatial_pmax.spatial_pmax(e)

    # Plot output
    plt.imshow(e, extent=(dem_bounds.left, dem_bounds.right, dem_bounds.bottom, dem_bounds.top), origin='lower')
    plt.plot(e_max[0], e_max[1], 'ro')  # Adjust if needed based on your function output format
    plt.plot(sta[:, 0], sta[:, 1], 'bo')
    plt.show()
