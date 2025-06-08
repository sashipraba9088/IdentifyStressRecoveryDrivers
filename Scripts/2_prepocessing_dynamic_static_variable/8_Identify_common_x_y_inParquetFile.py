import pandas as pd
from glob import glob
import os
import sys

# Define the base path where the Parquet files are located
base_path = 'E:/Redoing_Preprocessing/Parquetfilecreation/South_Eastern_Highland'

# Step 1: Read all Parquet files in the folder
file_pattern = os.path.join(base_path, "South_Eastern_Highland_*.parquet")
file_paths = sorted(glob(file_pattern))

print(f"Found {len(file_paths)} files.")
if not file_paths:
    print("No files found matching the pattern. Please check the file pattern and directory.")
    sys.exit()

# Optional: List the files found
print("Files to be processed:")
for fp in file_paths:
    print(fp)

common_points = None  # Initialize common points

# Step 2: Identify common points across all files without loading all data at once
for idx, file_path in enumerate(file_paths):
    year = os.path.basename(file_path).split("_")[-1].split(".")[0]  # Extract year from file name
    print(f"\nProcessing file {idx + 1}/{len(file_paths)}: {file_path}")
    print(f"Extracted year: {year}")

    # Read only necessary columns to save memory
    try:
        df = pd.read_parquet(file_path, columns=['x', 'y', 'season'])
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        continue  # Skip to the next file

    # Ensure 'season' column exists
    if 'season' not in df.columns:
        print(f"'season' column not found in {file_path}. Skipping this file.")
        continue

    # Ensure 'x' and 'y' columns exist
    if not {'x', 'y'}.issubset(df.columns):
        print(f"'x' or 'y' columns not found in {file_path}. Skipping this file.")
        continue

    # Find the number of unique seasons in the file
    num_seasons_in_file = df['season'].nunique()
    if num_seasons_in_file == 0:
        print(f"No seasons found in {file_path}. Skipping this file.")
        continue

    print(f"Number of unique seasons in {year}: {num_seasons_in_file}")

    # Find points that have data for all seasons in this file
    seasons_per_point = df.groupby(['x', 'y'])['season'].nunique()
    points_with_all_seasons = seasons_per_point[seasons_per_point == num_seasons_in_file].reset_index()[['x', 'y']]

    # Convert to a set of tuples for efficient intersection
    points_set = set(map(tuple, points_with_all_seasons.values))

    print(f"Number of points with all seasons in {year}: {len(points_set)}")

    if not points_set:
        print(f"No points with all seasons found in {file_path}. Skipping this file.")
        continue

    # Update the common_points set
    if common_points is None:
        common_points = points_set
    else:
        common_points &= points_set  # Intersection with existing common points

    print(f"Number of common points after processing {year}: {len(common_points)}")

    # If after intersection, common_points becomes empty, we can break early
    if not common_points:
        print("No common points found across files. Exiting early.")
        break

if not common_points:
    print("No common points found across all files. Exiting.")
    sys.exit()

# Convert the set of common points to a DataFrame
common_points_df = pd.DataFrame(list(common_points), columns=['x', 'y'])
print(f"\nTotal number of common points: {len(common_points_df)}")

# Step 3: Save the common points to a Parquet file
output_file = os.path.join(base_path, 'common_points.parquet')
try:
    common_points_df.to_parquet(output_file, index=False)
    print(f"Common points saved to {output_file}")
except Exception as e:
    print(f"Error saving common points DataFrame: {e}")