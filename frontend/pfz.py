# -*- coding: utf-8 -*-
"""PFZ(priyal).ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1bqcKXQLcyBZuXaFrNpobQ6CYQ9llsI8f
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LinearRegression
import numpy as np

from google.colab import files
uploaded = files.upload()

file_path = 'PfzForecast_SOUTH TAMILNADU (merged).csv'
df = pd.read_csv(file_path)
df.dropna(inplace=True)
df

df["Distance (km)"] = df["Distance (km) From-To"].apply(lambda x: np.mean([float(i) for i in str(x).split('-')]))
df["Depth (m)"] = df["Depth (mtr) From-To"].apply(lambda x: np.mean([float(i) for i in str(x).split('-')]))
df

def dms_to_decimal(dms):
    parts = dms.split()
    degrees, minutes, seconds, direction = float(parts[0]), float(parts[1]), float(parts[2]), parts[3]
    decimal = degrees + (minutes / 60) + (seconds / 3600)
    if direction in ['S', 'W']:  # South and West are negative
        decimal *= -1
    return decimal

df["Latitude"] = df["Latitude (dms)"].apply(dms_to_decimal)
df["Longitude"] = df["Longitude (dms)"].apply(dms_to_decimal)
df

le = LabelEncoder()
df["Direction"] = le.fit_transform(df["Direction"])
df

features = ["Bearing (deg)", "Distance (km)", "Direction"]
target_latitude = "Latitude"
target_longitude = "Longitude"
target_depth = "Depth (m)"

X_train, X_test, y_train_lat, y_test_lat = train_test_split(df[features], df[target_latitude], test_size=0.2, random_state=42)
model_latitude = LinearRegression()
model_latitude.fit(X_train, y_train_lat)

X_train, X_test, y_train_lon, y_test_lon = train_test_split(df[features], df[target_longitude], test_size=0.2, random_state=42)
model_longitude = LinearRegression()
model_longitude.fit(X_train, y_train_lon)

X_train, X_test, y_train_depth, y_test_depth = train_test_split(df[features], df[target_depth], test_size=0.2, random_state=42)
model_depth = LinearRegression()
model_depth.fit(X_train, y_train_depth)

# Function to convert Decimal to DMS format
def decimal_to_dms(decimal, is_latitude=True):
    direction = 'N' if is_latitude and decimal >= 0 else 'S' if is_latitude else 'E' if decimal >= 0 else 'W'
    decimal = abs(decimal)
    degrees = int(decimal)
    minutes = int((decimal - degrees) * 60)
    seconds = round((decimal - degrees - minutes / 60) * 3600, 2)
    return f"{degrees} {minutes} {seconds} {direction}"

def predict_coordinates_and_depth(coast_name):
    row = df[df["From the coast of"] == coast_name]
    if row.empty:
        return "Coast not found in dataset."

    X_input = row[features]

    predicted_latitude = model_latitude.predict(X_input)[0]
    predicted_longitude = model_longitude.predict(X_input)[0]
    predicted_depth = model_depth.predict(X_input)[0]

    lat_dms = decimal_to_dms(predicted_latitude, is_latitude=True)
    lon_dms = decimal_to_dms(predicted_longitude, is_latitude=False)

    return lat_dms, lon_dms, round(predicted_depth, 2)

user_coast = input("Enter the coastal location: ")
result = predict_coordinates_and_depth(user_coast)

if isinstance(result, str):
    print(result)
else:
    lat, lon, depth = result
    print(f"Predicted Data for {user_coast}:")
    print(f"Latitude (DMS): {lat}")
    print(f"Longitude (DMS): {lon}")
    print(f"Depth (m): {depth}")

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Function to evaluate model performance
def evaluate_model(model, X_test, y_test, target_name):
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    print(f"Model Performance for {target_name}:")
    print(f"Mean Absolute Error (MAE): {mae:.4f}")
    print(f"Mean Squared Error (MSE): {mse:.4f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")
    print(f"R² Score: {r2:.4f}")
    print("-" * 50)

# Evaluate Latitude model
evaluate_model(model_latitude, X_test, y_test_lat, "Latitude")

# Evaluate Longitude model
evaluate_model(model_longitude, X_test, y_test_lon, "Longitude")

# Evaluate Depth model
evaluate_model(model_depth, X_test, y_test_depth, "Depth")