import argparse
import numpy as np
from rasterio.io import MemoryFile
from pyseis import spatial_migrate


def spatial_clip(data, quantile, replace=np.nan, normalise=True):
    """
    Clip values of spatial data.

    The function replaces raster values based on different thresholds.

    Parameters:
    data (rasterio.io.DatasetReader): Spatial data set to be processed.
    quantile (float): Quantile value below which raster values are clipped.
    replace (float, optional): Replacement value. Default is `np.nan`.
    normalise (bool, optional): Optionally normalize values above threshold
                                quantile between 0 and 1. Default is True.

    Returns:
    rasterio.io.DatasetReader: Data set with clipped values.

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
        raster_data = (raster_data - np.nanmin(raster_data)) / (
            np.nanmax(raster_data) - np.nanmin(raster_data)
        )

    # Create a new raster with clipped values
    profile = data.profile.copy()
    with MemoryFile() as memfile:
        with memfile.open(**profile) as clipped_raster:
            clipped_raster.write(raster_data, 1)
        # Open the dataset in read mode
        clipped_dataset = memfile.open()

    return clipped_dataset


# Example
def example_run(quantile=0.75):
    quantile = quantile

    migrated_result = spatial_migrate.example_run()

    # Apply spatial clipping to the migrated result
    clipped_result = spatial_clip(
        migrated_result,
        quantile=0.75,
        replace=np.nan,
        normalise=True
        )

    return clipped_result


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Spatial Migrate example.')
    parser.add_argument(
        '--q',
        type=float,
        default=0.75,
        help='Quantile value below which raster values are clipped')

    # Parse command line arguments
    args = parser.parse_args()
    example_run(args.q)
