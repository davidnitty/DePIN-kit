require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    hardhat: {
      chainId: 4690
    },
    iotexTestnet: {
      url: process.env.IOTEX_TESTNET_RPC_URL || "https://graphql.testnet.iotex.io",
      chainId: 4690,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    },
    iotexMainnet: {
      url: process.env.IOTEX_MAINNET_RPC_URL || "https://graphql.iotex.io",
      chainId: 4689,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    }
  },
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  },
  etherscan: {
    apiKey: {
      iotex: process.env.IOTEXSCAN_API_KEY || ""
    }
  }
};
