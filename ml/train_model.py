import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib
from pathlib import Path


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "ml" / "models"
MODEL_FILE = MODEL_DIR / "fuel_prediction_model.pkl"

MODEL_DIR.mkdir(parents=True, exist_ok=True)


# Simulated training data
np.random.seed(42)

distance_km = np.random.uniform(10, 500, 500)
speed_kmh = np.random.uniform(20, 100, 500)
fuel_level = np.random.uniform(10, 100, 500)

fuel_consumption = (
    0.08 * distance_km
    + 0.03 * speed_kmh
    + np.random.normal(0, 2, 500)
)


# Input features
X = np.column_stack([
    distance_km,
    speed_kmh,
    fuel_level
])

# Target
y = fuel_consumption


# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


# Create ML model
model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)


# Train
model.fit(X_train, y_train)


# Test
predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, predictions)


print("==========================================")
print(" FleetVision 360 ML Model")
print("==========================================")
print(f"Training records : {len(X_train)}")
print(f"Testing records  : {len(X_test)}")
print(f"Mean Absolute Error: {mae:.2f}")


# Save model
joblib.dump(model, MODEL_FILE)

print()
print("Model training completed successfully.")
print(f"Model saved to: {MODEL_FILE}")