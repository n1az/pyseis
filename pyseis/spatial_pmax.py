import argparse
import numpy as np
import rasterio
from pyseis import spatial_amplitude


def spatial_pmax(data):
    """
    Get the most likely source location.

    Parameters:
    data (numpy.ndarray or rasterio.io.MemoryFile): Spatial data with source
                                                    location estimates.

    Returns:
    numpy.ndarray: Coordinates of the most likely source location(s).

    Example:
    >>> import numpy as np
    >>> data = np.random.rand(100, 100)
    >>> spatial_pmax(data)
    array(...)  # Coordinates of the maximum value(s) in the data

    """
    if isinstance(data, rasterio.io.MemoryFile):
        with data.open() as dataset:
            data_array = dataset.read(1)
            transform = dataset.transform
    elif isinstance(data, np.ndarray):
        data_array = data
        transform = None
    else:
        raise ValueError(
            "Input data must be either a numpy array or a rasterio MemoryFile"
        )

    # Get the indices of the maximum value(s) in the data
    max_indices = np.unravel_index(np.argmax(data_array), data_array.shape)

    # Convert indices to coordinates
    if transform:
        # Use rasterio's transform to get real-world coordinates
        max_locations = [np.array(rasterio.transform.xy(
            transform, *max_indices
        ))]
    else:
        # Use array indices as coordinates
        max_locations = [np.array(max_indices)]

    return max_locations


# Example
if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Spatial Pmax example.')
    parser.add_argument(
        '--size',
        type=int,
        default=100,
        help='Size of numpy array')
    parser.add_argument(
        '--use-mem',
        action='store_true',
        help='Use memoryfile')

    # Parse command line arguments
    args = parser.parse_args()

    # Example usage with numpy array
    if args.use_mem:
        e_max = spatial_pmax(
            spatial_amplitude.example_run()
        )
        print("Most likely source location(s) for memoryfile:")
        for loc in e_max:
            print(loc)
    else:
        example_data = np.random.rand(args.size, args.size)
        max_locations = spatial_pmax(example_data)
        print("Most likely source location(s) for numpy array:")
        for loc in max_locations:
            print(loc)
