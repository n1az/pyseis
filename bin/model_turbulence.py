import numpy as np
import pandas as pd
from scipy.constants import g, pi
from scipy.integrate import quad


def model_turbulence(d_s, s_s, r_s, h_w, w_w, a_w, f, res=100, eseis=False, **kwargs):
    """
    Model the seismic spectrum due to hydraulic turbulence.

    Parameters:
    d_s : float
        Mean sediment grain diameter (m)
    s_s : float
        Standard deviation of sediment grain diameter (m)
    r_s : float
        Specific sediment density (kg/m^3)
    h_w : float
        Fluid flow depth (m)
    w_w : float
        Fluid flow width (m)
    a_w : float
        Fluid flow inclination angle (radians)
    f : list or np.ndarray
        Frequency range to be modeled. If of length two, it represents the lower and upper limit.
        If it contains more than two values, it is interpreted as the actual frequency vector.
    res : int, optional
        Resolution of the frequency vector, default is 100.
    eseis : bool, optional
        Whether to return an 'eseis' object (not implemented in this script).

    Returns:
    pd.DataFrame
        DataFrame containing frequency and power.
    Author: Shahriar Shohid Choudhury
    """

    # Set default parameters
    params = {
        'c': 0.5,
        'g': g,
        'k': 0.5,
        'k_s': 3 * d_s,
        'h': 3 * d_s / 2,
        'e_0': 0,
        'r_w': 1000,
        'c_w': 0.5,
    }

    params.update(kwargs)

    if len(f) == 2:
        f_seq = np.logspace(np.log10(f[0]), np.log10(f[1]), res)
    else:
        f_seq = np.array(f)

    u_p_0 = (params['c'] * params['g'] * h_w * np.sin(a_w)) ** (1 / 2)
    z = params['k'] * w_w / (3 * (params['k_s'] ** (2 / 3)))
    n_0 = [1, 1]
    p_0 = params['e_0']
    v_0 = 1

    def psi_function(d):
        return (1 / (1 + (2 * d_s / d) ** (4 / 3))) ** 2

    psi = psi_function(d_s)

    l = (0.1 * d_s, 10 * d_s)

    def phi_function(f, u_p_0, s, d_s):
        def integrand(d):
            a = ((1 / (1 + (2 * f * d / u_p_0) ** (4 / 3))) ** 2)
            b = ((1 / (2 * s * d) * (1 + np.cos(pi * (np.log(d) - np.log(d_s)) / s)))) * d ** 2
            return a * b

        return quad(integrand, l[0], l[1])[0]

    phi = [phi_function(f, u_p_0, s_s, d_s) for f in f_seq]

    p = ((n_0[0] ** 2 + n_0[1] ** 2) *
         (params['k'] * w_w / (3 * (params['k_s'] ** (2 / 3)))) *
         ((params['r_w'] / r_s) ** 2) *
         (((1 + p_0) ** 2) / ((f_seq ** (5 * p_0)) * v_0 ** 5)) *
         z * psi * phi *
         (f_seq ** ((4 / 3) + 5 * p_0)) *
         (params['g'] ** (7 / 3)) *
         (np.sin(a_w) ** (7 / 3)) *
         (params['c_w'] ** 2) * (h_w ** (7 / 3)))

    P = pd.DataFrame({'frequency': f_seq, 'power': p})

    if eseis:
        # Placeholder for eseis object creation (not implemented)
        pass

    return P
