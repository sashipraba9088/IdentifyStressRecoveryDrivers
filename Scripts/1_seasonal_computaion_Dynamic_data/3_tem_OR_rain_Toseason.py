import xarray as xr
import os

# Specify the input NetCDF file directory
input_dir = "G:/Temperature/Temperature 1986-2022"  # Update with the directory containing your NetCDF files
output_dir = "Seasonal_NetCDF"
os.makedirs(output_dir, exist_ok=True)

# Define the seasons and their respective months
seasons = {
    "Autumn": [3, 4, 5],          # March, April, May
    "Winter": [6, 7, 8],          # June, July, August
    "Spring": [9, 10, 11],        # September, October, November
    "Summer": [12, 1, 2],         # December (current year), January, February (next year)
}

# Function to extract year and month from a file name
def extract_year_month(file_name):
    # Assuming file format like 'ANUClimate_v2-0_tavg_monthly_201601.nc'
    parts = file_name.split("_")
    year_month = parts[-1].replace(".nc", "")  # '201601'
    year = int(year_month[:4])  # First 4 characters are the year
    month = int(year_month[4:])  # Remaining characters are the month
    return year, month

# Group files by year and month
files = sorted([f for f in os.listdir(input_dir) if f.endswith(".nc")])
file_dict = {}
for file_name in files:
    year, month = extract_year_month(file_name)
    if year not in file_dict:
        file_dict[year] = {}
    file_dict[year][month] = os.path.join(input_dir, file_name)

# Process each year to calculate seasonal means
for year in sorted(file_dict.keys()):
    for season, months in seasons.items():
        season_data = []

        # Handle the special case for Summer spanning two years
        for month in months:
            if month == 12 and year in file_dict:  # December of the current year
                if month in file_dict[year]:
                    season_data.append(xr.open_dataset(file_dict[year][month]))
            elif month in [1, 2] and (year + 1) in file_dict:  # January, February of the next year
                if month in file_dict[year + 1]:
                    season_data.append(xr.open_dataset(file_dict[year + 1][month]))
            elif month in file_dict[year]:  # Other months within the current year
                season_data.append(xr.open_dataset(file_dict[year][month]))

        # If there is no data for the season, skip it
        if not season_data:
            print(f"No data for {season} of {year}")
            continue

        # Calculate the mean for the season
        seasonal_mean = xr.concat(season_data, dim="time").mean(dim="time")

        # Save the seasonal mean NetCDF file
        output_file = os.path.join(output_dir, f"{year}_{season}.nc")
        seasonal_mean.to_netcdf(output_file)
        print(f"Saved seasonal mean file: {output_file}")
