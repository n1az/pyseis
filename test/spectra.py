from pyseis import fmi_spectra


def create_reference_spectra(parameters):
    """
    Create corresponding reference spectra
    """
    ref_spectra = fmi_spectra.fmi_spectra(parameters=parameters, n_cores=2)
    return ref_spectra
