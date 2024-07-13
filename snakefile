# Snakefile

# Define input files
R_SCRIPTS = ["rscript"]
PY_SCRIPTS = ["test_spatials", "test_fmi_models"]

rule all:
    input:
        expand("output/R_{script}.txt", script=R_SCRIPTS),
        expand("output/py_{script}.txt", script=PY_SCRIPTS)

rule clean:
    """
    Rule to clean the existing outputs from previous runs.
    """
    output:
        touch("clean.txt")
    run:
        import os
        import glob

        # Define patterns to clean
        patterns_to_clean = ["output/R_*.txt", "output/py_*.txt"]

        for pattern in patterns_to_clean:
            for file in glob.glob(pattern):
                if os.path.exists(file):
                    os.remove(file)
                    print(f"Removed: {file}")

rule run_rscript:
    """
    Rule to run the R script
    """
    input:
        script = "R/{script}.R",
        clean = "clean.txt"
    output:
        touch(temp("output/R_{script}.txt"))
    run:
        import subprocess

        r_command = f"Rscript {input.script}"
        subprocess.run(r_command, shell=True, check=True)

rule run_python_script:
    """
    Rule to run Python scripts
    """
    input:
        script = "test/{script}.py",
        clean = "clean.txt"
    output:
        touch(temp("output/py_{script}.txt"))
    run:
        import subprocess

        py_command = f"python {input.script}"
        subprocess.run(py_command, shell=True, check=True)