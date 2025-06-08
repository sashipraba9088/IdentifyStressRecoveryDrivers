import xarray as xr
import rioxarray  # For CRS and spatial operations
import rasterio
import os

# Paths
reference_geotiff_path = "E:/ResampledTiffs_90_22/South_Eastern_Highlands/Responsive/2010/z_score/2010 South_Eastern_Highland z_score Autumn_clipped.tif"  # Path to the reference GeoTIFF
input_nc_dir = "tem_nc"  # Directory containing clipped NetCDF files
output_tiff_dir = "Tem_GeoTiff"  # Directory to save GeoTIFF files
os.makedirs(output_tiff_dir, exist_ok=True)

# Get CRS and resolution from the reference GeoTIFF
with rasterio.open(reference_geotiff_path) as ref:
    ref_crs = ref.crs  # CRS of the reference GeoTIFF
    ref_transform = ref.transform  # Transform of the reference GeoTIFF
    ref_resolution = (ref.transform[0], -ref.transform[4])  # Resolution of the reference GeoTIFF

# Process each NetCDF file
for file_name in os.listdir(input_nc_dir):
    if file_name.endswith(".nc"):
        input_nc_path = os.path.join(input_nc_dir, file_name)
        output_tiff_path = os.path.join(output_tiff_dir, file_name.replace(".nc", ".tif"))

        # Open the NetCDF file
        ds = xr.open_dataset(input_nc_path)

        # Assume the first variable in the dataset is the target variable
        variable_name = list(ds.data_vars.keys())[0]
        data_array = ds[variable_name]

        # Set CRS and resolution to match the reference GeoTIFF
        data_array = data_array.rio.set_crs(ref_crs)  # Assign CRS from the reference GeoTIFF
        data_array = data_array.rio.reproject(
            ref_crs,  # Reproject to the same CRS as the reference GeoTIFF
            resolution=ref_resolution,  # Resample to match the reference GeoTIFF's pixel size
        )

        # Save the data as a GeoTIFF
        data_array.rio.to_raster(output_tiff_path)
        print(f"Converted to GeoTIFF using reference: {output_tiff_path}")