import os
import pandas as pd
import numpy as np
import logging
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import dask.dataframe as dd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# Setup logging
logging.basicConfig(level=logging.INFO)  # Changed to INFO for cleaner output

# Constants (Update these paths)
INPUT_DIRECTORY_PATH = 'F:/Chapter2_RealWork/Chapter_2_Final Analysis/Test3_ANNModel_DataPreparation/Parquet_with_lag'
OUTPUT_DIRECTORY_PATH = 'F:/Chapter2_RealWork/Chapter_2_Final Analysis/Test3_ANNModel_DataPreparation/Sensitivity_analysis'
Model_directory = 'F:/Chapter2_RealWork/Chapter_2_Final Analysis/Test3_ANNModel_DataPreparation/checkpoints_2010-2022'

# Year ranges of interest
YEARS_OF_INTEREST = set(range(2016, 2019))

# Load your features
columns_of_interest = [
    "Aspect", "clay", "NVIS", "Sand", "Slope", "TWI",
    "PET", "Rain", "Tavg", "Tavg_lag1",
    "PET_lag2", "PET_lag3", "PET_lag4", "PET_lag5",
    "Rain_lag2", "Rain_lag3", "Rain_lag4", "Rain_lag5",
    "Rain_lag6", "Rain_lag7", "Rain_lag8", "Rain_lag9"
]  # Update with your features

# Identify lag variables' columns
lag_columns = [col for col in columns_of_interest if 'lag' in col.lower()]

# Map each feature to its corresponding lag columns
# This ensures that only the lag columns related to the feature are shuffled together
feature_to_lag_columns = {}
for col in lag_columns:
    # Extract the base feature name before '_lag'
    base_feature = re.split('_lag', col)[0]
    feature_to_lag_columns.setdefault(base_feature, []).append(col)

# Compute global min and max across all files
def compute_global_min_max(files, columns):
    global_min = None
    global_max = None
    for file in files:
        ddf = dd.read_parquet(file)
        df = ddf[columns].compute()
        if global_min is None:
            global_min = df.min().values
            global_max = df.max().values
        else:
            global_min = np.minimum(global_min, df.min().values)
            global_max = np.maximum(global_max, df.max().values)
    return global_min, global_max

# Prepare the data
files = [
    os.path.join(INPUT_DIRECTORY_PATH, f) for f in os.listdir(INPUT_DIRECTORY_PATH)
    if f.endswith('.parquet') and any(str(year) in f for year in YEARS_OF_INTEREST)
]

if not files:
    raise ValueError("No Parquet files found in the specified directory matching the years of interest.")

# Compute global min and max
logging.info("Computing global min and max for scaling...")
global_min, global_max = compute_global_min_max(files, columns_of_interest)
logging.info(f"Global Min Values: {global_min}")
logging.info(f"Global Max Values: {global_max}")

# Load and concatenate all data into a single DataFrame
def load_and_concatenate(files):
    data_frames = []
    for file in files:
        logging.info(f"Loading file: {file}")
        df = pd.read_parquet(file, engine='pyarrow')
        data_frames.append(df)
    concatenated_df = pd.concat(data_frames, ignore_index=True)
    return concatenated_df

logging.info("Loading and concatenating all data...")
all_data = load_and_concatenate(files)
logging.info(f"Total data points: {all_data.shape[0]}")

# Drop unnecessary columns and handle missing values if any
columns_to_drop = ['x', 'y', 'season', 'year']
all_data = all_data.drop(columns=columns_to_drop, errors='ignore')  # Drop specified columns if present
all_data = all_data.dropna(subset=['z_score'] + columns_of_interest)  # Ensure no missing values
logging.info(f"Data points after dropping missing values: {all_data.shape[0]}")

# Scale the features using global min and max
def scale_data(df, min_vals, max_vals):
    scaled_df = df.copy()
    scaled_df[columns_of_interest] = (scaled_df[columns_of_interest] - min_vals) / (max_vals - min_vals)
    scaled_df[columns_of_interest] = scaled_df[columns_of_interest].clip(0, 1)  # Ensure within [0,1]
    return scaled_df

logging.info("Scaling the features...")
scaled_data = scale_data(all_data, global_min, global_max)
logging.info("Scaling completed.")

# Load the model architecture
logging.info("Loading the ANN model architecture...")
model = Sequential([
    Dense(256, activation='relu', input_shape=(len(columns_of_interest),)),
    Dropout(0.2),
    Dense(128, activation='relu'),
    Dropout(0.2),
    Dense(64, activation='relu'),
    Dense(1)
])

# Load the model weights
model_weights_path = os.path.join(Model_directory, 'final_ann_model.h5')
if not os.path.exists(model_weights_path):
    raise FileNotFoundError(f"Model weights not found at {model_weights_path}")

logging.info(f"Loading model weights from: {model_weights_path}")
model.load_weights(model_weights_path)
logging.info("Model weights loaded.")

