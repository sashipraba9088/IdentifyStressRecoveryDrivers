import xarray as xr
import os
import calendar

# Specify the input NetCDF file directory
input_dir = "PET_Monthly_NC"  # Directory with monthly mean files
output_dir = "PET_Seasonal_NC"
os.makedirs(output_dir, exist_ok=True)

# Define the seasons and their respective months
seasons = {
    "Autumn": [3, 4, 5],          # March, April, May
    "Winter": [6, 7, 8],          # June, July, August
    "Spring": [9, 10, 11],        # September, October, November
    "Summer": [12, 1, 2],         # December (current year), January, February (next year)
}

# Get a sorted list of files in the input directory
files = sorted(os.listdir(input_dir))

# Create a mapping of month names to their numeric values
month_name_to_number = {name: idx for idx, name in enumerate(calendar.month_name) if name}
print(month_name_to_number)
# Group files by year based on file naming convention (e.g., '2019_January.nc')
year_files = {}
for file_name in files:
    if file_name.endswith(".nc"):
        # Extract the year and month from the filename
        year, month_name = file_name.split("_")[0], file_name.split("_")[1].replace(".nc", "")
        month = month_name_to_number[month_name]
        if year not in year_files:
            year_files[year] = {}
        year_files[year][month] = os.path.join(input_dir, file_name)

# Process each year
for year, monthly_files in year_files.items():
    # Load datasets for the current year
    year_dataset = {month: xr.open_dataset(file_path) for month, file_path in monthly_files.items()}
    
    # Calculate seasonal means
    for season, months in seasons.items():
        if season == "Summer":
            # Special case: December (current year), January, February (next year)
            current_year_months = [m for m in months if m != 1 and m != 2]
            next_year_months = [m for m in months if m == 1 or m == 2]
            print(current_year_months)
            print(next_year_months)
            # Get datasets for the current year
            current_year_data = [year_dataset[m] for m in current_year_months if m in year_dataset]
            print(current_year_data)
            # Get datasets for the next year
            next_year = str(int(year) + 1)
            next_year_data = []
            if next_year in year_files:
                for m in next_year_months:
                    if m in year_files[next_year]:
                        dataset = xr.open_dataset(year_files[next_year][m])
                        next_year_data.append(dataset)

            # Combine current and next year data
            combined_data = current_year_data + next_year_data
            seasonal_mean = xr.concat(combined_data, dim="time").mean(dim="time")
        else:
            # Normal case: Get datasets for the season months
            season_data = [year_dataset[m] for m in months if m in year_dataset]
            if not season_data:
                continue
            seasonal_mean = xr.concat(season_data, dim="time").mean(dim="time")

        # Save the seasonal mean NetCDF file
        output_file = os.path.join(output_dir, f"{year}_{season}.nc")
        seasonal_mean.to_netcdf(output_file)
        print(f"Saved seasonal file: {output_file}")

