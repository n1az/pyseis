import numpy as np
from pyseis import model_turbulence, model_bedload


def calculate_psd(hq_pair):
    """
    Calculate synthetic spectrogram
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
