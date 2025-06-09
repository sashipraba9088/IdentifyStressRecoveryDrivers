# IdentifyStressRecoveryDrivers

This repository contains code and resources used to identify the drivers of drought-induced stress and post-drought recovery in Eucalyptus forests, as described in our paper.

It includes preprocessing steps for dynamic, static, and response variables (AOI provided as a shapefile). OLS models were implemented to identify the lagged and cumulative effects of the dynamic variables, and the code for ANN hyperparameter tuning, training, and sensitivity analysis is located in the sub directory modelling. The source code provided is written in Python programming language and has been tested using Python 3.11.5. The source code is written in Python 3.11.5, and the main libraries used are Dask, TensorFlow 2.6.0, and Keras 2.6.0.
- - - -
SYSTEM REQUIREMENTS:
Please make sure that the following Python packages are installed on your computer before running any of the above execution files:


(1) NumPy (http://www.numpy.org/)


(2) SciPy (http://www.scipy.org/)



(3) matplotlib (http://matplotlib.org/)



(4) pandas (https://pandas.pydata.org/)
- - - -
DATA RESOURCES:


(1) Please refer the provided Table 1 in the paper to download thestatic and dynamic varaiables used in this paper.


(2) Response varaiable- This dataset was obtained using Google Earth Engine (https://code.earthengine.google.com/97960acc37b8d4a17612a6e3b583e2a8 and https://code.earthengine.google.com/b35112c71516df6381978a0298214c74)


(3) CRI index - This index was developed using Gogle Earth ENgine (https://code.earthengine.google.com/?scriptPath=users%2Fnuwanthisashipraba%2FPHD_Chapter2%3AGrass_Tree_Factor_test5)
