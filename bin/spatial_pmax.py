import numpy as np

def spatial_pmax(data):
    """
    Get the most likely source location.

    Parameters:
    data (numpy.ndarray): Spatial data with source location estimates.

    Returns:
    numpy.ndarray: Coordinates of the most likely source location(s).

    Example:
    >>> import numpy as np
    >>> data = np.random.rand(100, 100)
    >>> spatial_pmax(data)
    array(...)  # Coordinates of the maximum value(s) in the data

    Author: Lamia Islam
    """
    # Get the maximum value(s) in the data
    max_values = np.where(data == np.max(np.max(data)))

    # Convert the indices to coordinates
    max_locations = [np.array([row, col]) for row, col in zip(*max_values)]

    return max_locations

# Example
# if __name__ == "__main__":
#     # Example usage
#     example_data = np.random.rand(100, 100)
#     max_locations = spatial_pmax(example_data)
#     print("Most likely source location(s):")
#     for loc in max_locations:
#         print(loc)