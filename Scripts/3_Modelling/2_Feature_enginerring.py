import pandas as pd
import os

# Function to fill lagged columns for multiple variables based on their respective time lags
def fill_lagged_columns_multiple(input_dir, output_dir, variables_lags):
    """
    Fills lagged columns for multiple variables based on their respective time lags.

    Args:
        input_dir (str): Directory containing the input Parquet files.
        output_dir (str): Directory to save the updated Parquet files.
        variables_lags (dict): A dictionary where keys are variable names and values are lists of time lags for each column.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Define the sequence of seasons
    seasons = ['Summer', 'Autumn', 'Winter', 'Spring']

    # Get a list of all available years in the dataset
    all_files = [
        file_name for file_name in os.listdir(input_dir)
        if file_name.endswith(".parquet")
    ]
    available_years = sorted(
        [int(file_name.split("_")[-1].split(".")[0]) for file_name in all_files]
    )

    # Determine the earliest available year
    earliest_year = min(available_years)

    for file_name in all_files:
        file_path = os.path.join(input_dir, file_name)

        # Load the existing Parquet file
        df = pd.read_parquet(file_path)

        # Get the current year from the file name
        current_year = int(file_name.split("_")[-1].split(".")[0])

        for variable, lags in variables_lags.items():
            for col_index, lag in enumerate(lags, start=1):
                col_name = f"{variable}{col_index}"
                df[col_name] = None

                for index, row in df.iterrows():
                    current_season = row['season']

                    # Calculate the target season and year based on the lag
                    target_season_index = (seasons.index(current_season) - lag) % len(seasons)
                    target_season = seasons[target_season_index]
                    year_offset = (seasons.index(current_season) - lag) // len(seasons)
                    target_year = current_year + year_offset

                    # If target year is outside the available range, assign None
                    if target_year < earliest_year:
                        df.at[index, col_name] = None
                        continue

                    # Find the target file and row
                    target_file_name = f"NSW_North_Coast_Dataframe_{target_year}.parquet"
                    target_file_path = os.path.join(input_dir, target_file_name)

                    if os.path.exists(target_file_path):
                        target_df = pd.read_parquet(target_file_path)
                        target_row = target_df[
                            (target_df['season'] == target_season) &
                            (target_df['x'] == row['x']) &
                            (target_df['y'] == row['y'])
                        ]

                        # Assign the variable value from the target row to the lagged column
                        if not target_row.empty:
                            df.at[index, col_name] = target_row.iloc[0][variable]
                        else:
                            df.at[index, col_name] = None  # No match found
                    else:
                        df.at[index, col_name] = None  # Target file does not exist

        # Save the updated dataframe to a new Parquet file
        updated_file_path = os.path.join(output_dir, f"updated_{file_name}")
        df.to_parquet(updated_file_path, index=False)

        print(f"Updated file saved at: {updated_file_path}")

# Define input and output directories
input_dir = "F:/Chapter2_RealWork/Chapter_2_Final Analysis/Test3_ANNModel_DataPreparation/parquet_without_lag"
output_dir = "F:/Chapter2_RealWork/Chapter_2_Final Analysis/Test3_ANNModel_DataPreparation/parquet_without_lag"

# Define variables with their respective time lags
variables_lags = {
    "Tavg": [2, 3, 4, 5, 6, 7, 8, 9],  # Tavg lags: 8 seasons back to 1 season back
    "PET": [1],                        # PET lags: 1 season back
    "Rain": [2, 3, 4, 5]               # Rain lags: 4 seasons back to 2 seasons back
}

# Fill lagged columns for multiple variables
fill_lagged_columns_multiple(
    input_dir=input_dir,
    output_dir=output_dir,
    variables_lags=variables_lags
)