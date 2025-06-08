import numpy as np
import os
from osgeo import gdal

# Define the root directories
root_directories = [
    'E:/Chapter_4/Test5-WholeDomainlevel_analysis/SEH_NBR_zscore_whole_domain_level', 
    #'C:/Chapter2_RealWork/Featuredata_preprocessing/ResampledTiffs/Sydney Basin'
]
years = [str(year) for year in range(1990, 2024)]

# Hardcode the output base path
output_base_path = 'C:/Chapter4/Responsive_Npy_converted_Newzscore'

def convert_tiff_to_npy(tiff_path, npy_path):
    dataset = gdal.Open(tiff_path)
    if dataset is None:
        print(f"Failed to open {tiff_path}")
        return
    band = dataset.GetRasterBand(1)
    image_array = band.ReadAsArray()
    np.save(npy_path, image_array)

for root_dir in root_directories:
    responsive_path = os.path.join(root_dir, 'Responsive')
    if os.path.exists(responsive_path):
        for year in years:
            year_path = os.path.join(responsive_path, year)
            if os.path.exists(year_path):
                z_score_path = os.path.join(year_path, 'z_score')
                if os.path.exists(z_score_path):
                    for file_name in os.listdir(z_score_path):
                        if file_name.endswith('.tif'):
                            tiff_file_path = os.path.join(z_score_path, file_name)
                            output_path = os.path.join(output_base_path, os.path.basename(root_dir), 'Responsive', year, 'z_score')
                            os.makedirs(output_path, exist_ok=True)
                            npy_file_path = os.path.join(output_path, file_name.replace('.tif', '.npy'))
                            convert_tiff_to_npy(tiff_file_path, npy_file_path)


