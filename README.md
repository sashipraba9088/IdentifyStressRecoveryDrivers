# IdentifyStressRecoveryDrivers

This repository contains code and resources used to identify the drivers of drought-induced stress and post-drought recovery in Eucalyptus forests, as described in our paper.

Different preprocessing steps for dynamic, static and response varaibales are mentioned in this repo as mentioned in the paper.Area of Interest (AOI) are given as a shape file. OLS models were implemented to identify the lag and cummulative effect of the dynakic varaiables and codes used for ANN model hyperparameter tunning and training and sensitvity analysi are listed in the sub directory modelling. The source code provided is written in Python programming language and has been tested using Python 3.12. The main libraries used in this project include dask, tensorflow2.6.0 and Keras2.6.0.
- - - -
SYSTEM REQUIREMENTS:
Please make sure that the following Python packages are installed on your computer before running any of the above execution files:
(1) NumPy (http://www.numpy.org/)
(2) SciPy (http://www.scipy.org/)
(3) matplotlib (http://matplotlib.org/)
(4) pandas (https://pandas.pydata.org/)
- - - -
DATA RESOURCES:
(1) Please refere the provided Table 1 in the paper to download thestatic and dynamic varaiables used in this paper.
(2) Response varaiable- This dataset was obtained using Google Earth Engine (https://code.earthengine.google.com/97960acc37b8d4a17612a6e3b583e2a8 and https://code.earthengine.google.com/b35112c71516df6381978a0298214c74)
(3) CRI index - This index was developed using Gogle Earth ENgine (https://code.earthengine.google.com/?scriptPath=users%2Fnuwanthisashipraba%2FPHD_Chapter2%3AGrass_Tree_Factor_test5)
    

Overview

Study Objective: Quantify canopy stress and recovery following the 2019–2020 drought in Eucalyptus forests across two eastern New South Wales bioregions (NSW North Coast and South Eastern Highlands).

Approach:

Preprocess static, dynamic, and response variables (AOI provided as a shapefile).

Implement Ordinary Least Squares (OLS) models to identify lagged and cumulative effects of climatic drivers.

Use Artificial Neural Networks (ANN) for hyperparameter tuning, training, and sensitivity analysis to link NBR z‑scores with climatic, topographic, soil, and vegetation variables.

Technology: Python 3.12 with Dask, TensorFlow 2.6.0, and Keras 2.6.0.

Repository Structure

IdentifyStressRecoveryDrivers/
├── data/                 # AOI shapefile and raw datasets
├── preprocessing/        # Scripts for dynamic, static, and response variable preprocessing
├── modelling/            # Model implementations
│   ├── ols/              # OLS lag and cumulative effect analyses
│   └── ann/              # ANN hyperparameter tuning, training, sensitivity analysis
├── notebooks/            # Jupyter notebooks for exploratory analyses and visualization
└── utils/                # Utility functions and helpers

System Requirements

Ensure you have Python 3.12 installed, then install the required packages:

pip install numpy scipy matplotlib pandas dask tensorflow==2.6.0 keras==2.6.0

NumPy: http://www.numpy.org/

SciPy: http://www.scipy.org/

matplotlib: http://matplotlib.org/

pandas: https://pandas.pydata.org/

Data Resources

Static & Dynamic Variables: Refer to Table 1 in the paper for download sources.

Response Variable (Sentinel‑2 NBR z‑scores): Generated via Google Earth Engine

Script 1

Script 2

CRI Index: Computed in Google Earth Engine

CRI index script