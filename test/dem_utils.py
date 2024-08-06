import numpy as np
import rasterio
from rasterio.transform import from_origin


def create_dem(xmin, xmax, ymin, ymax, res, filepath):
    """
    Create a synthetic Digital Elevation Model (DEM) and save it to a file.

    Args:
        xmin (float): Minimum x-coordinate of the DEM.
        xmax (float): Maximum x-coordinate of the DEM.
        ymin (float): Minimum y-coordinate of the DEM.
        ymax (float): Maximum y-coordinate of the DEM.
        res (tuple): Resolution of the DEM in (x, y) direction.
        filepath (str): Path to save the DEM file.

    Returns:
        str: Path to the saved DEM file.
    """
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
    dem = (np.sin(5 * X) * np.cos(5 * Y) + np.random.rand(
        height,
        width
        ) * 0.1) * 100

    with rasterio.open(
        filepath,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=dem.dtype,
        crs="+proj=latlong",
        transform=transform,
    ) as dst:
        dst.write(dem, 1)

    print(f"DEM created and saved to {filepath}")
    return filepath
