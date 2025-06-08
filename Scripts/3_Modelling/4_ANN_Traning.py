import os
import pandas as pd
import random
import numpy as np
import dask.dataframe as dd
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.model_selection import train_test_split

# Step 1: Get list of all parquet files in your directory
parquet_files = [
    os.path.join('F:/Chapter2_RealWork/Chapter_2_Final Analysis/Test3_ANNModel_DataPreparation/Parquet_with_lag', f)
    for f in os.listdir('F:/Chapter2_RealWork/Chapter_2_Final Analysis/Test3_ANNModel_DataPreparation/Parquet_with_lag')
    if f.endswith('.parquet')
]

# Calculate global min and max values across all files
def compute_min_max(files):
    first_file = True
    for file in files:
        ddf = dd.read_parquet(file)
        df = ddf.compute()
        features = [col for col in df.columns if col not in ['x', 'y', 'season', 'year', 'z_score']]
        df = df[features]
        
        if first_file:
            nb_features = len(features)
            global_min = np.full(nb_features, np.inf)
            global_max = np.full(nb_features, -np.inf)
            first_file = False
        
        min_values = df.min().values
        max_values = df.max().values
        global_min = np.minimum(global_min, min_values)
        global_max = np.maximum(global_max, max_values)
    
    return global_min, global_max, nb_features

# Precompute global min, max values
global_min, global_max, nb_features = compute_min_max(parquet_files)

# Step 2: Define a function to load, shuffle, and train the model on each batch of files
def train_model_on_batch(file_batch, model, checkpoint_dir, epoch, batch_num):
    # Load parquet files individually and concatenate
    df_list = [dd.read_parquet(file).compute() for file in file_batch]
    df = pd.concat(df_list, ignore_index=True)

    # Drop unwanted columns
    columns_to_drop = ['season', 'x', 'y', 'year']
    df = df.drop(columns=columns_to_drop, errors='ignore')

    # Ensure the 'z_score' column exists
    if 'z_score' not in df.columns:
        raise KeyError("'z_score' column not found in the dataset. Please check the input files.")

    # Separate features and target variable
    X = df.drop(columns=['z_score']).values
    y = df['z_score'].values

    # Normalize the features using global min and max
    X = (X - global_min) / (global_max - global_min)

    # Shuffle the data before splitting
    combined = list(zip(X, y))
    random.shuffle(combined)
    X, y = zip(*combined)

    # Convert to numpy arrays after shuffling
    X = np.array(X)
    y = np.array(y)

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train the model
    history = model.fit(
        X_train, y_train,
        epochs=1, batch_size=1000, validation_data=(X_test, y_test)
    )

    # Save the model checkpoint
    checkpoint_filepath = os.path.join(checkpoint_dir, f'epoch{epoch}_batch{batch_num}.weights.h5')
    model.save_weights(checkpoint_filepath)
    print(f"Checkpoint saved: {checkpoint_filepath}")

    # Evaluate the model
    test_loss, test_mae = model.evaluate(X_test, y_test)
    print(f"Test Loss: {test_loss}, Test MAE: {test_mae}")

# Step 3: Train the model for multiple epochs with an adaptive learning rate
num_epochs = 10  # Specify the number of epochs
batch_size = 7   # Number of files to process per batch
checkpoint_dir = 'checkpoints_2010-2022'  # Directory to save checkpoints
os.makedirs(checkpoint_dir, exist_ok=True)  # Ensure the checkpoint directory exists

# Initialize a new model
model = models.Sequential()
model.add(layers.Dense(256, activation='relu', input_dim=nb_features))
model.add(layers.Dropout(0.2))
model.add(layers.Dense(128, activation='relu'))
model.add(layers.Dropout(0.2))
model.add(layers.Dense(64, activation='relu'))
model.add(layers.Dense(1))  # Output layer for regression

# Define initial learning rate and decay rate
initial_learning_rate = 0.0001  # Adjust as needed
decay_rate = 0.9  # Adjust as needed

# Compile the model once
#optimizer = tf.keras.optimizers.Adam(learning_rate=initial_learning_rate) 
optimizer = tf.keras.optimizers.SGD(learning_rate=initial_learning_rate)
model.compile(optimizer=optimizer, loss='mean_squared_error', metrics=['mae'])

# Train for multiple epochs with adaptive learning rate
for epoch in range(num_epochs):
    # Adjust learning rate
    new_learning_rate = initial_learning_rate * (decay_rate ** epoch)
    tf.keras.backend.set_value(model.optimizer.learning_rate, new_learning_rate)
    print(f"Epoch {epoch + 1}/{num_epochs} - Learning Rate: {new_learning_rate}")

    # Shuffle the list of files at the start of each epoch
    random.shuffle(parquet_files)

    # Iterate over files in batches
    for batch_num, i in enumerate(range(0, len(parquet_files), batch_size)):
        # Get a batch of files
        file_batch = parquet_files[i:i + batch_size]
        print(f"Training on files: {file_batch}")
        train_model_on_batch(file_batch, model, checkpoint_dir, epoch + 1, batch_num + 1)

# Save the final model
final_model_path = os.path.join(checkpoint_dir, 'final_ann_model.h5')
model.save(final_model_path)
print(f"Final model saved as '{final_model_path}'.")
