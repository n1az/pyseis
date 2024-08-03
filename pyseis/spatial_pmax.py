import numpy as np
import rasterio


def spatial_pmax(data):
    """
    Get the most likely source location.

    Parameters:
    data (numpy.ndarray or rasterio.io.MemoryFile): Spatial data with
                                                source location estimates.

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
        max_locations = [np.array(rasterio.transform.xy(transform,
                                                        *max_indices))]
    else:
        # Use array indices as coordinates
        max_locations = [np.array(max_indices)]

    return max_locations


# Example
if __name__ == "__main__":
    # Example usage with numpy array
    example_data = np.random.rand(100, 100)
    max_locations = spatial_pmax(example_data)
    print("Most likely source location(s) for numpy array:")
    for loc in max_locations:
        print(loc)

    # Example usage with rasterio MemoryFile
    from rasterio.transform import from_origin
    from rasterio.io import MemoryFile

    with MemoryFile() as memfile:
        with memfile.open(
            driver="GTiff",
            height=100,
            width=100,
            count=1,
            dtype=np.float32,
            crs="+proj=latlong",
            transform=from_origin(0, 0, 1, 1),
        ) as dataset:
            data = np.random.rand(100, 100).astype(np.float32)
            dataset.write(data, 1)

        max_locations = spatial_pmax(memfile)
        print("\nMost likely source location(s) for rasterio MemoryFile:")
        for loc in max_locations:
            print(loc)
