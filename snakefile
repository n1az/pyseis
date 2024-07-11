# snakefile

## Define the order of execution

rule all:
    input:
        "R_script.txt",
        "py_script_1.txt",
        "py_script_2.txt"

rule clean:
    """
    Rule to clean the existing outputs from previous runs.
    """
    run:
        import shutil
        import os

        output_dirs = ["R/output", "test/output"]
        
        for dir in output_dirs:
            if os.path.exists(dir):
                shutil.rmtree(dir)
            os.makedirs(dir)

rule run_rscript:
    """
    Rule to run the R script and store the outputs in the R/output folder.
    """
    input:
        script = "R/rscript.R"
    output:
        touch("R_script.txt")
    run:
        import subprocess

        r_command = f"Rscript {input.script}"
        subprocess.run(r_command, shell=True, check=True)

rule run_python_script1:
    """
    Rule to run the first Python script and store the outputs in the test/output folder.
    """
    input:
        script = "test/test_spatials.py"
    output:
        touch("py_script_1.txt")
    run:
        import subprocess

        py_command = f"python {input.script}"
        subprocess.run(py_command, shell=True, check=True)

rule run_python_script2:
    """
    Rule to run the second Python script and store the outputs in the test/output folder.
    """
    input:
        script = "test/test_fmi_models.py"
    output:
        touch("py_script_2.txt")
    run:
        import subprocess

        py_command = f"python {input.script}"
        subprocess.run(py_command, shell=True, check=True)
