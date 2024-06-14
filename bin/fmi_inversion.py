import numpy as np
import pandas as pd
from joblib import Parallel, delayed

def fmi_inversion(reference, data, n_cores=1):
    """
    Invert fluvial data set based on reference spectra catalogue.

    The fluvial model inversion (FMI) routine uses a predefined look-up table 
    with reference spectra to identify those spectra that fit the empirical 
    data set best, and returns the corresponding target variables and fit 
    errors.

    Note that the frequencies of the empiric and modelled data sets must 
    match.

    Parameters:
        reference (list): List containing dictionaries with precalculated model spectra.
        data (np.ndarray or pd.DataFrame): Empiric spectra which are used to identify the best 
                                           matching target parameters of the reference data set.
        n_cores (int): Number of CPU cores to use. Disabled by setting to 1. Default is 1.
  
    Returns:
        dict: Dictionary containing the inversion results with parameters and rmse.
    """

    if isinstance(data, pd.DataFrame):
        psd_list = [data[col].values for col in data.columns]
    else:
        psd_list = [data[:, i] for i in range(data.shape[1])]

    reference_spectra = np.vstack([x['power'] for x in reference])
    reference_parameters = pd.DataFrame([x['pars'] for x in reference])

    def invert_single_spectrum(psd, reference_spectra):
        if not np.isnan(psd).any():
            d = reference_spectra - psd
            rmse = np.sqrt(np.mean(d**2, axis=1))
            rmse_min = np.min(rmse)
            mod_best = np.argmin(rmse)
            rmse_f = np.sqrt((reference_spectra[mod_best, :] - psd)**2)
        else:
            mod_best = np.nan
            rmse_f = np.full_like(psd, np.nan)
            rmse = np.nan
            rmse_min = np.nan

        return {'rmse_f': rmse_f, 'rmse': rmse_min, 'mod_best': mod_best}

    if n_cores > 1:
        inversion = Parallel(n_jobs=n_cores)(delayed(invert_single_spectrum)(psd, reference_spectra) for psd in psd_list)
    else:
        inversion = [invert_single_spectrum(psd, reference_spectra) for psd in psd_list]

    model_best = [inv['mod_best'] for inv in inversion]
    parameters_out = pd.DataFrame([reference_parameters.iloc[int(mb)] for mb in model_best if not np.isnan(mb)], columns=reference_parameters.columns)

    rmse = np.vstack([inv['rmse_f'] for inv in inversion])

    return {'parameters': parameters_out, 'rmse': rmse}

# Example usage (assuming the functions fmi_parameters and fmi_spectra are defined, as they are not provided in the original R code):

# ## create 100 example reference parameter sets
# ref_pars = fmi_parameters(n=10, h_w=[0.02, 1.20], q_s=[0.001, 8.000] / 2650, d_s=0.01, s_s=1.35, r_s=2650, w_w=6, a_w=0.0075, f_min=5, f_max=80, r_0=6, f_0=1, q_0=10, v_0=350, p_0=0.55, e_0=0.09, n_0_a=0.6, n_0_b=0.8, res=100)
# 
# ## create corresponding reference spectra
# ref_spectra = fmi_spectra(parameters=ref_pars)
# 
# ## define water level and bedload flux time series
# h = np.array([0.01, 1.00, 0.84, 0.60, 0.43, 0.32, 0.24, 0.18, 0.14, 0.11])
# q = np.array([0.05, 5.00, 4.18, 3.01, 2.16, 1.58, 1.18, 0.89, 0.69, 0.54]) / 2650
# hq = pd.DataFrame({'h': h, 'q': q}).T
# 
# ## calculate synthetic spectrogram
# psd = np.column_stack([calculate_spectrogram(hq) for _, hq in hq.iteritems()])
# 
# ## invert empiric data set
# X = fmi_inversion(reference=ref_spectra, data=psd)
# 
# ## plot model results
# import matplotlib.pyplot as plt
# plt.plot(X['parameters']['q_s'] * 2650, type='l')
# plt.plot(X['parameters']['h_w'], type='l')

