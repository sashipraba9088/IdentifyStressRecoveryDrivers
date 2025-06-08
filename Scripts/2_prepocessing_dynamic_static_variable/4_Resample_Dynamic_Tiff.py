from osgeo import gdal
import os

gdal.UseExceptions()  # Enable GDAL exceptions for better error handling

# Path to the reference z-score image
reference_image_path = "E:/Chapter_4/Test4-DataForCorrelation_pixellevel/Enviornmnetal_rasters_masked/zscore_difference_bellow-1_4.tif"  # Update to your z-score image path

# List of directories containing input images to align
input_directories = [
    "E:/Chapter_4/Test4-DataForCorrelation_pixellevel/Enviornmnetal_rasters_masked",
    # Add additional directories as needed
]

# Directory to save aligned output images
output_root = "E:/Chapter_4/Test4-DataForCorrelation_pixellevel/Enviornmnetal_rasters_masked_resampled"
os.makedirs(output_root, exist_ok=True)

# Open the reference image to extract its geospatial parameters
reference_ds = gdal.Open(reference_image_path, gdal.GA_ReadOnly)
if not reference_ds:
    raise FileNotFoundError(f"Reference image not found: {reference_image_path}")

ref_proj = reference_ds.GetProjection()  # CRS of the reference image
ref_geotrans = reference_ds.GetGeoTransform()  # GeoTransform of the reference image
ref_width = reference_ds.RasterXSize
ref_height = reference_ds.RasterYSize
ref_extent = (
    ref_geotrans[0],  # Min X
    ref_geotrans[3],  # Max Y
    ref_geotrans[0] + ref_width * ref_geotrans[1],  # Max X
    ref_geotrans[3] + ref_height * ref_geotrans[5]  # Min Y
)
reference_ds = None  # Close the reference dataset

# Debugging information for the reference image
print("Reference Image Info:")
print(f"Projection: {ref_proj}")
print(f"GeoTransform: {ref_geotrans}")
print(f"Extent: {ref_extent}")
print(f"Width: {ref_width}, Height: {ref_height}")

# Process each directory and align images
for input_directory in input_directories:
    for root, _, files in os.walk(input_directory):
        for file in files:
            if file.endswith(".tif"):  # Only process .tif files
                input_file_path = os.path.join(root, file)

                # Extract base name (e.g., PET_2022_Summer) from the input file name
                base_name = os.path.splitext(file)[0]  # Remove .tif extension

                # Construct the output file path using the base name
                output_file_path = os.path.join(output_root, f"{base_name}.tif")
                os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

                # Print debug info for the current file
                print(f"Processing file: {input_file_path}")
                print(f"Output file: {output_file_path}")

                try:
                    # Align the input image to match the reference image
                    kwargs = {
                        "format": "GTiff",
                        "outputBounds": ref_extent,  # Align to the reference image extent
                        "dstSRS": ref_proj,  # CRS of the reference image
                        "width": ref_width,  # Match the reference image width
                        "height": ref_height,  # Match the reference image height
                        "resampleAlg": "bilinear"  # Resampling method
                    }
                    ds = gdal.Warp(output_file_path, input_file_path, **kwargs)
                    if ds:
                        ds = None  # Close the dataset
                        print(f"Aligned and saved: {output_file_path}")
                    else:
                        print(f"Failed to process: {input_file_path}")
                except Exception as e:
                    print(f"Error processing {input_file_path}: {e}")

print("Processing complete.")
