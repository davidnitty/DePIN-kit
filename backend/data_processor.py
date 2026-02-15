"""
Data Processing Module
Clean and aggregate data from DePINs
"""

import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Process and aggregate data from DePIN devices
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize data processor

        Args:
            db_path: Path to SQLite database
        """
        if db_path is None:
            db_path = Path(__file__).parent / "data" / "metrics.db"

        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for storing metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                value REAL NOT NULL,
                data_type TEXT NOT NULL,
                is_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create aggregated_metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS aggregated_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                period TEXT NOT NULL,
                start_time INTEGER NOT NULL,
                end_time INTEGER NOT NULL,
                avg_value REAL NOT NULL,
                min_value REAL NOT NULL,
                max_value REAL NOT NULL,
                count INTEGER NOT NULL,
                data_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

        logger.info(f"Database initialized at {self.db_path}")

    def clean_data(self, data: List[Dict]) -> List[Dict]:
        """
        Clean incoming data by removing outliers and invalid entries

        Args:
            data: List of raw data points

        Returns:
            List of cleaned data points
        """
        if not data:
            return []

        df = pd.DataFrame(data)

        # Remove entries with missing values
        df = df.dropna(subset=['value', 'data_type', 'timestamp'])

        # Remove outliers using IQR method
        for data_type in df['data_type'].unique():
            type_df = df[df['data_type'] == data_type]
            Q1 = type_df['value'].quantile(0.25)
            Q3 = type_df['value'].quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            # Filter out outliers
            df = df[~((df['data_type'] == data_type) &
                      ((df['value'] < lower_bound) | (df['value'] > upper_bound)))]

        # Convert back to list of dictionaries
        cleaned_data = df.to_dict('records')

        logger.info(f"Cleaned data: {len(data)} -> {len(cleaned_data)} entries")
        return cleaned_data

    def aggregate_data(self, device_id: int, data_type: str,
                       period: str = "hour") -> Dict:
        """
        Aggregate data for a device over a time period

        Args:
            device_id: Device ID
            data_type: Type of data to aggregate
            period: Aggregation period ("hour", "day", "week")

        Returns:
            Dictionary with aggregated statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate time range
        now = int(datetime.utcnow().timestamp())
        period_seconds = {
            "hour": 3600,
            "day": 86400,
            "week": 604800
        }

        start_time = now - period_seconds.get(period, 3600)

        # Query metrics
        cursor.execute("""
            SELECT
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value,
                COUNT(*) as count
            FROM metrics
            WHERE device_id = ?
                AND data_type = ?
                AND timestamp >= ?
                AND timestamp <= ?
        """, (device_id, data_type, start_time, now))

        result = cursor.fetchone()

        if result and result[3] > 0:
            aggregated = {
                "device_id": device_id,
                "period": period,
                "start_time": start_time,
                "end_time": now,
                "avg_value": result[0],
                "min_value": result[1],
                "max_value": result[2],
                "count": result[3],
                "data_type": data_type
            }

            # Store aggregated metrics
            cursor.execute("""
                INSERT INTO aggregated_metrics
                (device_id, period, start_time, end_time, avg_value, min_value, max_value, count, data_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                device_id, period, start_time, now,
                result[0], result[1], result[2], result[3], data_type
            ))

            conn.commit()
            conn.close()

            return aggregated
        else:
            conn.close()
            return {}

    def store_metrics(self, device_id: int, metrics: List[Dict]):
        """
        Store metrics in database

        Args:
            device_id: Device ID
            metrics: List of metric data
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for metric in metrics:
            cursor.execute("""
                INSERT INTO metrics (device_id, timestamp, value, data_type, is_verified)
                VALUES (?, ?, ?, ?, ?)
            """, (
                device_id,
                metric.get('timestamp', int(datetime.utcnow().timestamp())),
                metric.get('value', 0),
                metric.get('data_type', 'unknown'),
                metric.get('is_verified', False)
            ))

        conn.commit()
        conn.close()

        logger.info(f"Stored {len(metrics)} metrics for device {device_id}")

    def get_metrics(self, device_id: int, data_type: Optional[str] = None,
                    start_time: Optional[int] = None, end_time: Optional[int] = None,
                    limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve metrics from database

        Args:
            device_id: Device ID
            data_type: Filter by data type (optional)
            start_time: Start timestamp (optional)
            end_time: End timestamp (optional)
            limit: Maximum number of records (optional)

        Returns:
            List of metric dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM metrics WHERE device_id = ?"
        params = [device_id]

        if data_type:
            query += " AND data_type = ?"
            params.append(data_type)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)

        columns = ['id', 'device_id', 'timestamp', 'value', 'data_type', 'is_verified', 'created_at']
        metrics = []

        for row in cursor.fetchall():
            metrics.append({
                col: val for col, val in zip(columns, row)
            })

        conn.close()
        return metrics

    def get_device_statistics(self, device_id: int) -> Dict:
        """
        Get comprehensive statistics for a device

        Args:
            device_id: Device ID

        Returns:
            Dictionary with device statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get overall statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total_metrics,
                COUNT(DISTINCT data_type) as data_types,
                MIN(timestamp) as first_metric,
                MAX(timestamp) as last_metric
            FROM metrics
            WHERE device_id = ?
        """, (device_id,))

        result = cursor.fetchone()

        # Get statistics by data type
        cursor.execute("""
            SELECT
                data_type,
                COUNT(*) as count,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value
            FROM metrics
            WHERE device_id = ?
            GROUP BY data_type
        """, (device_id,))

        by_type = {}
        for row in cursor.fetchall():
            by_type[row[0]] = {
                "count": row[1],
                "avg_value": row[2],
                "min_value": row[3],
                "max_value": row[4]
            }

        conn.close()

        return {
            "device_id": device_id,
            "total_metrics": result[0],
            "data_types": result[1],
            "first_metric": result[2],
            "last_metric": result[3],
            "by_type": by_type
        }

    def export_data(self, device_id: int, format: str = "csv",
                    output_path: Optional[str] = None) -> str:
        """
        Export device data to file

        Args:
            device_id: Device ID
            format: Export format ("csv", "json")
            output_path: Output file path (optional)

        Returns:
            Path to exported file
        """
        metrics = self.get_metrics(device_id)

        if output_path is None:
            output_path = Path(__file__).parent / "data" / f"device_{device_id}_export.{format}"

        if format == "csv":
            df = pd.DataFrame(metrics)
            df.to_csv(output_path, index=False)
        elif format == "json":
            with open(output_path, 'w') as f:
                json.dump(metrics, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Exported {len(metrics)} metrics to {output_path}")
        return str(output_path)

    def cleanup_old_data(self, days: int = 30):
        """
        Remove data older than specified days

        Args:
            days: Number of days to retain data
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_time = int((datetime.utcnow() - timedelta(days=days)).timestamp())

        cursor.execute("""
            DELETE FROM metrics
            WHERE timestamp < ?
        """, (cutoff_time,))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Cleaned up {deleted_count} old metrics")


class DataValidator:
    """
    Validate data from DePIN devices
    """

    @staticmethod
    def validate_metric(data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate a single metric

        Args:
            data: Metric data dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        required_fields = ['value', 'data_type', 'timestamp']

        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"

        # Validate value
        try:
            value = float(data['value'])
            if not (-1e10 <= value <= 1e10):
                return False, "Value out of reasonable range"
        except (ValueError, TypeError):
            return False, "Invalid value format"

        # Validate timestamp
        try:
            timestamp = int(data['timestamp'])
            now = int(datetime.utcnow().timestamp())

            if timestamp > now + 3600:
                return False, "Timestamp is in the future"

            if timestamp < now - 86400 * 365:
                return False, "Timestamp is too old"
        except (ValueError, TypeError):
            return False, "Invalid timestamp format"

        # Validate data_type
        valid_types = ['temperature', 'humidity', 'vibration', 'energy', 'pressure', 'flow', 'other']

        if data['data_type'] not in valid_types:
            return False, f"Invalid data_type: {data['data_type']}"

        return True, None

    @staticmethod
    def validate_batch(data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Validate a batch of metrics

        Args:
            data: List of metric dictionaries

        Returns:
            Tuple of (valid_data, invalid_data)
        """
        valid_data = []
        invalid_data = []

        for metric in data:
            is_valid, error = DataValidator.validate_metric(metric)

            if is_valid:
                valid_data.append(metric)
            else:
                metric['validation_error'] = error
                invalid_data.append(metric)

        logger.info(f"Validated {len(data)} metrics: {len(valid_data)} valid, {len(invalid_data)} invalid")

        return valid_data, invalid_data


if __name__ == "__main__":
    print("Testing Data Processor...")

    # Create sample data
    sample_metrics = [
        {
            "timestamp": int(datetime.utcnow().timestamp()) - 3600,
            "value": 25.5,
            "data_type": "temperature",
            "is_verified": True
        },
        {
            "timestamp": int(datetime.utcnow().timestamp()) - 1800,
            "value": 26.2,
            "data_type": "temperature",
            "is_verified": True
        },
        {
            "timestamp": int(datetime.utcnow().timestamp()),
            "value": 60.0,
            "data_type": "humidity",
            "is_verified": False
        }
    ]

    # Initialize processor
    processor = DataProcessor()

    # Store metrics
    processor.store_metrics(device_id=1, metrics=sample_metrics)

    # Get metrics
    retrieved = processor.get_metrics(device_id=1)
    print(f"Retrieved {len(retrieved)} metrics")

    # Get statistics
    stats = processor.get_device_statistics(device_id=1)
    print(f"Statistics: {stats}")

    # Aggregate data
    aggregated = processor.aggregate_data(device_id=1, data_type="temperature", period="hour")
    print(f"Aggregated: {aggregated}")

    print("\n✅ Data Processor test complete!")
