import math
import numpy as np
from multiprocessing import Pool, cpu_count

def model_turbulence(d_s, s_s, r_s, h_w, w_w, a_w, f, r_0, f_0, q_0, v_0, p_0, n_0, res, eseis=False):
    # Placeholder for the actual implementation of model_turbulence
    # Assuming it returns a dictionary with 'frequency' and 'power'
    frequency = np.linspace(f[0], f[1], res)
    power = np.random.rand(res)  # Random values for demonstration
    return {'frequency': frequency, 'power': power}

def model_bedload(d_s, s_s, r_s, q_s, h_w, w_w, a_w, f, r_0, f_0, q_0, e_0, v_0, x_0, n_0, res, eseis=False):
    # Placeholder for the actual implementation of model_bedload
    # Assuming it returns a dictionary with 'frequency' and 'power'
    frequency = np.linspace(f[0], f[1], res)
    power = np.random.rand(res)  # Random values for demonstration
    return {'frequency': frequency, 'power': power}

def calculate_spectrum(parameters):
    # Model spectrum due to water flow
    p_turbulence = model_turbulence(
        d_s=parameters['d_s'], s_s=parameters['s_s'], r_s=parameters['r_s'],
        h_w=parameters['h_w'], w_w=parameters['w_w'], a_w=parameters['a_w'],
        f=[parameters['f_min'], parameters['f_max']], r_0=parameters['r_0'],
        f_0=parameters['f_0'], q_0=parameters['q_0'], v_0=parameters['v_0'],
        p_0=parameters['p_0'], n_0=[parameters['n_0_a'], parameters['n_0_b']],
        res=parameters['res'], eseis=False
    )

    # Model spectrum due to bedload impacts
    p_bedload = model_bedload(
        d_s=parameters['d_s'], s_s=parameters['s_s'], r_s=parameters['r_s'],
        q_s=parameters['q_s'], h_w=parameters['h_w'], w_w=parameters['w_w'],
        a_w=parameters['a_w'], f=[parameters['f_min'], parameters['f_max']],
        r_0=parameters['r_0'], f_0=parameters['f_0'], q_0=parameters['q_0'],
        e_0=parameters['e_0'], v_0=parameters['v_0'], x_0=parameters['p_0'],
        n_0=parameters['n_0_a'], res=parameters['res'], eseis=False
    )

    # Combine model outputs
    p_combined = p_turbulence
    p_combined['power'] = p_turbulence['power'] + p_bedload['power']

    # Convert linear to log scale
    p_turbulence_log = p_turbulence
    p_bedload_log = p_bedload
    p_combined_log = p_combined

    p_turbulence_log['power'] = 10 * np.log10(p_turbulence['power'])
    p_bedload_log['power'] = 10 * np.log10(p_bedload['power'])
    p_combined_log['power'] = 10 * np.log10(p_combined['power'])

    # Return model outputs
    return {
        'parameters': parameters,
        'frequency': p_combined_log['frequency'],
        'power': p_combined_log['power']
    }

def fmi_spectra(parameters, n_cores=1):
    """
    Create reference model spectra catalogue.

    Parameters:
    parameters (list): List of dictionaries containing model parameters 
                       for which the spectra shall be calculated.
    n_cores (int): Number of CPU cores to use. Disabled by setting to 1. Default is 1.

    Returns:
    list: List containing the calculated reference spectra and the corresponding input parameters.
    Note that the spectra are given in dB for a seamless comparison with the empirical PSD data,
    while the original output of the models are in linear scale.
    """

    if n_cores > 1:
        n_cores = min(n_cores, cpu_count())

        with Pool(n_cores) as pool:
            spectra = pool.map(calculate_spectrum, parameters)
    else:
        spectra = list(map(calculate_spectrum, parameters))

    return spectra

# Example usage
ref_pars = [
    {
        'h_w': [0.02, 2.00], 'q_s': [0.001, 50.000 / 2650], 'd_s': 0.01, 's_s': 1.35,
        'r_s': 2650, 'w_w': 6, 'a_w': 0.0075, 'f_min': 5, 'f_max': 80, 'r_0': 6,
        'f_0': 1, 'q_0': 10, 'v_0': 350, 'p_0': 0.55, 'e_0': 0.09, 'n_0_a': 0.6,
        'n_0_b': 0.8, 'res': 100
    },
    {
        'h_w': [0.02, 2.00], 'q_s': [0.001, 50.000 / 2650], 'd_s': 0.01, 's_s': 1.35,
        'r_s': 2650, 'w_w': 6, 'a_w': 0.0075, 'f_min': 5, 'f_max': 80, 'r_0': 6,
        'f_0': 1, 'q_0': 10, 'v_0': 350, 'p_0': 0.55, 'e_0': 0.09, 'n_0_a': 0.6,
        'n_0_b': 0.8, 'res': 100
    }
]

ref_spectra = fmi_spectra(parameters=ref_pars, n_cores=2)
