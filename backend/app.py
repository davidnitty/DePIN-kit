"""
Flask API for IoTeX DePIN Kit
REST API for interacting with DePIN smart contracts and services
"""

import os
import sys
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JSON_SORT_KEYS'] = False


# Import modules
try:
    from contract_interface import ContractInterface
    from iotex_depink import IoTeXDePIN
    from ai_model import PredictiveMaintenanceModel, AnomalyDetectionModel
    from data_processor import DataProcessor, DataValidator
    from reward_system import RewardSystem

    # Initialize services
    contract = ContractInterface()
    depin = IoTeXDePIN()
    data_processor = DataProcessor()
    reward_system = RewardSystem()

    logger.info("✅ All services initialized successfully")
except Exception as e:
    logger.error(f"❌ Error initializing services: {e}")
    contract = None
    depin = None
    data_processor = None
    reward_system = None


# Error handlers
@app.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({"error": "Bad Request", "message": str(error)}), 400


@app.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    return jsonify({"error": "Not Found", "message": str(error)}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500


# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "contract": contract is not None,
            "depin": depin is not None,
            "data_processor": data_processor is not None,
            "reward_system": reward_system is not None
        }
    })


# Device endpoints
@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get all registered devices"""
    try:
        if not depin:
            return jsonify({"error": "DePIN service not available"}), 503

        devices = depin.get_all_devices()

        return jsonify({
            "success": True,
            "count": len(devices),
            "devices": [
            {
                "device_id": d.device_id,
                "owner": d.owner_address,
                "type": d.device_type,
                "status": d.status,
                "metadata_uri": d.metadata_uri
            }
            for d in devices
        ]
        })
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    """Get device information"""
    try:
        if not depin:
            return jsonify({"error": "DePIN service not available"}), 503

        device = depin.get_device(device_id)

        if not device:
            return jsonify({"error": "Device not found"}), 404

        return jsonify({
            "success": True,
            "device": {
                "device_id": device.device_id,
                "owner": device.owner_address,
                "type": device.device_type,
                "status": device.status,
                "metadata_uri": device.metadata_uri,
                "location": device.location,
                "specifications": device.specifications
            }
        })
    except Exception as e:
        logger.error(f"Error getting device: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/devices', methods=['POST'])
def register_device():
    """Register a new device"""
    try:
        if not depin:
            return jsonify({"error": "DePIN service not available"}), 503

        data = request.get_json()

        # Validate required fields
        required_fields = ['owner_address', 'metadata', 'device_type']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Register device
        device = depin.onboard_depin(
            owner_address=data['owner_address'],
            metadata=data['metadata'],
            device_type=data['device_type'],
            location=data.get('location')
        )

        return jsonify({
            "success": True,
            "device_id": device.device_id,
            "status": device.status,
            "message": "Device registered successfully"
        }), 201

    except Exception as e:
        logger.error(f"Error registering device: {e}")
        return jsonify({"error": str(e)}), 500


# Metrics endpoints
@app.route('/api/devices/<int:device_id>/metrics', methods=['POST'])
def submit_metrics(device_id):
    """Submit metrics for a device"""
    try:
        if not depin:
            return jsonify({"error": "DePIN service not available"}), 503

        data = request.get_json()

        if 'metrics' not in data:
            return jsonify({"error": "Missing metrics field"}), 400

        # Validate data
        valid_data, invalid_data = DataValidator.validate_batch(data['metrics'])

        if invalid_data:
            logger.warning(f"Rejected {len(invalid_data)} invalid metrics")

        # Process valid data
        if valid_data:
            processed = depin.process_data(device_id, valid_data)

            # Store in database
            data_processor.store_metrics(device_id, processed)

            return jsonify({
                "success": True,
                "processed": len(processed),
                "rejected": len(invalid_data),
                "message": f"Processed {len(processed)} metrics"
            })
        else:
            return jsonify({"error": "No valid metrics provided"}), 400

    except Exception as e:
        logger.error(f"Error submitting metrics: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/devices/<int:device_id>/metrics', methods=['GET'])
def get_metrics(device_id):
    """Get metrics for a device"""
    try:
        if not data_processor:
            return jsonify({"error": "Data processor not available"}), 503

        # Get query parameters
        data_type = request.args.get('data_type')
        limit = request.args.get('limit', type=int)

        metrics = data_processor.get_metrics(device_id, data_type=data_type, limit=limit)

        return jsonify({
            "success": True,
            "device_id": device_id,
            "count": len(metrics),
            "metrics": metrics
        })
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({"error": str(e)}), 500


# Statistics endpoints
@app.route('/api/devices/<int:device_id>/stats', methods=['GET'])
def get_device_stats(device_id):
    """Get statistics for a device"""
    try:
        if not data_processor:
            return jsonify({"error": "Data processor not available"}), 503

        stats = data_processor.get_device_statistics(device_id)

        return jsonify({
            "success": True,
            "statistics": stats
        })
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/devices/<int:device_id>/stats/aggregate', methods=['GET'])
def get_aggregate_stats(device_id):
    """Get aggregated statistics for a device"""
    try:
        if not data_processor:
            return jsonify({"error": "Data processor not available"}), 503

        data_type = request.args.get('data_type', 'temperature')
        period = request.args.get('period', 'hour')

        aggregated = data_processor.aggregate_data(device_id, data_type, period)

        if not aggregated:
            return jsonify({"error": "No data found for aggregation"}), 404

        return jsonify({
            "success": True,
            "aggregated": aggregated
        })
    except Exception as e:
        logger.error(f"Error getting aggregated stats: {e}")
        return jsonify({"error": str(e)}), 500


# AI/ML endpoints
@app.route('/api/devices/<int:device_id>/predict', methods=['POST'])
def predict_maintenance(device_id):
    """Predict maintenance needs for a device"""
    try:
        # Import AI model
        from ai_model import PredictiveMaintenanceModel

        data = request.get_json()

        if 'data' not in data:
            return jsonify({"error": "Missing data field"}), 400

        # Load model
        model_path = Path(__file__).parent / "models" / "predictive_maintenance"

        if not model_path.exists():
            return jsonify({"error": "Predictive model not available"}), 503

        model = PredictiveMaintenanceModel(str(model_path))

        # Make predictions
        import pandas as pd
        df = pd.DataFrame(data['data'])
        predictions = model.predict(df)

        return jsonify({
            "success": True,
            "predictions": predictions.tolist(),
            "average_failure_probability": float(np.mean(predictions))
        })
    except Exception as e:
        logger.error(f"Error predicting maintenance: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/devices/<int:device_id>/anomalies', methods=['POST'])
def detect_anomalies(device_id):
    """Detect anomalies in device metrics"""
    try:
        from ai_model import AnomalyDetectionModel

        data = request.get_json()

        if 'data' not in data:
            return jsonify({"error": "Missing data field"}), 400

        # Load model
        model_path = Path(__file__).parent / "models" / "anomaly_detection"

        if not model_path.exists():
            return jsonify({"error": "Anomaly detection model not available"}), 503

        model = AnomalyDetectionModel(str(model_path))

        # Detect anomalies
        import pandas as pd
        df = pd.DataFrame(data['data'])
        anomalies, errors = model.detect_anomalies(df)

        return jsonify({
            "success": True,
            "anomalies": anomalies.tolist(),
            "anomaly_count": int(np.sum(anomalies)),
            "reconstruction_errors": errors.tolist()
        })
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        return jsonify({"error": str(e)}), 500


# Reward endpoints
@app.route('/api/rewards/calculate', methods=['POST'])
def calculate_rewards():
    """Calculate rewards for a device"""
    try:
        if not reward_system:
            return jsonify({"error": "Reward system not available"}), 503

        data = request.get_json()

        if 'device_id' not in data:
            return jsonify({"error": "Missing device_id field"}), 400

        metrics = data.get('metrics', [])
        performance_data = data.get('performance_data')

        calculation = reward_system.calculate_rewards(
            device_id=data['device_id'],
            metrics=metrics,
            performance_data=performance_data
        )

        return jsonify({
            "success": True,
            "calculation": {
                "device_id": calculation.device_id,
                "metric_count": calculation.metric_count,
                "base_reward": calculation.base_reward,
                "multipliers": calculation.multipliers,
                "final_reward": calculation.final_reward,
                "calculated_at": calculation.calculated_at
            }
        })
    except Exception as e:
        logger.error(f"Error calculating rewards: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/rewards/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get reward leaderboard"""
    try:
        if not reward_system:
            return jsonify({"error": "Reward system not available"}), 503

        limit = request.args.get('limit', 10, type=int)
        leaderboard = reward_system.get_reward_leaderboard(limit=limit)

        return jsonify({
            "success": True,
            "leaderboard": leaderboard
        })
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return jsonify({"error": str(e)}), 500


