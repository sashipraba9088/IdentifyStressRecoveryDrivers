import os
import pandas as pd
from glob import glob

# Define paths
input_dir = "E:/Redoing_Preprocessing/Parquetfilecreation/South_Eastern_Highland"
output_dir = "E:/Redoing_Preprocessing/Parquetfilecreation/South_Eastern_Highland_CommonPoint"
reference_file = "E:/Redoing_Preprocessing/Parquetfilecreation/common_points.parquet"  # Replace with the path to your reference file

# Load reference x, y points
reference_df = pd.read_parquet(reference_file)
reference_points = reference_df.set_index(['x', 'y']).index

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Process each Parquet file in the input directory
input_files = glob(os.path.join(input_dir, "*.parquet"))
for input_file in input_files:
    # Load the Parquet file
    df = pd.read_parquet(input_file)

    # Filter rows based on the reference x, y points
    filtered_df = df.set_index(['x', 'y']).loc[reference_points].reset_index()

    # Generate output file path
    output_file = os.path.join(output_dir, os.path.basename(input_file))

    # Save the filtered data to the output directory
    filtered_df.to_parquet(output_file, index=False)
    print(f"Processed and saved: {output_file}")

# Final message
print("All files processed successfully!")