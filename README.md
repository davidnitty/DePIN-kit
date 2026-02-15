# IoTeX DePIN Kit

**AI-Powered Development for Decentralized Physical Infrastructure Networks**

## 📋 Overview

The IoTeX DePIN Kit is a comprehensive platform for building and managing decentralized physical infrastructure networks (DePIN) on the IoTeX blockchain. It combines smart contracts, AI/ML capabilities, and a modern web interface to create a powerful development toolkit.

## 🏗️ Architecture

```
iotex-depin-kit/
├── contracts/           # Solidity smart contracts
│   ├── DePINManager.sol
│   ├── RewardDistribution.sol
│   └── scripts/
├── backend/            # Python Flask API
│   ├── contract_interface.py
│   ├── ai_model.py
│   ├── iotex_depink.py
│   ├── data_processor.py
│   ├── reward_system.py
│   └── app.py
└── frontend/           # React application
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   └── services/
    └── public/
```

## ✨ Features

- **Smart Contract Management**: Deploy and interact with IoTeX DePIN smart contracts
- **AI-Powered Analytics**: Predictive maintenance and anomaly detection for device metrics
- **Reward Distribution**: Automated reward calculation and distribution system
- **Data Processing**: Clean, aggregate, and analyze device metrics
- **Modern UI**: React-based dashboard for monitoring and management

## 🚀 Getting Started

### Prerequisites

- Node.js >= 18
- Python >= 3.9
- Hardhat
- IoTeX Wallet (testnet or mainnet)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-username/iotex-depin-kit.git
cd iotex-depin-kit
```

2. **Install Smart Contract Dependencies**
```bash
cd contracts
npm install
```

3. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your private key and RPC URLs
```

4. **Compile and Deploy Contracts**
```bash
npm run compile
npm run deploy:testnet
```

5. **Install Backend Dependencies**
```bash
cd ../backend
pip install -r requirements.txt
```

6. **Configure Backend**
```bash
cp .env.example .env
# Add deployed contract addresses to .env
```

7. **Install Frontend Dependencies**
```bash
cd ../frontend
npm install
```

8. **Run the Application**

   Terminal 1 (Backend):
```bash
cd backend
python app.py
```

   Terminal 2 (Frontend):
```bash
cd frontend
npm start
```

9. **Access the Dashboard**
Open http://localhost:3000 in your browser

## 📚 Documentation

### Smart Contracts

- **DePINManager.sol**: Main registry for managing devices
  - `registerDevice(metadataURI)`: Register a new device
  - `reportMetrics(deviceId, value, dataType)`: Report metrics
  - `getDeviceInfo(deviceId)`: Get device information

- **RewardDistribution.sol**: Manage rewards and penalties
  - `distributeRewards(deviceId, metricCount)`: Distribute rewards
  - `slashDevice(deviceId, violationType, slashPercentage)`: Slash device rewards

### Backend API

**Device Endpoints**
- `GET /api/devices` - List all devices
- `GET /api/devices/<id>` - Get device details
- `POST /api/devices` - Register new device

**Metrics Endpoints**
- `POST /api/devices/<id>/metrics` - Submit metrics
- `GET /api/devices/<id>/metrics` - Get device metrics

**AI/ML Endpoints**
- `POST /api/devices/<id>/predict` - Predict maintenance needs
- `POST /api/devices/<id>/anomalies` - Detect anomalies

**Reward Endpoints**
- `POST /api/rewards/calculate` - Calculate rewards
- `GET /api/rewards/leaderboard` - Get leaderboard

### Frontend Components

- **Dashboard**: Network overview and statistics
- **Devices**: Device management interface
- **Analytics**: Data visualization and insights
- **Profile**: User settings and wallet connection

## 🔧 Development

### Running Tests

**Smart Contracts**
```bash
cd contracts
npm test
```

**Backend**
```bash
cd backend
pytest
```

**Frontend**
```bash
cd frontend
npm test
```

### Building for Production

**Frontend**
```bash
cd frontend
npm run build
```

## 🌐 Deployment

### Smart Contracts

Deploy to IoTeX testnet:
```bash
cd contracts
npm run deploy:testnet
```

Deploy to IoTeX mainnet:
```bash
npm run deploy:mainnet
```

### Backend

Use a production WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Frontend

Build and serve static files:
```bash
npm run build
# Serve the build/ directory with nginx or similar
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🔗 Links

- [IoTeX Documentation](https://docs.iotex.io/)
- [IoTeX Explorer](https://iotexscan.io/)
- [Hardhat Documentation](https://hardhat.org/)

## 🙏 Acknowledgments

Built with:
- IoTeX Blockchain
- Ethereum Smart Contracts
- TensorFlow/Keras
- Flask
- React