# Define perturbations
perturbations = {feature: 0.30 for feature in columns_of_interest}  # 30% increase

# Sensitivity analysis function with group shuffling of feature-specific lag columns
def sensitivity_analysis(model, X, y, feature_names, perturbations, feature_to_lag_columns, n_repeats=1):
    """
    Perform permutation sensitivity analysis by perturbing each feature and measuring the impact on model performance.

    Args:
        model: Trained Keras model.
        X: Features DataFrame.
        y: Target values (numpy array).
        feature_names: List of feature names.
        perturbations: Dictionary mapping features to their perturbation values.
        feature_to_lag_columns: Dictionary mapping features to their associated lag columns.
        n_repeats: Number of times to repeat the shuffling for averaging.

    Returns:
        Dictionary mapping features to their averaged sensitivity scores.
    """
    print("Starting sensitivity analysis...")
    print(f"Shape of X: {X.shape}")

    # Initialize dictionary to hold sensitivity scores
    sensitivity_scores = {feature: [] for feature in feature_names}

    for repeat in range(n_repeats):
        print(f"\n--- Repeat {repeat + 1}/{n_repeats} ---")
        for i, feature in enumerate(feature_names):
            print(f"\nAnalyzing feature: {feature} (index {i})")

            # Generate a unique seed for each feature and repeat to ensure different shuffles
            shuffle_seed = 42 + i + repeat * len(feature_names)
            print(f"Shuffling with random_state={shuffle_seed}")

            # Shuffle the entire dataset row-wise
            print("Shuffling the entire dataset row-wise...")
            X_shuffled = X.sample(frac=1, random_state=shuffle_seed).reset_index(drop=True)
            y_shuffled = y[X_shuffled.index]

            # Identify and shuffle the lag columns associated with the current feature, including the feature itself
            current_feature_lag_columns = feature_to_lag_columns.get(feature, []).copy()
            if feature not in current_feature_lag_columns and feature in X_shuffled.columns:
                current_feature_lag_columns.append(feature)

            if current_feature_lag_columns:
                print(f"Shuffling lag columns for feature '{feature}': {current_feature_lag_columns}")
                # Extract the lag columns as a separate DataFrame
                lag_data = X_shuffled[current_feature_lag_columns]

                # Shuffle the rows of the lag_data DataFrame as a group
                lag_data_shuffled = lag_data.sample(frac=1, random_state=shuffle_seed).reset_index(drop=True)

                # Assign the shuffled lag_data back to X_shuffled
                X_shuffled[current_feature_lag_columns] = lag_data_shuffled
                print(f"Shuffled lag columns for feature '{feature}': {current_feature_lag_columns}")
            else:
                print(f"No lag columns to shuffle for feature '{feature}'.")

            # Apply perturbation to the current feature
            perturbation_value = perturbations.get(feature, 0)
            print(f"Applying perturbation of +{perturbation_value} to feature: {feature}")
            X_perturbed = X_shuffled.copy()
            X_perturbed[feature] = X_perturbed[feature] + perturbation_value
            X_perturbed[feature] = np.clip(X_perturbed[feature], 0, 1)  # Ensure within [0,1]

            # Calculate perturbed predictions
            print("Calculating perturbed predictions...")
            perturbed_predictions = model.predict(X_perturbed, batch_size=1024)

            # Calculate the sensitivity score (Mean Absolute Error)
            sensitivity_score = np.mean(np.abs(perturbed_predictions - y_shuffled))
            sensitivity_scores[feature].append(sensitivity_score)
            print(f"Sensitivity score for {feature}: {sensitivity_score}")

    # Average the sensitivity scores over repeats
    averaged_sensitivity_scores = {
        feature: np.mean(scores) if scores else 0 for feature, scores in sensitivity_scores.items()
    }
    return averaged_sensitivity_scores

# Prepare data for sensitivity analysis
logging.info("Preparing data for sensitivity analysis...")
X = scaled_data[columns_of_interest]
y = scaled_data['z_score'].to_numpy().reshape(-1, 1)  # Ensure y is in the correct shape

# Perform sensitivity analysis with multiple repeats for robustness
n_repeats = 5  # You can adjust this number based on your requirements
logging.info(f"Performing sensitivity analysis with {n_repeats} repeats...")
sensitivity_scores = sensitivity_analysis(
    model,
    X,
    y,
    columns_of_interest,
    perturbations,
    feature_to_lag_columns,
    n_repeats=n_repeats
)

# Convert sensitivity scores to DataFrame
sensitivity_df = pd.DataFrame({
    'feature': list(sensitivity_scores.keys()),
    'sensitivity_score': list(sensitivity_scores.values())
})

# Save the results
final_csv_path = os.path.join(OUTPUT_DIRECTORY_PATH, 'global_feature_importances_test_2_2016-2019_transition.csv')
logging.info(f"Saving sensitivity analysis results to: {final_csv_path}")
sensitivity_df.to_csv(final_csv_path, index=False)