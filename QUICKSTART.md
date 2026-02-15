# Quick Start Guide - IoTeX DePIN Kit

## 🎯 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Node.js 18+ installed
- [ ] Python 3.9+ installed
- [ ] Git installed
- [ ] IoTeX Wallet (create at https://iotex.io/wallet)
- [ ] Testnet IOTX (get from https://faucet.iotex.io/)

## 📝 Step 1: Environment Setup

### 1.1 Install Node Dependencies

```bash
cd contracts
npm install
```

### 1.2 Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 1.3 Install Frontend Dependencies

```bash
cd frontend
npm install
```

## 🔐 Step 2: Configure Environment

### 2.1 Smart Contract Configuration

```bash
cd contracts
cp .env.example .env
```

Edit `.env` and add your private key:
```env
PRIVATE_KEY=0x...  # Your wallet private key (without 0x)
IOTEX_TESTNET_RPC_URL=https://graphql.testnet.iotex.io
```

### 2.2 Backend Configuration

```bash
cd backend
cp .env.example .env
```

Add your private key and RPC URLs.

### 2.3 Frontend Configuration

```bash
cd frontend
cp .env.example .env
```

The defaults should work for local development.

## 🚀 Step 3: Deploy Smart Contracts

```bash
cd contracts
npx hardhat compile
npx hardhat run scripts/deploy.js --network iotexTestnet
```

Expected output:
```
Deploying IoTeX DePIN Kit Contracts...

Deploying contracts with account: 0x...
1. Deploying DePINManager...
   DePINManager deployed to: 0x...
2. Deploying RewardDistribution...
   RewardDistribution deployed to: 0x...

✅ Deployment Complete!
```

Copy the contract addresses and add them to your backend `.env` file.

## 🎛️ Step 4: Start the Backend

```bash
cd backend
python app.py
```

Expected output:
```
INFO - Connected to IoTeX network
INFO - Loaded account: 0x...
INFO - All services initialized successfully
 * Running on http://0.0.0.0:5000
```

Test the API:
```bash
curl http://localhost:5000/api/health
```

## 🖥️ Step 5: Start the Frontend

In a new terminal:

```bash
cd frontend
npm start
```

Expected output:
```
Compiled successfully!

You can now view iotex-depin-frontend in the browser.

  Local:            http://localhost:3000
```

## ✅ Step 6: Access the Dashboard

1. Open http://localhost:3000 in your browser
2. You should see the IoTeX DePIN Dashboard
3. Check the health status and system overview

## 📱 Step 7: Register Your First Device

You can register a device using the API:

```bash
curl -X POST http://localhost:5000/api/devices \
  -H "Content-Type: application/json" \
  -d '{
    "owner_address": "0x...",
    "metadata": {
      "name": "Temperature Sensor 1",
      "location": "San Francisco"
    },
    "device_type": "sensor"
  }'
```

Or use the Devices page in the frontend when implemented.

## 🎉 Success!

You now have a fully functional IoTeX DePIN Kit running locally!

## 🐛 Troubleshooting

### Smart Contract Deployment Fails

- Ensure you have testnet IOTX in your wallet
- Check that your private key is correct
- Verify RPC URL is accessible

### Backend Won't Start

- Check Python version (3.9+)
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Verify contract addresses in .env

### Frontend Shows Errors

- Clear browser cache
- Check that backend is running on port 5000
- Verify API URL in frontend .env

## 📚 Next Steps

1. **Explore the Dashboard**: View network statistics
2. **Register Devices**: Add your DePIN devices
3. **Submit Metrics**: Send data from your devices
4. **View Analytics**: Analyze device performance
5. **Claim Rewards**: Check and claim rewards

## 🆘 Need Help?

- Check the main README.md
- Open an issue on GitHub
- Join the IoTeX community Discord

Happy building! 🚀
