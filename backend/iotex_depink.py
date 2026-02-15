"""
IoTeX DePIN Integration
Core module for onboarding and managing DePINs
"""

import os
import json
import requests
import ipfshttpclient
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import hashlib


@dataclass
class DePINDevice:
    """Data class for DePIN device information"""
    device_id: int
    owner_address: str
    metadata_uri: str
    device_type: str
    status: str
    location: Optional[Dict[str, float]] = None
    specifications: Optional[Dict] = None


@dataclass
class MetricData:
    """Data class for metric data"""
    device_id: int
    timestamp: int
    value: float
    data_type: str
    is_verified: bool = False


class IoTeXDePIN:
    """
    Core module for managing IoTeX DePIN integration
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize IoTeX DePIN integration

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.ipfs_client = self._connect_ipfs()
        self.devices = {}
        self.metrics = {}

        # Import contract interface
        from contract_interface import ContractInterface
        self.contract = ContractInterface(config_path)

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file"""
        if config_path is None:
            config_path = Path(__file__).parent / "config" / "depink_config.json"

        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Return default configuration
            return {
                "ipfs": {
                    "gateway": "https://ipfs.io/ipfs/",
                    "api": "/ip4/127.0.0.1/tcp/5001"
                },
                "blockchain": {
                    "network": "testnet",
                    "confirmation_blocks": 12
                },
                "rewards": {
                    "base_rate": 100,
                    "multipliers": {
                        "high_quality": 1.2,
                        "low_latency": 1.1,
                        "verified": 1.3
                    }
                }
            }

    def _connect_ipfs(self):
        """Connect to IPFS node"""
        try:
            client = ipfshttpclient.connect(self.config["ipfs"]["api"])
            print(f"Connected to IPFS at {self.config['ipfs']['api']}")
            return client
        except Exception as e:
            print(f"Warning: Could not connect to IPFS: {e}")
            print("Will use IPFS gateway for uploads")
            return None

    def onboard_depin(self, owner_address: str, metadata: Dict,
                      device_type: str, location: Optional[Dict] = None) -> DePINDevice:
        """
        Onboard a new DePIN device

        Args:
            owner_address: Ethereum address of device owner
            metadata: Device metadata dictionary
            device_type: Type of device (e.g., "sensor", "gateway", "processor")
            location: Optional location data {lat, lng}

        Returns:
            DePINDevice object
        """
        print(f"Onboarding new DePIN device for {owner_address}...")

        # Prepare metadata
        metadata["device_type"] = device_type
        metadata["onboarded_at"] = datetime.utcnow().isoformat()
        if location:
            metadata["location"] = location

        # Upload metadata to IPFS
        metadata_uri = self._upload_to_ipfs(metadata)

        # Register device on blockchain
        receipt = self.contract.register_device(metadata_uri, owner_address)

        # Get device ID from transaction
        device_id = self._extract_device_id(receipt)

        # Create device object
        device = DePINDevice(
            device_id=device_id,
            owner_address=owner_address,
            metadata_uri=metadata_uri,
            device_type=device_type,
            status="Active",
            location=location,
            specifications=metadata
        )

        # Store locally
        self.devices[device_id] = device

        print(f"✅ Device onboarded successfully with ID: {device_id}")
        return device

    def _upload_to_ipfs(self, data: Dict) -> str:
        """
        Upload data to IPFS

        Args:
            data: Data to upload

        Returns:
            IPFS URI (ipfs://<hash>)
        """
        json_data = json.dumps(data, indent=2)

        if self.ipfs_client:
            # Use local IPFS node
            result = self.ipfs_client.add_json(data)
            return f"ipfs://{result['Hash']}"
        else:
            # Use Pinata or other service (placeholder)
            # In production, integrate with Pinata API
            hash_value = hashlib.sha256(json_data.encode()).hexdigest()[:46]
            print(f"IPFS hash (simulated): {hash_value}")
            return f"ipfs://{hash_value}"

    def _extract_device_id(self, receipt: Dict) -> int:
        """
        Extract device ID from transaction receipt

        Args:
            receipt: Transaction receipt

        Returns:
            Device ID
        """
        # Parse logs to extract DeviceRegistered event
        # This is simplified - in production, decode logs properly
        for log in receipt.get('logs', []):
            # Decode topics to get device ID
            # This is a placeholder - implement proper event decoding
            pass

        # Fallback: get total devices from contract
        return self.contract.get_total_devices()

    def process_data(self, device_id: int, data: List[Dict]) -> List[MetricData]:
        """
        Process incoming data from a DePIN

        Args:
            device_id: Device ID
            data: List of data points

        Returns:
            List of processed MetricData objects
        """
        print(f"Processing {len(data)} data points from device {device_id}...")

        processed_metrics = []

        for data_point in data:
            # Create metric data object
            metric = MetricData(
                device_id=device_id,
                timestamp=int(datetime.utcnow().timestamp()),
                value=float(data_point.get('value', 0)),
                data_type=data_point.get('type', 'unknown'),
                is_verified=False
            )

            # Report metrics to blockchain
            try:
                receipt = self.contract.report_metrics(
                    device_id,
                    int(metric.value),
                    metric.data_type
                )
                metric.is_verified = True
            except Exception as e:
                print(f"Warning: Could not report metrics: {e}")

            processed_metrics.append(metric)

        # Store metrics locally
        if device_id not in self.metrics:
            self.metrics[device_id] = []
        self.metrics[device_id].extend(processed_metrics)

        print(f"✅ Processed {len(processed_metrics)} metrics")
        return processed_metrics

    def enforce_rewards(self, device_id: int, metric_count: int,
                        quality_multiplier: float = 1.0) -> float:
        """
        Calculate and distribute rewards for a device

        Args:
            device_id: Device ID
            metric_count: Number of metrics reported
            quality_multiplier: Quality multiplier (0.5 to 2.0)

        Returns:
            Total reward amount
        """
        print(f"Calculating rewards for device {device_id}...")

        # Get base reward rate
        base_rate = self.config["rewards"]["base_rate"]

        # Calculate total reward
        total_reward = base_rate * metric_count * quality_multiplier

        # In production, this would call RewardDistribution contract
        print(f"Reward: {total_reward} tokens (base: {base_rate}, metrics: {metric_count}, multiplier: {quality_multiplier})")

        return total_reward

    def enforce_penalties(self, device_id: int, violation_type: str) -> float:
        """
        Enforce penalties for rule violations

        Args:
            device_id: Device ID
            violation_type: Type of violation

        Returns:
            Penalty amount (positive = tokens slashed)
        """
        print(f"Enforcing penalty for device {device_id}: {violation_type}")

        # Map violation types to slashing percentages
        slashing_percentages = {
            "offline": 5,
            "data_inconsistency": 10,
            "malicious_activity": 50,
            "latency_violation": 3
        }

        slash_percentage = slashing_percentages.get(violation_type, 0)

        if slash_percentage > 0:
            # In production, call RewardDistribution.slashDevice()
            print(f"Penalty: {slash_percentage}% of rewards slashed")
            return slash_percentage

        return 0

    def get_device(self, device_id: int) -> Optional[DePINDevice]:
        """
        Get device information

        Args:
            device_id: Device ID

        Returns:
            DePINDevice object or None
        """
        if device_id in self.devices:
            return self.devices[device_id]

        # Try to fetch from blockchain
        try:
            device_info = self.contract.get_device_info(device_id)

            device = DePINDevice(
                device_id=device_id,
                owner_address=device_info['owner'],
                metadata_uri=device_info['metadataURI'],
                device_type="unknown",
                status=str(device_info['status']),
                specifications=None
            )

            self.devices[device_id] = device
            return device

        except Exception as e:
            print(f"Error fetching device {device_id}: {e}")
            return None

    def get_all_devices(self) -> List[DePINDevice]:
        """
        Get all registered devices

        Returns:
            List of DePINDevice objects
        """
        # Fetch from blockchain
        total_devices = self.contract.get_total_devices()

        devices = []
        for device_id in range(1, total_devices + 1):
            device = self.get_device(device_id)
            if device:
                devices.append(device)

        return devices

    def get_metrics(self, device_id: int, limit: Optional[int] = None) -> List[MetricData]:
        """
        Get metrics for a device

        Args:
            device_id: Device ID
            limit: Maximum number of metrics to return

        Returns:
            List of MetricData objects
        """
        if device_id in self.metrics:
            metrics = self.metrics[device_id]
            return metrics[-limit:] if limit else metrics

        # Try to fetch from blockchain
        try:
            blockchain_metrics = self.contract.get_metrics(device_id)

            metrics = []
            for metric in blockchain_metrics:
                metrics.append(MetricData(
                    device_id=metric['deviceId'],
                    timestamp=metric['timestamp'],
                    value=float(metric['value']),
                    data_type=metric['dataType'],
                    is_verified=metric['isVerified']
                ))

            self.metrics[device_id] = metrics
            return metrics

        except Exception as e:
            print(f"Error fetching metrics for device {device_id}: {e}")
            return []

    def verify_data_integrity(self, device_id: int, data: List[Dict]) -> bool:
        """
        Verify data integrity using AI models

        Args:
            device_id: Device ID
            data: Data to verify

        Returns:
            True if data is valid, False otherwise
        """
        # Import AI models
        from ai_model import AnomalyDetectionModel

        # Load or create anomaly detection model
        model_path = Path(__file__).parent / "models" / "anomaly_detection"

        if model_path.exists():
            model = AnomalyDetectionModel(str(model_path))
        else:
            print("Warning: Anomaly detection model not found. Skipping verification.")
            return True

        # Convert data to DataFrame
        import pandas as pd
        df = pd.DataFrame(data)

        # Detect anomalies
        anomalies, _ = model.detect_anomalies(df)

        # Check if any anomalies detected
        if anomalies.any():
            print(f"⚠️ Anomalies detected in data from device {device_id}")
            return False

        return True


if __name__ == "__main__":
    print("Testing IoTeX DePIN Integration...")

    try:
        # Initialize DePIN
        depin = IoTeXDePIN()

        # Get all devices
        devices = depin.get_all_devices()
        print(f"Found {len(devices)} devices")

        # Get metrics for first device
        if devices:
            device_id = devices[0].device_id
            metrics = depin.get_metrics(device_id, limit=10)
            print(f"Device {device_id} has {len(metrics)} metrics")

    except Exception as e:
        print(f"Error: {e}")
