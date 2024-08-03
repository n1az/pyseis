import random


def fmi_parameters(
    n,
    d_s,
    s_s,
    r_s,
    q_s,
    h_w,
    w_w,
    a_w,
    f_min,
    f_max,
    r_0,
    f_0,
    q_0,
    v_0,
    p_0,
    e_0,
    n_0_a,
    n_0_b,
    res,
):
    """
    Create reference model reference parameter catalogue.

    In order to run the fluvial model inversion (FMI) routine, a set of
    randomized target parameter combinations needs to be created. This
    function does this job.

    All parameters must be provided as single values, except for those
    parameters that shall be randomized, which must be provided as a vector
    of length two. This vector defines the range within which uniformly
    distributed random values will be generated and assigned.

    Parameters:
    n (int):        Number of output reference spectra.
    d_s (float):    Mean sediment grain diameter (m). Alternative to gsd.
    s_s (float):    Standard deviation of sediment grain diameter (m).
                    Alternative to gsd.
    r_s (float):    Specific sediment density (kg / m^3).
    q_s (float):    Unit sediment flux (m^2 / s).
    h_w (float):    Fluid flow depth (m).
    w_w (float):    Fluid flow width (m).
    a_w (float):    Fluid flow inclination angle (radians).
    f_min (float):  Lower boundary of the frequency range to be modeled.
    f_max (float):  Upper boundary of the frequency range to be modeled.
    r_0 (float):    Distance of seismic station to source.
    f_0 (float):    Reference frequency (Hz).
    q_0 (float):    Ground quality factor at f_0.
                    Reasonable value may be 20 (Tsai et al. 2012).
    v_0 (float):    Phase speed of the Rayleigh wave at f_0 (m/s).
                    Assuming a shear wave velocity of about 2200 m/s,
                    Tsai et al. (2012) yield a value of 1295 m/s for
                    this parameter.
    p_0 (float):    Variation exponent of Rayleigh wave velocities with
                    frequency (dimensionless).
    e_0 (float):    Exponent characterizing quality factor increase with
                    frequency (dimensionless).
                    Reasonable value may be 0 (Tsai et al. 2012).
    n_0_a (float):  Lower Greens function displacement amplitude coefficients.
                    Cf. N_ij in eq. 36
                    in Gimbert et al. (2014).
    n_0_b (float):  Lower Greens function displacement amplitude coefficients.
                    Cf. N_ij in eq. 36
                    in Gimbert et al. (2014).
    res (int):      Output resolution, i.e., length of the spectrum vector.

    Returns:
    list: List of dictionaries with model reference parameters.
    """

    # Build preliminary output structure
    pars_template = {
        "d_s": d_s,
        "s_s": s_s,
        "r_s": r_s,
        "q_s": q_s,
        "w_w": w_w,
        "a_w": a_w,
        "h_w": h_w,
        "f_min": f_min,
        "f_max": f_max,
        "r_0": r_0,
        "f_0": f_0,
        "q_0": q_0,
        "v_0": v_0,
        "p_0": p_0,
        "e_0": e_0,
        "n_0_a": n_0_a,
        "n_0_b": n_0_b,
        "res": res,
    }

    # Build model parameter catalog
    pars_reference = []
    for i in range(n):
        pars_ref = pars_template.copy()

        # Identify parameters to randomize
        for key, value in pars_ref.items():
            if isinstance(value, (list, tuple)) and len(value) == 2:
                pars_ref[key] = random.uniform(value[0], value[1])

        pars_reference.append(pars_ref)

    return pars_reference


# Example usage
ref_pars = fmi_parameters(
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
