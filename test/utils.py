import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.io import MemoryFile
from scipy.stats import norm


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

    x = np.linspace(0, 1, width)
    y = np.linspace(0, 1, height)
    X, Y = np.meshgrid(x, y)
    dem = (np.sin(
        5 * X
        ) * np.cos(5 * Y) + np.random.rand(
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


def convert_to_memoryfile(map_data):
    """
    Convert a distance map dictionary to a MemoryFile object.

    Args:
        map_data (dict): Dictionary containing the distance map data.

    Returns:
        rasterio.io.MemoryFile: Opened MemoryFile dataset.
    """
    profile = {
        "driver": "GTiff",
        "height": map_data["values"].shape[0],
        "width": map_data["values"].shape[1],
        "count": 1,
        "dtype": map_data["values"].dtype,
        "crs": map_data["crs"],
        "transform": map_data["transform"],
    }
    memfile = MemoryFile()
    with memfile.open(**profile) as dataset:
        dataset.write(map_data["values"], 1)
    return memfile.open()


def create_signal():
    # Create synthetic signal
    x = np.arange(1, 1001)
    data = np.vstack(
        [
            norm.pdf(x, 500, 50) * 100,
            norm.pdf(x, 500, 50) * 2,
            norm.pdf(x, 500, 50) * 1,
        ]
    )
    return data
