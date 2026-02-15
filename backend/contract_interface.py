"""
Smart Contract Interface
Interacts with deployed IoTeX DePIN smart contracts using Web3.py
"""

import os
import json
from web3 import Web3
from web3.middleware import geth_poa
from eth_account import Account
from pathlib import Path


class ContractInterface:
    """
    Interface for interacting with IoTeX DePIN smart contracts
    """

    def __init__(self, config_path=None):
        """
        Initialize the contract interface

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.w3 = self._connect_web3()
        self.accounts = self._load_accounts()
        self.contracts = self._load_contracts()

    def _load_config(self, config_path):
        """Load configuration from file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "contracts" / "deployment.json"

        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Return default configuration
            return {
                "contracts": {
                    "DePINManager": os.getenv("DEPIN_MANAGER_ADDRESS", ""),
                    "RewardDistribution": os.getenv("REWARD_DISTRIBUTION_ADDRESS", "")
                }
            }

    def _connect_web3(self):
        """Connect to IoTeX blockchain"""
        network_url = os.getenv(
            "IOTEX_TESTNET_RPC_URL",
            "https://graphql.testnet.iotex.io"
        )

        w3 = Web3(Web3.HTTPProvider(network_url))

        # Add middleware for POA chains
        w3.middleware_onion.inject(geth_poa.geth_poa_middleware, layer=0)

        if w3.is_connected():
            print(f"Connected to IoTeX network at {network_url}")
            return w3
        else:
            raise ConnectionError("Failed to connect to IoTeX network")

    def _load_accounts(self):
        """Load Ethereum account from private key"""
        private_key = os.getenv("PRIVATE_KEY")
        if private_key:
            account = Account.from_key(private_key)
            print(f"Loaded account: {account.address}")
            return {"default": account}
        else:
            print("Warning: No private key found in environment")
            return {}

    def _load_contracts(self):
        """Load smart contract ABIs and addresses"""
        contracts = {}

        # Load ABIs from build artifacts
        build_path = Path(__file__).parent.parent / "contracts" / "artifacts"

        contract_names = ["DePINManager", "RewardDistribution"]

        for contract_name in contract_names:
            abi_path = build_path / f"{contract_name}.sol" / f"{contract_name}.json"

            if abi_path.exists():
                with open(abi_path, 'r') as f:
                    artifact = json.load(f)
                    abi = artifact["abi"]

                address = self.config["contracts"].get(contract_name, "")

                if address and Web3.is_address(address):
                    contract = self.w3.eth.contract(
                        address=Web3.to_checksum_address(address),
                        abi=abi
                    )
                    contracts[contract_name] = contract
                    print(f"Loaded contract: {contract_name} at {address}")
                else:
                    print(f"Warning: No valid address for {contract_name}")
            else:
                print(f"Warning: ABI not found for {contract_name}")

        return contracts

    def register_device(self, metadata_uri, account_key="default"):
        """
        Register a new device on the blockchain

        Args:
            metadata_uri: IPFS hash of device metadata
            account_key: Key for the account to use

        Returns:
            Transaction receipt
        """
        if "DePINManager" not in self.contracts:
            raise ValueError("DePINManager contract not loaded")

        if account_key not in self.accounts:
            raise ValueError(f"Account '{account_key}' not found")

        account = self.accounts[account_key]
        contract = self.contracts["DePINManager"]

        # Build transaction
        transaction = contract.functions.registerDevice(
            metadata_uri
        ).build_transaction({
            'from': account.address,
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(account.address),
        })

        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # Wait for transaction receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt['status'] == 1:
            print(f"Device registered successfully. Transaction hash: {tx_hash.hex()}")
            return receipt
        else:
            raise Exception(f"Transaction failed: {tx_hash.hex()}")

    def report_metrics(self, device_id, value, data_type, account_key="default"):
        """
        Report metrics for a device

        Args:
            device_id: Device ID
            value: Metric value
            data_type: Type of data (e.g., "temperature", "humidity")
            account_key: Key for the account to use

        Returns:
            Transaction receipt
        """
        if "DePINManager" not in self.contracts:
            raise ValueError("DePINManager contract not loaded")

        if account_key not in self.accounts:
            raise ValueError(f"Account '{account_key}' not found")

        account = self.accounts[account_key]
        contract = self.contracts["DePINManager"]

        # Build transaction
        transaction = contract.functions.reportMetrics(
            device_id,
            value,
            data_type
        ).build_transaction({
            'from': account.address,
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(account.address),
        })

        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(transaction, account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # Wait for transaction receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt['status'] == 1:
            print(f"Metrics reported successfully. Transaction hash: {tx_hash.hex()}")
            return receipt
        else:
            raise Exception(f"Transaction failed: {tx_hash.hex()}")

    def get_device_info(self, device_id):
        """
        Get information about a device

        Args:
            device_id: Device ID

        Returns:
            Device information dictionary
        """
        if "DePINManager" not in self.contracts:
            raise ValueError("DePINManager contract not loaded")

        contract = self.contracts["DePINManager"]

        device_info = contract.functions.getDeviceInfo(device_id).call()

        return {
            'id': device_info[0],
            'owner': device_info[1],
            'metadataURI': device_info[2],
            'status': device_info[3],
            'totalRewards': device_info[4],
            'registrationTime': device_info[5],
            'lastReportTime': device_info[6],
        }

    def get_metrics(self, device_id):
        """
        Get metrics for a device

        Args:
            device_id: Device ID

        Returns:
            List of metric dictionaries
        """
        if "DePINManager" not in self.contracts:
            raise ValueError("DePINManager contract not loaded")

        contract = self.contracts["DePINManager"]

        metrics = contract.functions.getMetrics(device_id).call()

        return [
            {
                'deviceId': metric[0],
                'timestamp': metric[1],
                'value': metric[2],
                'dataType': metric[3],
                'isVerified': metric[4],
            }
            for metric in metrics
        ]

    def get_total_devices(self):
        """
        Get total number of devices

        Returns:
            Total device count
        """
        if "DePINManager" not in self.contracts:
            raise ValueError("DePINManager contract not loaded")

        contract = self.contracts["DePINManager"]
        return contract.functions.getTotalDevices().call()

    def get_pool_stats(self):
        """
        Get reward pool statistics

        Returns:
            Dictionary with pool statistics
        """
        if "RewardDistribution" not in self.contracts:
            raise ValueError("RewardDistribution contract not loaded")

        contract = self.contracts["RewardDistribution"]

        stats = contract.functions.getPoolStats().call()

        return {
            'totalPool': stats[0],
            'staked': stats[1],
            'distributed': stats[2],
            'available': stats[3],
        }


if __name__ == "__main__":
    # Example usage
    print("Testing ContractInterface...")

    try:
        ci = ContractInterface()

        # Get total devices
        total = ci.get_total_devices()
        print(f"Total devices: {total}")

        # Get pool stats
        stats = ci.get_pool_stats()
        print(f"Pool stats: {stats}")

    except Exception as e:
        print(f"Error: {e}")
