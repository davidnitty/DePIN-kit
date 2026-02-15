const hre = require("hardhat");

async function main() {
  console.log("Deploying IoTeX DePIN Kit Contracts...\n");

  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);
  console.log("Account balance:", (await hre.ethers.provider.getBalance(deployer.address)).toString(), "\n");

  // Deploy DePINManager
  console.log("1. Deploying DePINManager...");
  const DePINManager = await hre.ethers.getContractFactory("DePINManager");
  const depinManager = await DePINManager.deploy();
  await depinManager.waitForDeployment();
  const depinManagerAddress = await depinManager.getAddress();
  console.log("   DePINManager deployed to:", depinManagerAddress);

  // Deploy RewardDistribution
  console.log("\n2. Deploying RewardDistribution...");
  const RewardDistribution = await hre.ethers.getContractFactory("RewardDistribution");
  const rewardDistribution = await RewardDistribution.deploy(depinManagerAddress);
  await rewardDistribution.waitForDeployment();
  const rewardDistributionAddress = await rewardDistribution.getAddress();
  console.log("   RewardDistribution deployed to:", rewardDistributionAddress);

  // Verify deployment
  console.log("\n✅ Deployment Complete!");
  console.log("\nContract Addresses:");
  console.log("- DePINManager:", depinManagerAddress);
  console.log("- RewardDistribution:", rewardDistributionAddress);

  // Save deployment info
  const deploymentInfo = {
    network: hre.network.name,
    chainId: (await hre.ethers.provider.getNetwork()).chainId.toString(),
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    contracts: {
      DePINManager: depinManagerAddress,
      RewardDistribution: rewardDistributionAddress
    }
  };

  const fs = require("fs");
  fs.writeFileSync(
    "./deployment.json",
    JSON.stringify(deploymentInfo, null, 2)
  );
  console.log("\nDeployment info saved to deployment.json");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
