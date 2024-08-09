import argparse
import numpy as np
import pandas as pd


def model_bedload(
    gsd=None,
    d_s=None,
    s_s=None,
    r_s=None,
    q_s=None,
    h_w=None,
    w_w=None,
    a_w=None,
    f=(1, 100),
    r_0=None,
    f_0=None,
    q_0=None,
    e_0=None,
    v_0=None,
    x_0=None,
    n_0=None,
    n_c=None,
    res=100,
    adjust=True,
    **kwargs
):
    """
    Model the seismic spectrum due to bedload transport in rivers.

    This function calculates a seismic spectrum as predicted
    by the model of Tsai et al. (2012)
    for river bedload transport. It's based on the R implementation
    by Sophie Lagarde and Michael Dietze.

    Parameters:
    -----------
    gsd : array-like, optional
        Grain-size distribution function.
        Should be provided as a 2D array with two columns:
        grain-size class (in m) and weight/volume percentage per class.
    d_s : float, optional
        Mean sediment grain diameter (m). Alternative to gsd.
    s_s : float, optional
        Standard deviation of sediment grain diameter (m). Alternative to gsd.
    r_s : float
        Specific sediment density (kg/m^3)
    q_s : float
        Unit sediment flux (m^2/s)
    h_w : float
        Fluid flow depth (m)
    w_w : float
        Fluid flow width (m)
    a_w : float
        Fluid flow inclination angle (radians)
    f : tuple of float, optional
        Frequency range to be modelled (Hz). Default is (1, 100).
    r_0 : float
        Distance of seismic station to source (m)
    f_0 : float
        Reference frequency (Hz)
    q_0 : float
        Ground quality factor at f_0
    e_0 : float
        Exponent characterizing quality factor increase
        with frequency (dimensionless)
    v_0 : float
        Phase speed of the Rayleigh wave at f_0 (m/s)
    x_0 : float
        Exponent of the power law variation of Rayleigh wave
        velocities with frequency
    n_0 : float or array-like
        Green's function displacement amplitude coefficients
    n_c : float, optional
        Option to include single particle hops coherent in time
    res : int, optional
        Output resolution, i.e., length of the spectrum vector.
        Default is 100.
    adjust : bool, optional
        Option to adjust PSD for wide grain-size distributions.
        Default is True.
    **kwargs : dict, optional
        Additional parameters:
        - g : Gravitational acceleration (m/s^2). Default is 9.81.
        - r_w : Fluid specific density (kg/m^3). Default is 1000.
        - k_s : Roughness length (m). Default is 3 * d_s.
        - log_lim : Limits of grain-size distribution function template.
            Default is (0.0001, 100).
        - log_length : Length of grain-size distribution function template.
            Default is 10000.
        - nu : Specific density of the fluid (kg/m^3). Default is 1e-6.
        - power_d : Grain-size power exponent. Default is 3.
        - gamma : Gamma parameter, after Parker (1990). Default is 0.9.
        - s_c : Drag coefficient parameter. Default is 0.8.
        - s_p : Drag coefficient parameter. Default is 3.5.
        - c_1 : Inter-impact time scaling, after Sklar & Dietrich (2004).
            Default is 2/3.

    Returns:
    --------
    pandas.DataFrame
        A DataFrame with two columns:
        - 'frequency': The frequency vector (Hz)
        - 'power': The corresponding power spectral density

    Notes:
    ------
    When no user-defined grain-size distribution function is provided,
    the function calculates the raised cosine distribution function as
    defined in Tsai et al. (2012).

    The adjustment option is only relevant for wide grain-size distributions,
    i.e., s_s > 0.2.
    In such cases, the unadjusted version tends to underestimate seismic power.

    References:
    -----------
    Tsai, V. C., B. Minchew, M. P. Lamb, and J.-P. Ampuero (2012),
    A physical model for seismic noise generation from sediment transport
    in rivers, Geophys. Res. Lett., 39, L02404, doi:10.1029/2011GL050255.

    Examples:
    ---------
    >>> result = model_bedload(d_s=0.7, s_s=0.1, r_s=2650, q_s=0.001, h_w=4,
    ...                        w_w=50, a_w=0.005, f=(0.1, 20), r_0=600,
    ...                        f_0=1, q_0=20, e_0=0, v_0=1295,
    ...                        x_0=0.374, n_0=1, res=100)
    >>> import matplotlib.pyplot as plt
    >>> plt.semilogx(result[:, 0], 10 * np.log10(result[:, 1]))
    >>> plt.xlabel('Frequency (Hz)')
    >>> plt.ylabel('Power Spectral Density (dB)')
    >>> plt.show()
    """
    # Default values for additional parameters
    g = kwargs.get("g", 9.81)
    r_w = kwargs.get("r_w", 1000)
    k_s = kwargs.get("k_s", 3 * d_s)
    nu = kwargs.get("nu", 1e-6)
    power_d = kwargs.get("power_d", 3)
    gamma = kwargs.get("gamma", 0.9)
    s_c = kwargs.get("s_c", 0.8)
    s_p = kwargs.get("s_p", 3.5)
    c_1 = kwargs.get("c_1", 2 / 3)

    if gsd is None:
        x_log = np.logspace(np.log10(0.0001), np.log10(10), num=10000)
        s = s_s / np.sqrt(1 / 3 - 2 / np.pi**2)
        p_s = (
            1 / (2*s) * (1 + np.cos(np.pi * (np.log(x_log)-np.log(d_s)) / s))
        ) / x_log
        p_s[(np.log(x_log) - np.log(d_s)) > s] = 0
        p_s[(np.log(x_log) - np.log(d_s)) < -s] = 0
        x_log = x_log[p_s > 0]
        p_s = p_s[p_s > 0]
        if not adjust:
            p_s = p_s / np.sum(p_s)
    else:
        d_min = 10 ** np.ceil(np.log10(np.min(gsd[:, 0]) / 10))
        d_max = 10 ** np.ceil(np.log10(np.max(gsd[:, 0])))
        x_log = np.logspace(np.log10(d_min), np.log10(d_max), num=10000)
        p_s_gsd = np.interp(x_log, gsd[:, 0], gsd[:, 1], left=0, right=0)
        mask = ~np.isnan(p_s_gsd)
        x_log = x_log[mask]
        p_s_gsd = p_s_gsd[mask]
        f_density = np.sum(p_s_gsd * np.diff(x_log, prepend=x_log[0]))
        p_s = p_s_gsd / f_density
        d_s = x_log[np.argmin(np.abs(np.cumsum(p_s) - 0.5))]

    r_b = (r_s - r_w) / r_w
    u_s = np.sqrt(g * h_w * np.sin(a_w))
    u_m = 8.1 * u_s * (h_w / k_s) ** (1 / 6)
    chi = 0.407 * np.log(142 * np.tan(a_w))
    t_s_c50 = np.exp(
        2.59e-2*chi**4 + 8.94e-2*chi**3 + 0.142*chi**2 + 0.41*chi - 3.14
    )

    f_i = np.linspace(f[0], f[1], res)
    v_c = v_0 * (f_i / f_0) ** (-x_0)
    v_u = v_c / (1 + x_0)
    b = (2 * np.pi * r_0 * (1 + x_0) * f_i ** (1 + x_0 - e_0)) / (
        v_0 * q_0 * f_0 ** (x_0 - e_0)
    )
    x_b = 2 * np.log(1 + (1 / b)) * np.exp(-2 * b) + (1 - np.exp(-b)) * np.exp(
        -b
    ) * np.sqrt(2 * np.pi / b)

    s_x = np.log10((r_b * g * x_log**power_d) / nu**2)
    r_1 = (
        -3.76715
        + 1.92944 * s_x
        - 0.09815 * s_x**2
        - 0.00575 * s_x**3
        + 0.00056 * s_x**4
    )
    r_2 = (
        np.log10(1 - ((1 - s_c) / 0.85))
        - (1 - s_c) ** 2.3 * np.tanh(s_x - 4.6)
        + 0.3 * (0.5 - s_c) * (1 - s_c) ** 2 * (s_x - 4.6)
    )
    r_3 = (0.65 - ((s_c/2.83) * np.tanh(s_x-4.6))) ** (1 + ((3.5-s_p) / 2.5))
    w_1 = r_3 * 10 ** (r_2 + r_1)
    w_2 = (r_b * g * nu * w_1) ** (1 / 3)
    c_d = (4 / 3) * (r_b * g * x_log) / (w_2**2)
    t_s = (u_s**2) / (r_b * g * x_log)
    t_s_c = t_s_c50 * ((x_log / d_s) ** (-gamma))

    h_b = 1.44 * x_log * (t_s / t_s_c) ** 0.5
    h_b[h_b > h_w] = h_w
    u_b = 1.56 * np.sqrt(r_b * g * x_log) * (t_s / t_s_c) ** 0.56
    u_b[u_b > u_m] = u_m
    v_p = (4 / 3) * np.pi * (x_log / 2) ** 3
    m = r_s * v_p
    w_st = np.sqrt(4 * r_b * g * x_log / (3 * c_d))
    h_b_2 = 3 * c_d * r_w * h_b / (2 * r_s * x_log * np.cos(a_w))
    w_i = w_st * np.cos(a_w) * np.sqrt(1 - np.exp(-h_b_2))
    w_s = (h_b_2 * w_st * np.cos(a_w)) / (
        2 * np.log(np.exp(h_b_2 / 2) + np.sqrt(np.exp(h_b_2) - 1))
    )

    def calculate_psd(f, x_b, v_c, v_u):
        if n_c is not None:
            z = np.exp(-1j * n_c * np.pi * f * h_b / (c_1 * w_s))
            f_t = (np.abs(1 + z) ** 2) / 2
            psd_raw = (
                (c_1 * w_w * q_s * w_s * np.pi**2 * f**3 * m**2 * w_i**2 * x_b)
                * f_t
                / (v_p * u_b * h_b * r_s**2 * v_c**3 * v_u**2)
            )
        else:
            psd_raw = (
                c_1 * w_w * q_s * w_s * np.pi**2 * f**3 * m**2 * w_i**2 * x_b
            ) / (v_p * u_b * h_b * r_s**2 * v_c**3 * v_u**2)

        if adjust:
            psd_f = np.sum(p_s * psd_raw * n_0**2 *
                           np.diff(x_log, prepend=x_log[0]))
        else:
            psd_f = np.sum(p_s * psd_raw * n_0**2)
        return psd_f

    z = np.array([calculate_psd(f, x, v, u)
                  for f, x, v, u in zip(f_i, x_b, v_c, v_u)])

    # Return the result as a pandas DataFrame
    return pd.DataFrame({"frequency": f_i, "power": z})


