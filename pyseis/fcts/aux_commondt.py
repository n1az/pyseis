def aux_commondt(data, dt=None):
    """
    Identify highest common sampling interval
    
    The function compares the sampling intervals of a list of objects and 
    identifies the highest common sampling interval (dt) as well as the 
    aggregation factors for each object needed to reach this common sampling interval.
    
    :param data: List of objects or vector of sampling intervals to be checked for highest common sampling interval
    :param dt: Numeric value, user-defined common sampling frequency for which aggregation factors shall be computed
    :return: Dictionary with elements 'dt' (highest common sampling interval) and 'agg' (aggregation factors for each of the input data sets to reach the common sampling interval)
    """

    # Check/set input data
    if isinstance(data, list):
        # Get classes of list elements
        list_classes = [type(d).__name__ for d in data]
        
        # Check if list elements are eseis objects
        if not all(cls == "eseis" for cls in list_classes):
            raise ValueError("Input data does not entirely consist of eseis objects!")
        else:
            # Extract sampling intervals
            dt_data = [d.meta.dt for d in data]
    elif isinstance(data, (list, np.ndarray)) and all(isinstance(d, (int, float)) for d in data):
        dt_data = data
    else:
        raise ValueError("Input data must be either eseis object or vector of dt values!")

    # Define function to find greatest common divisor
    def gcd(x):
        from math import gcd as gcd_single
        from functools import reduce
        return reduce(gcd_single, x)

    # Find common divisor
    if dt is None:
        dt_common = gcd(dt_data)
    else:
        dt_common = dt

    # Find aggregation factors
    aggregation = [dt_common / d for d in dt_data]

    # Generate output data set
    data_out = {'dt': dt_common, 'agg': aggregation}

    # Return output
    return data_out