# Blockchain endpoints
@app.route('/api/blockchain/stats', methods=['GET'])
def get_blockchain_stats():
    """Get blockchain statistics"""
    try:
        if not contract:
            return jsonify({"error": "Contract interface not available"}), 503

        total_devices = contract.get_total_devices()
        pool_stats = contract.get_pool_stats()

        return jsonify({
            "success": True,
            "blockchain": {
                "total_devices": total_devices,
                "reward_pool": pool_stats
            }
        })
    except Exception as e:
        logger.error(f"Error getting blockchain stats: {e}")
        return jsonify({"error": str(e)}), 500


# Root endpoint
@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        "name": "IoTeX DePIN Kit API",
        "version": "1.0.0",
        "description": "REST API for IoTeX DePIN integration",
        "endpoints": {
            "health": "GET /api/health",
            "devices": {
                "list": "GET /api/devices",
                "get": "GET /api/devices/<device_id>",
                "register": "POST /api/devices"
            },
            "metrics": {
                "submit": "POST /api/devices/<device_id>/metrics",
                "get": "GET /api/devices/<device_id>/metrics"
            },
            "statistics": {
                "device": "GET /api/devices/<device_id>/stats",
                "aggregate": "GET /api/devices/<device_id>/stats/aggregate"
            },
            "ai": {
                "predict": "POST /api/devices/<device_id>/predict",
                "anomalies": "POST /api/devices/<device_id>/anomalies"
            },
            "rewards": {
                "calculate": "POST /api/rewards/calculate",
                "leaderboard": "GET /api/rewards/leaderboard"
            },
            "blockchain": {
                "stats": "GET /api/blockchain/stats"
            }
        }
    })


def main():
    """Run the Flask application"""
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'

    logger.info(f"Starting IoTeX DePIN Kit API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()
