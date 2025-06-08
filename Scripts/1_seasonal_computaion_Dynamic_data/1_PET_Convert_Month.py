
import xarray as xr
import os
import calendar

# Specify the input NetCDF file directory
input_dir = "E:/PET/"
output_dir = "C:/Chapter2_RealWork/Featuredata_preprocessing/PET_Data_Processing_New/PET_Monthly_NC"
os.makedirs(output_dir, exist_ok=True)

# Process all NetCDF files in the input directory
for file_name in os.listdir(input_dir):
    if file_name.endswith(".nc"):
        # Extract the year from the filename (assuming the filename includes the year, e.g., '2019.et_tall_crop.nc')
        year = file_name.split(".")[0]
        input_file = os.path.join(input_dir, file_name)
        
        # Open the NetCDF file
        dataset = xr.open_dataset(input_file)
        
        # Variable name to process
        variable_name = "et_tall_crop"
        
        # Group data by month and calculate the monthly mean
        monthly_means = dataset[variable_name].groupby("time.month").mean(dim="time")
        
        # Save each monthly mean to a separate NetCDF file
        for month in range(1, 13):
            # Get the month name (e.g., "January")
            month_name = calendar.month_name[month]
            
            # Extract the monthly mean data
            monthly_mean = monthly_means.sel(month=month)
            
            # Construct the output file name
            output_file = os.path.join(output_dir, f"{year}_{month_name}.nc")
            
            # Save to NetCDF
            monthly_mean.to_netcdf(output_file)
            print(f"Saved monthly mean file: {output_file}")
        
        # Close the dataset
        dataset.close()
