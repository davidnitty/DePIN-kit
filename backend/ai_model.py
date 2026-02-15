"""
AI/ML Module
TensorFlow/Keras-based predictive models for IoTeX DePIN
"""

import os
import json
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from pathlib import Path
from typing import Tuple, List, Dict, Optional
import pickle


class PredictiveMaintenanceModel:
    """
    LSTM-based predictive maintenance model for DePIN devices
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the predictive maintenance model

        Args:
            model_path: Path to saved model (optional)
        """
        self.model = None
        self.scaler = MinMaxScaler()
        self.sequence_length = 10  # Number of time steps to look back
        self.n_features = 5  # Number of features (temperature, humidity, vibration, energy, errors)

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def build_model(self) -> keras.Model:
        """
        Build LSTM model for predictive maintenance

        Returns:
            Compiled Keras model
        """
        model = keras.Sequential([
            layers.LSTM(128, return_sequences=True,
                       input_shape=(self.sequence_length, self.n_features)),
            layers.Dropout(0.2),
            layers.LSTM(64, return_sequences=False),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(16, activation='relu'),
            layers.Dense(1, activation='sigmoid')  # Probability of failure
        ])

        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
        )

        return model

    def prepare_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare time series sequences for LSTM

        Args:
            data: Normalized input data

        Returns:
            X (sequences), y (labels)
        """
        X, y = [], []

        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            y.append(data[i + self.sequence_length, 0])  # Predict next time step

        return np.array(X), np.array(y)

    def train(self, data: pd.DataFrame, labels: np.ndarray,
              epochs: int = 50, batch_size: int = 32) -> Dict:
        """
        Train the predictive maintenance model

        Args:
            data: Training data DataFrame
            labels: Binary labels (0 = normal, 1 = failure imminent)
            epochs: Number of training epochs
            batch_size: Batch size for training

        Returns:
            Training history dictionary
        """
        # Normalize features
        normalized_data = self.scaler.fit_transform(data)

        # Prepare sequences
        X, y = self.prepare_sequences(normalized_data)

        # Build model
        self.model = self.build_model()

        # Train model
        history = self.model.fit(
            X, labels[:len(X)],
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=1
        )

        return history.history

    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """
        Predict probability of device failure

        Args:
            data: Input data DataFrame

        Returns:
            Array of failure probabilities
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Normalize features
        normalized_data = self.scaler.transform(data)

        # Prepare sequences
        X, _ = self.prepare_sequences(normalized_data)

        # Make predictions
        predictions = self.model.predict(X)

        return predictions.flatten()

    def save_model(self, save_path: str):
        """
        Save model and scaler

        Args:
            save_path: Directory to save model files
        """
        os.makedirs(save_path, exist_ok=True)

        # Save Keras model
        self.model.save(f"{save_path}/model.keras")

        # Save scaler
        with open(f"{save_path}/scaler.pkl", 'wb') as f:
            pickle.dump(self.scaler, f)

        # Save configuration
        config = {
            'sequence_length': self.sequence_length,
            'n_features': self.n_features,
        }

        with open(f"{save_path}/config.json", 'w') as f:
            json.dump(config, f)

        print(f"Model saved to {save_path}")

    def load_model(self, load_path: str):
        """
        Load model and scaler

        Args:
            load_path: Directory containing model files
        """
        # Load Keras model
        self.model = keras.saving.load_model(f"{load_path}/model.keras")

        # Load scaler
        with open(f"{load_path}/scaler.pkl", 'rb') as f:
            self.scaler = pickle.load(f)

        # Load configuration
        with open(f"{load_path}/config.json", 'r') as f:
            config = json.load(f)
            self.sequence_length = config['sequence_length']
            self.n_features = config['n_features']

        print(f"Model loaded from {load_path}")


