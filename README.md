# comsol_tools
Python scripts to support Heat and Moisture transport calculations in COMSOL Multiphysics

[pvlib](https://pvlib-python.readthedocs.io/en/stable/index.html) is recommended to install into a separate conda environment. This environment is used also for other packages needed to run the code.

First install [Miniconda](https://docs.anaconda.com/miniconda/). Then run the following commands in the Anaconda Prompt:

```
conda --help
conda info --envs
conda create --name <name_of_my_environment>
conda activate <name_of_my_environment>
conda config --show channels
conda config --add channels conda-forge
conda list
conda install pvlib h5py spyder numpy matplotlib pandas scipy
conda list
pip uninstall h5py
pip install h5py
```

The two pip commands were needed to get the system running (situation in June 2024).

To modify and run the python code, start the Anaconda Prompt and write the following commands:

```
conda activate <name_of_my_environment>
spyder
```

The python files in this repository that start with...
- "1_": Read in a more general climate file (not included) and output climate data files for specific comsol models.
- "2_": Read in results files from comsol models, calculate mould index and save time series data as dict of pandas DataFrames to a pickle file.
- "3_": Make various plots of the data and output indicator values to text files.

All the code is for specific purpose and for a specific implementation. The code is put here however, if someone else also happens to find it useful.
