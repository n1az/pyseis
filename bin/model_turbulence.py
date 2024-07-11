import numpy as np
import pandas as pd
from scipy import integrate
import matplotlib.pyplot as plt

def model_turbulence(
    d_s,
    s_s,
    r_s=2650,
    h_w=0.8,  # Added default value for h_w
    w_w=40,   # Added default value for w_w
    a_w=0.0075,  # Added default value for a_w
    f=(1, 100),
    r_0=10,   # Added default value for r_0
    f_0=1,    # Added default value for f_0
    q_0=10,   # Added default value for q_0
    v_0=2175, # Added default value for v_0
    p_0=0.48, # Added default value for p_0
    n_0=(0.6, 0.8),  # Changed to tuple for consistency
    res=1000,
    **kwargs
):
    """
    Model the seismic spectrum due to hydraulic turbulence.

    This function calculates the seismic spectrum as predicted by the model
    of Gimbert et al. (2014) for hydraulic turbulence.

    Parameters:
    -----------
    d_s : float
        Mean sediment grain diameter (m)
    s_s : float
        Standard deviation of sediment grain diameter (m)
    r_s : float, optional
        Specific sediment density (kg/m^3). Default is 2650.
    h_w : float, optional
        Fluid flow depth (m). Default is 0.8.
    w_w : float, optional
        Fluid flow width (m). Default is 40.
    a_w : float, optional
        Fluid flow inclination angle (radians). Default is 0.0075.
    f : tuple or list, optional
        Frequency range to be modelled. If a tuple of length two, it represents
        the lower and upper limit. If a list, it's interpreted as the actual
        frequency vector. Default is (1, 100).
    r_0 : float, optional
        Distance of seismic station to source. Default is 10.
    f_0 : float, optional
        Reference frequency (Hz). Default is 1.
    q_0 : float, optional
        Ground quality factor at f_0. Default is 10.
    v_0 : float, optional
        Phase velocity of the Rayleigh wave at f_0 (m/s). Default is 2175.
    p_0 : float, optional
        Variation exponent of Rayleigh wave velocities with frequency. Default is 0.48.
    n_0 : tuple, optional
        Greens function displacement amplitude coefficients. Default is (0.6, 0.8).
    res : int, optional
        Output resolution, i.e., length of the spectrum vector. Default is 1000.
    **kwargs : dict
        Additional parameters that can be modified:
        - g : Gravitational acceleration (m/s^2). Default is 9.81.
        - k : Kolmogorov constant. Default is 0.5.
        - k_s : Roughness length (m). Default is 3 * d_s.
        - h : Reference height of the measurement (m). Default is k_s / 2.
        - e_0 : Exponent of Q increase with frequency. Default is 0.
        - r_w : Specific density of the fluid (kg/m^3). Default is 1000.
        - c_w : Instantaneous fluid-grain friction coefficient. Default is 0.5.

    Returns:
    --------
    pd.DataFrame
        A DataFrame containing the frequency and power columns.

    Example:
    --------
    >>> result = model_turbulence(d_s=0.03, s_s=1.35)
    >>> print(result.head())
    """
    # Extract additional arguments with default values
    g = kwargs.get('g', 9.81)
    k = kwargs.get('k', 0.5)
    k_s = kwargs.get('k_s', 3 * d_s)
    h = kwargs.get('h', k_s / 2)
    e_0 = kwargs.get('e_0', 0)
    r_w = kwargs.get('r_w', 1000)
    c_w = kwargs.get('c_w', 0.5)

    # Define frequency vector
    if isinstance(f, (tuple, list)) and len(f) == 2:
        f_seq = np.linspace(f[0], f[1], res)
    else:
        f_seq = np.array(f)

    # Calculate frequency dependent quality factor
    q_seq = q_0 * (f_seq / f_0)**e_0

    # Calculate frequency dependent wave phase velocity
    v_seq = v_0 * (f_seq / f_0)**(-p_0)

    # Calculate frequency dependent wave group velocity
    v_u_seq = v_seq / (1 + p_0)

    # Calculate beta
    beta = (2 * np.pi * r_0 * (1 + p_0) * f_seq**(1 + p_0 - e_0)) / (v_0 * q_0 * f_0**(p_0 - e_0))

    # Calculate psi
    psi = 2 * np.log(1 + (1 / beta)) * np.exp(-2 * beta) + (1 - np.exp(-beta)) * np.exp(-beta) * np.sqrt(2 * np.pi / beta)

    # Calculate auxiliary variables
    c_p_0 = 4 * (1 - (1 / 4 * k_s / h_w))
    c_k_s = 8 * (1 - (k_s / (2 * h_w)))
    c_s = 0.2 * (5.62 * np.log10(h_w / k_s) + 4)
    

    # Calculate zeta
    z = abs(c_k_s)**(2/3) * c_p_0**(8/3) * c_s**(4/3)

    # Calculate auxiliary variables
    u_s = np.sqrt(g * h_w * np.sin(a_w))
    u_p_0 = c_p_0 * u_s
    s = s_s / np.sqrt((1/3) - 2 / (np.pi**2))

    # Define integration limits
    l = (np.exp(-s) * d_s, np.exp(s) * d_s)

    # Define the integrand function
    def integrand(d, f):
        a = (1 / (1 + (2 * f * d / u_p_0)**(4/3)))**2
        b = (1 / (2 * s * d) * (1 + np.cos(np.pi * (np.log(d) - np.log(d_s)) / s))) * d**2
        return a * b

    # Integrate phi over grain-size distribution
    phi = np.array([integrate.quad(integrand, l[0], l[1], args=(f,))[0] for f in f_seq])

    # Calculate spectral power
    p = (n_0[0]**2 + n_0[1]**2) * \
        (k * w_w / (3 * (k_s**(2/3)))) * \
        ((r_w / r_s)**2) * \
        (((1 + p_0)**2) / ((f_0**(5 * p_0)) * v_0**5)) * \
        z * psi * phi * \
        (f_seq**((4/3) + 5 * p_0)) * \
        (g**(7/3)) * \
        (np.sin(a_w)**(7/3)) * \
        (c_w**2) * (h_w**(7/3))

    # Create and return DataFrame
    return pd.DataFrame({'frequency': f_seq, 'power': p})

def plot_spectrum(data, title):
    """
    Plot the power spectrum.

    Parameters:
    -----------
    data : pd.DataFrame
        DataFrame containing 'frequency' and 'power' columns.
    """
    plt.figure(figsize=(10, 6))
    plt.loglog(data['frequency'], data['power'])
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Power')
    plt.title(title)
    plt.grid(True, which="both", ls="-", alpha=0.5)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Example usage
    result = model_turbulence(
        d_s=0.03,  # 3 cm mean grain-size
        s_s=1.35,  # 1.35 log standard deviation
        f=(1, 200)  # 1-200 Hz frequency range
    )
    
    print(result.head())
    print("\nShape of the result:", result.shape)
    title = 'Seismic Spectrum due to Hydraulic Turbulence'

    # Plot the spectrum
    plot_spectrum(result, title)