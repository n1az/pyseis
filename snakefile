# snakefile

## Define the order of execution

rule all:
    input:
        "clean.txt",
        "R_script.txt",
        "py_script_1.txt",
        "py_script_2.txt"

rule clean:
    """
    Rule to clean the existing outputs from previous runs.
    """
    output:
        touch("clean.txt")
    run:
        import os

        # Define files to be cleaned based on rule all inputs
        files_to_clean = ["R_script.txt", "py_script_1.txt", "py_script_2.txt"]

        for file in files_to_clean:
            if os.path.exists(file):
                os.remove(file)
                print(f"Removed: {file}")

rule run_rscript:
    """
    Rule to run the R script
    """
    input:
        script = "R/rscript.R",
        clean = "clean.txt"
    output:
        touch("R_script.txt")
    run:
        import subprocess

        r_command = f"Rscript {input.script}"
        subprocess.run(r_command, shell=True, check=True)

rule run_python_script1:
    """
    Rule to run the test_spatial script
    """
    input:
        script = "test/test_spatials.py",
        clean = "clean.txt"
    output:
        touch("py_script_1.txt")
    run:
        import subprocess

        py_command = f"python {input.script}"
        subprocess.run(py_command, shell=True, check=True)

rule run_python_script2:
    """
    Rule to run the fmi_models script
    """
    input:
        script = "test/test_fmi_models.py",
        clean = "clean.txt"
    output:
        touch("py_script_2.txt")
    run:
        import subprocess

        py_command = f"python {input.script}"
        subprocess.run(py_command, shell=True, check=True)
