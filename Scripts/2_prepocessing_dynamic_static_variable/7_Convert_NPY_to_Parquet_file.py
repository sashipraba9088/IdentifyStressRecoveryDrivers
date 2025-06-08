import numpy as np
import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import gc

# Define the base path and constants
BASE_PATH = "E:/Redoing_Preprocessing/NPY_converted"
ROOT_DIRS = ["South_Eastern_Highland"]
YEARS = range(2010, 2023)  # Set the range of years to process
SEASONS = ['Autumn', 'Spring', 'Summer', 'Winter']
CHUNK_SIZE = 800000

# Desired column order
COLUMN_ORDER = ['x', 'y', 'season', 'year', 'Aspect', 'clay', 'NVIS', 'Sand', 'Slope', 'TWI', 'PET', 'Rain', 'Tavg', 'z_score']


def load_feature_files(base_path, root_dir, feature_type, feature_name, year=None, season=None):
    """
    Loads .npy files for a specific feature based on year and season.
    """
    if feature_type == "Responsive":
        feature_path = os.path.join(base_path, root_dir, feature_type, str(year), feature_name)
    else:
        feature_path = os.path.join(base_path, root_dir, feature_type, feature_name, str(year) if year else "")

    if not os.path.isdir(feature_path):
        return None

    files = os.listdir(feature_path)
    if season:
        files = [f for f in files if season in f]

    if not files:
        return None

    file_path = os.path.join(feature_path, files[0])
    return np.load(file_path) if os.path.exists(file_path) else None


def load_constant_features(base_path, root_dirs):
    """
    Loads all constant features into memory.
    """
    constant_features = {}
    for root_dir in root_dirs:
        for feature in ['Aspect', 'clay', 'NVIS', 'Sand', 'Slope', 'TWI']:
            data = load_feature_files(base_path, root_dir, "Feature_Constant", feature)
            if data is not None:
                constant_features[feature] = data
    return constant_features


def load_seasonal_data(base_path, root_dirs, year, seasons, feature, feature_type):
    """
    Loads and stacks seasonal data for a feature (e.g., PET, Rain, z_score).
    """
    stacked_data = []
    for root_dir in root_dirs:
        for season in seasons:
            data = load_feature_files(base_path, root_dir, feature_type, feature, year, season)
            if data is not None:
                stacked_data.append(data)
    return np.stack(stacked_data, axis=0) if stacked_data else None


def process_year(year, base_path, root_dirs, seasons, chunk_size):
    """
    Processes data for a single year and saves it as a Parquet file.
    """
    print(f"Processing year: {year}")

    # Load constant features
    constant_features = load_constant_features(base_path, root_dirs)
    if not constant_features or 'Aspect' not in constant_features:
        print(f"Error: Required constant features missing for year {year}.")
        return

    # Load dynamic features
    dynamic_features = {feature: load_seasonal_data(base_path, root_dirs, year, seasons, feature, "Feature_Dynamic")
                        for feature in ['PET', 'Rain', 'Tavg']}

    # Load responsive variable
    responsive_variable = load_seasonal_data(base_path, root_dirs, year, seasons, "z_score", "Responsive")
    if responsive_variable is None:
        print(f"No responsive data (z_score) found for year {year}.")
        return

    # Get spatial dimensions
    height, width = constant_features['Aspect'].shape[-2], constant_features['Aspect'].shape[-1]
    total_points = height * width
    num_chunks = (total_points + chunk_size - 1) // chunk_size  # Ceiling division

    # Process in chunks to reduce memory usage
    dataframes = []
    for chunk in range(num_chunks):
        spatial_start = chunk * chunk_size
        spatial_end = min(spatial_start + chunk_size, total_points)

        indices = np.unravel_index(range(spatial_start, spatial_end), (height, width))
        x_coords_chunk = np.tile(indices[1], len(seasons))
        y_coords_chunk = np.tile(indices[0], len(seasons))
        season_chunk = np.repeat(seasons, len(indices[0]))

        # Build chunk data
        chunk_data = {feature: np.tile(data[indices[0], indices[1]].flatten(), len(seasons))
                      for feature, data in constant_features.items()}
        for feature, data in dynamic_features.items():
            if data is not None:
                chunk_data[feature] = data[:, indices[0], indices[1]].flatten()
        if responsive_variable is not None:
            chunk_data['z_score'] = responsive_variable[:, indices[0], indices[1]].flatten()

        # Create DataFrame
        df_chunk = pd.DataFrame({
            'x': x_coords_chunk,
            'y': y_coords_chunk,
            'season': season_chunk,
            'year': np.repeat(year, len(x_coords_chunk)),
            **chunk_data
        })

        # Drop null values directly in DataFrame
        df_chunk.dropna(inplace=True)

        dataframes.append(df_chunk)
        gc.collect()  # Force garbage collection to free memory

    # Combine all chunks and reorder columns
    year_df = pd.concat(dataframes, ignore_index=True)
    for col in COLUMN_ORDER:
        if col not in year_df.columns:
            year_df[col] = np.nan  # Fill missing columns with NaN
    year_df = year_df[COLUMN_ORDER]

    # Save to Parquet
    output_file_path = f"E:/Redoing_Preprocessing/Parquetfilecreation/South_Eastern_Highland/South_Eastern_Highland_{year}.parquet"
    year_table = pa.Table.from_pandas(year_df)
    pq.write_table(year_table, output_file_path)
    print(f"Year {year} processed and saved to {output_file_path}")


# Process all years
for year in YEARS:
    process_year(year, BASE_PATH, ROOT_DIRS, SEASONS, CHUNK_SIZE)