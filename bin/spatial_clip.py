import numpy as np
import rasterio
from rasterio.io import MemoryFile

def spatial_clip(data, quantile, replace=np.nan, normalise=True):
    """
    Clip values of spatial data.

    The function replaces raster values based on different thresholds.

    Parameters:
    data (rasterio.io.DatasetReader): Spatial data set to be processed.
    quantile (float): Quantile value below which raster values are clipped.
    replace (float, optional): Replacement value. Default is `np.nan`.
    normalise (bool, optional): Optionally normalize values above threshold quantile between 0 and 1. Default is True.

    Returns:
    rasterio.io.DatasetReader: Data set with clipped values.

    Author: Lamia Islam
    """
    # Check/set parameters
    if quantile is None:
        quantile = 1.0

    # Read raster data
    raster_data = data.read(1)

    # Replace values
    threshold = np.quantile(raster_data[~np.isnan(raster_data)], quantile)
    raster_data[raster_data < threshold] = replace

    # Optionally normalize data set
    if normalise:
        raster_data = (raster_data - np.nanmin(raster_data)) / (np.nanmax(raster_data) - np.nanmin(raster_data))

    # Create a new raster with clipped values
    profile = data.profile.copy()
    with MemoryFile() as memfile:
        with memfile.open(**profile) as clipped_raster:
            clipped_raster.write(raster_data, 1)
        # Open the dataset in read mode
        clipped_dataset = memfile.open()

    return clipped_dataset