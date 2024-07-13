from setuptools import setup

# Function to read the requirements from requirements.txt
def read_requirements(file):
    with open(file, 'r') as f:
        return f.read().splitlines()

setup(
    name='pyseis',
    version='0.1.0',
    author='Frieder Emil Georg Tautz, Shahriar Shohid Choudhury, Md Niaz Morshed, Lamia Islam',
    author_email='tautz1@uni-potsdam.de, choudhury@uni-potsdam.de, md.niaz.morshed@uni-potsdam.de, lamia.islam@uni-potsdam.de',
    description='A comprehensive Python package for seismic data analysis and visualization.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://gitup.uni-potsdam.de/tautz1/pyseis',
    packages=['pyseis'],
    install_requires=read_requirements('requirements.txt'),  # Read dependencies from requirements.txt
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.11',
)
