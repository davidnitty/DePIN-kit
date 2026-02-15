"""
Reward System
Algorithm for distributing rewards to DePIN devices
"""

import os
import json
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RewardMultiplier(Enum):
    """Reward multipliers for different performance levels"""
    EXCELLENT = 1.5
    GOOD = 1.2
    AVERAGE = 1.0
    POOR = 0.7
    MINIMAL = 0.3


@dataclass
class RewardCalculation:
    """Data class for reward calculation results"""
    device_id: int
    metric_count: int
    base_reward: float
    multipliers: Dict[str, float]
    final_reward: float
    calculated_at: str


class RewardSystem:
    """
    Calculate and distribute rewards to DePIN devices
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize reward system

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.db_path = Path(__file__).parent / "data" / "rewards.db"

        # Initialize database
        self._init_database()

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file"""
        if config_path is None:
            config_path = Path(__file__).parent / "config" / "reward_config.json"

        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default configuration
            return {
                "base_reward_rate": 100,  # Tokens per metric
                "multipliers": {
                    "data_quality": {
                        "excellent": 1.5,
                        "good": 1.2,
                        "average": 1.0,
                        "poor": 0.7
                    },
                    "uptime": {
                        "high": 1.3,
                        "medium": 1.1,
                        "low": 0.8
                    },
                    "latency": {
                        "low": 1.2,
                        "medium": 1.0,
                        "high": 0.9
                    },
                    "verification": {
                        "verified": 1.3,
                        "unverified": 1.0
                    }
                },
                "penalties": {
                    "offline": -0.5,
                    "data_inconsistency": -0.3,
                    "latency_violation": -0.2
                },
                "min_reward": 10,
                "max_reward": 10000
            }

    def _init_database(self):
        """Initialize SQLite database for rewards"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create rewards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                metric_count INTEGER NOT NULL,
                base_reward REAL NOT NULL,
                multipliers TEXT NOT NULL,
                penalties REAL NOT NULL,
                final_reward REAL NOT NULL,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create reward_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reward_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                reward_amount REAL NOT NULL,
                reward_type TEXT NOT NULL,
                distributed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tx_hash TEXT
            )
        """)

        conn.commit()
        conn.close()

        logger.info(f"Rewards database initialized at {self.db_path}")

    def calculate_rewards(self, device_id: int, metrics: List[Dict],
                         performance_data: Optional[Dict] = None) -> RewardCalculation:
        """
        Calculate rewards for a device based on metrics and performance

        Args:
            device_id: Device ID
            metrics: List of reported metrics
            performance_data: Optional performance data (uptime, latency, etc.)

        Returns:
            RewardCalculation object
        """
        metric_count = len(metrics)
        base_reward = self.config["base_reward_rate"] * metric_count

        multipliers = {}

        # Data quality multiplier
        if metrics:
            quality_score = self._calculate_data_quality(metrics)
            quality_multiplier = self._get_quality_multiplier(quality_score)
            multipliers["data_quality"] = quality_multiplier
        else:
            multipliers["data_quality"] = 1.0

        # Performance multipliers
        if performance_data:
            # Uptime multiplier
            uptime = performance_data.get("uptime", 1.0)
            multipliers["uptime"] = self._get_uptime_multiplier(uptime)

            # Latency multiplier
            latency = performance_data.get("latency", 1000)
            multipliers["latency"] = self._get_latency_multiplier(latency)

            # Verification multiplier
            verified_ratio = performance_data.get("verified_ratio", 0.0)
            multipliers["verification"] = self._get_verification_multiplier(verified_ratio)
        else:
            multipliers["uptime"] = 1.0
            multipliers["latency"] = 1.0
            multipliers["verification"] = 1.0

        # Calculate final reward
        final_reward = base_reward

        for multiplier in multipliers.values():
            final_reward *= multiplier

        # Apply bounds
        final_reward = max(
            self.config["min_reward"],
            min(self.config["max_reward"], final_reward)
        )

        calculation = RewardCalculation(
            device_id=device_id,
            metric_count=metric_count,
            base_reward=base_reward,
            multipliers=multipliers,
            final_reward=final_reward,
            calculated_at=datetime.utcnow().isoformat()
        )

        # Store calculation
        self._store_reward_calculation(calculation)

        logger.info(f"Calculated reward for device {device_id}: {final_reward:.2f} tokens")
        return calculation

    def _calculate_data_quality(self, metrics: List[Dict]) -> float:
        """Calculate data quality score (0-1)"""
        if not metrics:
            return 0.0

        quality_factors = []

        # Verified ratio
        verified_count = sum(1 for m in metrics if m.get('is_verified', False))
        verified_ratio = verified_count / len(metrics)
        quality_factors.append(verified_ratio)

        # Consistency (low variance)
        values = [m.get('value', 0) for m in metrics if 'value' in m]
        if values:
            variance = np.var(values)
            # Lower variance is better (normalize to 0-1)
            consistency = max(0, 1 - (variance / 1000))
            quality_factors.append(consistency)

        # Recent data (not stale)
        now = int(datetime.utcnow().timestamp())
        recent_count = sum(1 for m in metrics
                          if m.get('timestamp', 0) > now - 3600)
        recency = recent_count / len(metrics)
        quality_factors.append(recency)

        # Average quality score
        return np.mean(quality_factors)

    def _get_quality_multiplier(self, score: float) -> float:
        """Get multiplier based on data quality score"""
        if score >= 0.8:
            return self.config["multipliers"]["data_quality"]["excellent"]
        elif score >= 0.6:
            return self.config["multipliers"]["data_quality"]["good"]
        elif score >= 0.4:
            return self.config["multipliers"]["data_quality"]["average"]
        else:
            return self.config["multipliers"]["data_quality"]["poor"]

    def _get_uptime_multiplier(self, uptime: float) -> float:
        """Get multiplier based on uptime (0-1)"""
        if uptime >= 0.95:
            return self.config["multipliers"]["uptime"]["high"]
        elif uptime >= 0.90:
            return self.config["multipliers"]["uptime"]["medium"]
        else:
            return self.config["multipliers"]["uptime"]["low"]

    def _get_latency_multiplier(self, latency_ms: int) -> float:
        """Get multiplier based on latency in milliseconds"""
        if latency_ms < 100:
            return self.config["multipliers"]["latency"]["low"]
        elif latency_ms < 500:
            return self.config["multipliers"]["latency"]["medium"]
        else:
            return self.config["multipliers"]["latency"]["high"]

    def _get_verification_multiplier(self, ratio: float) -> float:
        """Get multiplier based on verification ratio"""
        if ratio >= 0.8:
            return self.config["multipliers"]["verification"]["verified"]
        else:
            return self.config["multipliers"]["verification"]["unverified"]

    def apply_penalty(self, device_id: int, violation_type: str) -> float:
        """
        Apply penalty to a device

        Args:
            device_id: Device ID
            violation_type: Type of violation

        Returns:
            Penalty amount (negative value)
        """
        penalty_percentage = self.config["penalties"].get(violation_type, 0)

        if penalty_percentage == 0:
            logger.warning(f"Unknown violation type: {violation_type}")
            return 0

        # Get recent rewards for device
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT final_reward
            FROM rewards
            WHERE device_id = ?
            ORDER BY calculated_at DESC
            LIMIT 10
        """, (device_id,))

        recent_rewards = [row[0] for row in cursor.fetchall()]

        if recent_rewards:
            avg_reward = np.mean(recent_rewards)
            penalty_amount = avg_reward * penalty_percentage
        else:
            penalty_amount = 100 * abs(penalty_percentage)  # Default base

        conn.close()

        logger.info(f"Applied penalty to device {device_id}: {penalty_amount:.2f} tokens ({violation_type})")
        return penalty_amount

    def distribute_rewards(self, device_id: int, reward_amount: float,
                          reward_type: str = "metrics", tx_hash: Optional[str] = None):
        """
        Record reward distribution

        Args:
            device_id: Device ID
            reward_amount: Amount to distribute
            reward_type: Type of reward
            tx_hash: Transaction hash (optional)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO reward_history (device_id, reward_amount, reward_type, tx_hash)
            VALUES (?, ?, ?, ?)
        """, (device_id, reward_amount, reward_type, tx_hash))

        conn.commit()
        conn.close()

        logger.info(f"Distributed {reward_amount:.2f} tokens to device {device_id}")

    def get_total_rewards(self, device_id: int, days: int = 30) -> float:
        """
        Get total rewards for a device over specified period

        Args:
            device_id: Device ID
            days: Number of days to look back

        Returns:
            Total reward amount
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_time = int((datetime.utcnow() - timedelta(days=days)).timestamp())

        cursor.execute("""
            SELECT COALESCE(SUM(reward_amount), 0)
            FROM reward_history
            WHERE device_id = ?
                AND distributed_at >= datetime(?, 'unixepoch')
        """, (device_id, cutoff_time))

        total = cursor.fetchone()[0]
        conn.close()

        return float(total)

    def _store_reward_calculation(self, calculation: RewardCalculation):
        """Store reward calculation in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO rewards
            (device_id, metric_count, base_reward, multipliers, penalties, final_reward)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            calculation.device_id,
            calculation.metric_count,
            calculation.base_reward,
            json.dumps(calculation.multipliers),
            0,  # No penalties in calculation
            calculation.final_reward
        ))

        conn.commit()
        conn.close()

    def get_reward_leaderboard(self, limit: int = 10) -> List[Dict]:
        """
        Get leaderboard of top rewarded devices

        Args:
            limit: Maximum number of devices to return

        Returns:
            List of device dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                device_id,
                SUM(reward_amount) as total_rewards,
                COUNT(*) as reward_count
            FROM reward_history
            WHERE distributed_at >= datetime('now', '-30 days')
            GROUP BY device_id
            ORDER BY total_rewards DESC
            LIMIT ?
        """, (limit,))

        leaderboard = []
        for row in cursor.fetchall():
            leaderboard.append({
                "device_id": row[0],
                "total_rewards": row[1],
                "reward_count": row[2]
            })

        conn.close()
        return leaderboard


if __name__ == "__main__":
    print("Testing Reward System...")

    # Create sample metrics
    sample_metrics = [
        {"value": 25.5, "data_type": "temperature", "is_verified": True, "timestamp": int(datetime.utcnow().timestamp())},
        {"value": 26.2, "data_type": "temperature", "is_verified": True, "timestamp": int(datetime.utcnow().timestamp())},
        {"value": 60.0, "data_type": "humidity", "is_verified": True, "timestamp": int(datetime.utcnow().timestamp())},
        {"value": 24.8, "data_type": "temperature", "is_verified": False, "timestamp": int(datetime.utcnow().timestamp())},
    ]

    # Create performance data
    performance_data = {
        "uptime": 0.98,
        "latency": 80,
        "verified_ratio": 0.75
    }

    # Initialize reward system
    reward_system = RewardSystem()

    # Calculate rewards
    calculation = reward_system.calculate_rewards(
        device_id=1,
        metrics=sample_metrics,
        performance_data=performance_data
    )

    print(f"\nReward Calculation:")
    print(f"  Device ID: {calculation.device_id}")
    print(f"  Metric Count: {calculation.metric_count}")
    print(f"  Base Reward: {calculation.base_reward:.2f}")
    print(f"  Multipliers: {calculation.multipliers}")
    print(f"  Final Reward: {calculation.final_reward:.2f}")

    # Test penalty
    penalty = reward_system.apply_penalty(device_id=1, violation_type="offline")
    print(f"\nPenalty Applied: {penalty:.2f} tokens")

    # Get leaderboard
    leaderboard = reward_system.get_reward_leaderboard(limit=5)
    print(f"\nLeaderboard: {leaderboard}")

    print("\n✅ Reward System test complete!")
