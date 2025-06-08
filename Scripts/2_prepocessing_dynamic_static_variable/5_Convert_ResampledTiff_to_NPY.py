import os
import numpy as np
import rasterio

# Path to the folder containing all TIFF files
input_folder = 'E:/Redoing_Preprocessing/Resampled_Tiff/South_Eastern_Highland/Feature_Dynamic/Tem_GeoTiff_Resampled'

# Path to save the converted NPY files
output_folder = 'Tem_NPY_converted'
os.makedirs(output_folder, exist_ok=True)

# Loop through each file in the input folder
for file_name in os.listdir(input_folder):
    if file_name.endswith('.tif'):  # Only process TIFF files
        # Full path to the input TIFF file
        input_file_path = os.path.join(input_folder, file_name)

        # Load the GeoTIFF file using rasterio
        with rasterio.open(input_file_path) as src:
            # Read the first band as a NumPy array
            image_array = src.read(1)

        # Define the output file path with "Tem_" added to the front
        output_file_path = os.path.join(output_folder, file_name.replace('.tif', '.npy'))

        # Save the NumPy array
        np.save(output_file_path, image_array)
        print(f"Converted and saved: {output_file_path}")

print("All files have been converted.")