# Example usage
# Example
if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Reference model bedload example.')
    parser.add_argument(
        '--show-plot',
        action='store_true',
        help='Show the plot of the results')

    # Parse command line arguments
    args = parser.parse_args()

    import model_turbulence

    # Set parameters
    d_s = 0.7
    s_s = 0.1
    r_s = 2650
    q_s = 0.001
    h_w = 4
    w_w = 50
    a_w = 0.005
    r_0 = 600
    f_0 = 1
    q_0 = 20
    e_0 = 0
    v_0 = 1295
    x_0 = 0.374
    n_0 = 1

    # Run the model
    result = model_bedload(
        d_s=d_s,
        s_s=s_s,
        r_s=r_s,
        q_s=q_s,
        h_w=h_w,
        w_w=w_w,
        a_w=a_w,
        f=(0.1, 20),
        r_0=r_0,
        f_0=f_0,
        q_0=q_0,
        e_0=e_0,
        v_0=v_0,
        x_0=x_0,
        n_0=n_0,
        res=1000,
    )

    # Plot the result
    print(result.head())
    print("\nShape of the result:", result.shape)
    if args.show_plot:
        title = "Seismic Spectrum due to Bedload Transport"
        model_turbulence.plot_spectrum(result, title)
    else:
        print('Skipping Bedload Transport plot display.')
