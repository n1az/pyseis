from pyseis import fmi_parameters


def create_reference_parameters():
    """
    Create example reference parameter sets
    """
    ref_pars = fmi_parameters.fmi_parameters(
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
    return ref_pars