class AnomalyDetectionModel:
    """
    Autoencoder-based anomaly detection model for DePIN metrics
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the anomaly detection model

        Args:
            model_path: Path to saved model (optional)
        """
        self.encoder = None
        self.decoder = None
        self.autoencoder = None
        self.scaler = MinMaxScaler()
        self.threshold = None

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def build_model(self, input_dim: int) -> keras.Model:
        """
        Build autoencoder for anomaly detection

        Args:
            input_dim: Input feature dimension

        Returns:
            Compiled Keras model
        """
        # Encoder
        encoder_input = keras.Input(shape=(input_dim,))
        encoded = layers.Dense(32, activation='relu')(encoder_input)
        encoded = layers.Dense(16, activation='relu')(encoded)
        encoded = layers.Dense(8, activation='relu')(encoded)

        # Decoder
        decoded = layers.Dense(16, activation='relu')(encoded)
        decoded = layers.Dense(32, activation='relu')(decoded)
        decoded = layers.Dense(input_dim, activation='sigmoid')(decoded)

        # Autoencoder
        autoencoder = keras.Model(encoder_input, decoded)
        autoencoder.compile(optimizer='adam', loss='mse')

        self.encoder = keras.Model(encoder_input, encoded)
        self.autoencoder = autoencoder

        return autoencoder

    def train(self, data: pd.DataFrame, epochs: int = 100,
              batch_size: int = 32) -> Dict:
        """
        Train the anomaly detection model

        Args:
            data: Training data (assumed to be normal data)
            epochs: Number of training epochs
            batch_size: Batch size for training

        Returns:
            Training history dictionary
        """
        # Normalize features
        normalized_data = self.scaler.fit_transform(data)

        # Build model
        self.autoencoder = self.build_model(normalized_data.shape[1])

        # Train model
        history = self.autoencoder.fit(
            normalized_data, normalized_data,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=1
        )

        # Calculate threshold based on reconstruction error
        reconstructions = self.autoencoder.predict(normalized_data)
        mse = np.mean(np.power(normalized_data - reconstructions, 2), axis=1)
        self.threshold = np.mean(mse) + 2 * np.std(mse)

        return history.history

    def detect_anomalies(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Detect anomalies in device metrics

        Args:
            data: Input data DataFrame

        Returns:
            Tuple of (anomaly_flags, reconstruction_errors)
        """
        if self.autoencoder is None:
            raise ValueError("Model not trained. Call train() first.")

        # Normalize features
        normalized_data = self.scaler.transform(data)

        # Reconstruct data
        reconstructions = self.autoencoder.predict(normalized_data)

        # Calculate reconstruction error
        mse = np.mean(np.power(normalized_data - reconstructions, 2), axis=1)

        # Flag anomalies
        anomalies = mse > self.threshold

        return anomalies, mse

    def save_model(self, save_path: str):
        """
        Save model and scaler

        Args:
            save_path: Directory to save model files
        """
        os.makedirs(save_path, exist_ok=True)

        # Save Keras model
        self.autoencoder.save(f"{save_path}/autoencoder.keras")
        self.encoder.save(f"{save_path}/encoder.keras")

        # Save scaler
        with open(f"{save_path}/scaler.pkl", 'wb') as f:
            pickle.dump(self.scaler, f)

        # Save threshold
        with open(f"{save_path}/threshold.pkl", 'wb') as f:
            pickle.dump(self.threshold, f)

        print(f"Model saved to {save_path}")

    def load_model(self, load_path: str):
        """
        Load model and scaler

        Args:
            load_path: Directory containing model files
        """
        # Load Keras models
        self.autoencoder = keras.saving.load_model(f"{load_path}/autoencoder.keras")
        self.encoder = keras.saving.load_model(f"{load_path}/encoder.keras")

        # Load scaler
        with open(f"{load_path}/scaler.pkl", 'rb') as f:
            self.scaler = pickle.load(f)

        # Load threshold
        with open(f"{load_path}/threshold.pkl", 'rb') as f:
            self.threshold = pickle.load(f)

        print(f"Model loaded from {load_path}")


def generate_sample_data(n_samples: int = 1000) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Generate synthetic training data for testing

    Args:
        n_samples: Number of samples to generate

    Returns:
        Tuple of (features DataFrame, labels array)
    """
    np.random.seed(42)

    # Generate normal data
    data = pd.DataFrame({
        'temperature': np.random.normal(50, 5, n_samples),
        'humidity': np.random.normal(60, 10, n_samples),
        'vibration': np.random.normal(0.5, 0.1, n_samples),
        'energy': np.random.normal(100, 20, n_samples),
        'errors': np.random.randint(0, 2, n_samples),
    })

    # Generate labels (1 = failure imminent)
    labels = np.zeros(n_samples)

    # Introduce failures in last 10% of samples
    failure_start = int(n_samples * 0.9)
    labels[failure_start:] = 1

    # Modify data to indicate failure
    data.loc[failure_start:, 'temperature'] += 20
    data.loc[failure_start:, 'vibration'] += 0.5
    data.loc[failure_start:, 'errors'] += 3

    return data, labels


if __name__ == "__main__":
    print("Testing AI Models...")

    # Generate sample data
    print("\n1. Generating sample data...")
    data, labels = generate_sample_data(1000)
    print(f"Generated {len(data)} samples")

    # Test Predictive Maintenance Model
    print("\n2. Training Predictive Maintenance Model...")
    pm_model = PredictiveMaintenanceModel()
    history = pm_model.train(data, labels, epochs=5, batch_size=32)
    print(f"Training complete. Final accuracy: {history['accuracy'][-1]:.4f}")

    # Test Anomaly Detection Model
    print("\n3. Training Anomaly Detection Model...")
    anomaly_model = AnomalyDetectionModel()
    anomaly_history = anomaly_model.train(data, epochs=5, batch_size=32)
    print(f"Training complete. Final loss: {anomaly_history['loss'][-1]:.4f}")
    print(f"Anomaly threshold: {anomaly_model.threshold:.6f}")

    # Save models
    print("\n4. Saving models...")
    models_dir = Path(__file__).parent / "models"
    pm_model.save_model(str(models_dir / "predictive_maintenance"))
    anomaly_model.save_model(str(models_dir / "anomaly_detection"))

    print("\n✅ All models trained and saved successfully!")
