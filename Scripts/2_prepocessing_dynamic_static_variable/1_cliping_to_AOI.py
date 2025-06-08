import xarray as xr
import rioxarray  # Enables CRS and spatial operations in xarray
import geopandas as gpd
import os

# Path to your shapefile
shapefile_path = "F:/Chapter2_RealWork/Chapter_2_Final Analysis/Shapefile_Interested/NSW_North_Coast.shp"

# Directory containing input NetCDF files
input_nc_dir = "G:/DataSet/Features/SeasonalData_Temperature"

# Output directory for clipped NetCDF files
output_nc_dir = "Tem_Bud_Clliped_NC"
os.makedirs(output_nc_dir, exist_ok=True)

# Load the shapefile
shapefile = gpd.read_file(shapefile_path)

# Ensure the shapefile has a CRS
if shapefile.crs is None:
    raise ValueError("The shapefile does not have a CRS. Please define one.")

# Get the CRS from the shapefile
shapefile_crs = shapefile.crs

# Process each NetCDF file
for file_name in os.listdir(input_nc_dir):
    if file_name.endswith(".nc"):
        input_nc_path = os.path.join(input_nc_dir, file_name)
        output_nc_path = os.path.join(output_nc_dir, file_name)

        # Open the NetCDF file
        ds = xr.open_dataset(input_nc_path)

        # Assume the first variable in the dataset is the target variable
        variable_name = list(ds.data_vars.keys())[0]
        data_array = ds[variable_name]

        # Set the CRS for the NetCDF file to match the shapefile's CRS
        if not data_array.rio.crs:
            data_array = data_array.rio.set_crs(shapefile_crs)

        # Clip the NetCDF file using the shapefile
        clipped_data = data_array.rio.clip(shapefile.geometry, shapefile_crs, drop=True)

        # Save the clipped data to a new NetCDF file
        clipped_data.to_dataset(name=variable_name).to_netcdf(output_nc_path)
        print(f"Clipped and saved: {output_nc_path}")
