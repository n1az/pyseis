import numpy as np
from pyseis import (
    fmi_parameters,
    model_bedload,
    model_turbulence,
    fmi_spectra,
    fmi_inversion,
)


def create_reference_parameters():
    """
    Create example reference parameter sets.

    Returns:
        list: A list of parameter dictionaries.
    """
    return fmi_parameters.fmi_parameters(
        n=2,
        h_w=[0.02, 2.00],
        q_s=[0.001, 50.000 / 2650],
        d_s=0.01,
        s_s=1.35,
        r_s=2650,
        w_w=6,
        a_w=0.0075,
        f_min=5,
        f_max=80,
        r_0=6,
        f_0=1,
        q_0=10,
        v_0=350,
        p_0=0.55,
        e_0=0.09,
        n_0_a=0.6,
        n_0_b=0.8,
        res=100,
    )


def create_reference_spectra(ref_pars):
    """
    Create corresponding reference spectra.

    Args:
        ref_pars (list): A list of parameter dictionaries.

    Returns:
        list: A list of spectrum dictionaries.
    """
    return fmi_spectra.fmi_spectra(parameters=ref_pars, n_cores=2)


def calculate_psd(hq_pair):
    """
    Calculate Power Spectral Density for a given water
    level and bedload flux pair.

    Args:
        hq_pair (tuple): A tuple containing water level and bedload flux.

    Returns:
        numpy.ndarray: The calculated PSD.
    """
    h, q = hq_pair
    try:
        psd_turbulence = model_turbulence.model_turbulence(
            h_w=h,
            d_s=0.01,
            s_s=1.35,
            r_s=2650,
            w_w=6,
            a_w=0.0075,
            f=(10, 70),
            r_0=5.5,
            f_0=1,
            q_0=18,
            v_0=450,
            p_0=0.34,
            n_0=(0.5, 0.8),
            res=100,
        )["power"]

        psd_bedload = model_bedload.model_bedload(
            h_w=h,
            q_s=q,
            d_s=0.01,
            s_s=1.35,
            r_s=2650,
            w_w=6,
            a_w=0.0075,
            f=(10, 70),
            r_0=5.5,
            f_0=1,
            q_0=18,
            v_0=450,
            x_0=0.34,
            e_0=0.0,
            n_0=0.5,
            res=100,
        )["power"]

        psd_sum = psd_turbulence + psd_bedload
        return 10 * np.log10(psd_sum)
    except Exception as e:
        print(f"Error calculating PSD for h={h}, q={q}: {str(e)}")
        return np.full(100, np.nan)


def perform_inversion(ref_spectra, psd):
    """
    Perform FMI inversion.

    Args:
        ref_spectra (list): A list of reference spectra.
        psd (numpy.ndarray): The power spectral density data.

    Returns:
        dict: The inversion results.
    """
    return fmi_inversion.fmi_inversion(reference=ref_spectra, data=psd)
