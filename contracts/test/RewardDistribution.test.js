const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("RewardDistribution", function () {
  let rewardDistribution;
  let depinManager;
  let owner;
  let addr1;
  let addr2;

  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();

    // Deploy DePINManager first
    const DePINManager = await ethers.getContractFactory("DePINManager");
    depinManager = await DePINManager.deploy();
    await depinManager.waitForDeployment();

    // Deploy RewardDistribution
    const RewardDistribution = await ethers.getContractFactory("RewardDistribution");
    rewardDistribution = await RewardDistribution.deploy(await depinManager.getAddress());
    await rewardDistribution.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should set the correct depinManager address", async function () {
      expect(await rewardDistribution.depinManager()).to.equal(await depinManager.getAddress());
    });
  });

  describe("Staking Rewards", function () {
    it("Should allow staking rewards", async function () {
      const stakeAmount = ethers.parseEther("1000");

      await expect(
        rewardDistribution.connect(owner).stakeRewards(stakeAmount, { value: stakeAmount })
      ).to.emit(rewardDistribution, "RewardsStaked");

      const stats = await rewardDistribution.getPoolStats();
      expect(stats.staked).to.equal(stakeAmount);
    });

    it("Should enforce minimum stake amount", async function () {
      const stakeAmount = ethers.parseEther("100"); // Below minimum

      await expect(
        rewardDistribution.connect(owner).stakeRewards(stakeAmount, { value: stakeAmount })
      ).to.be.reverted;
    });
  });

  describe("Distributing Rewards", function () {
    let deviceId;
    const stakeAmount = ethers.parseEther("10000");

    beforeEach(async function () {
      await rewardDistribution.connect(owner).stakeRewards(stakeAmount, { value: stakeAmount });

      await depinManager.connect(addr1).registerDevice("ipfs://QmTest123");
      deviceId = 1;
    });

    it("Should distribute rewards to a device", async function () {
      const metricCount = 5;

      await rewardDistribution.connect(owner).distributeRewards(deviceId, metricCount);

      const device = await depinManager.getDeviceInfo(deviceId);
      expect(device.totalRewards).to.be.gt(0);
    });

    it("Should mark device as able to claim", async function () {
      await rewardDistribution.connect(owner).distributeRewards(deviceId, 5);

      expect(await rewardDistribution.checkClaimable(deviceId)).to.equal(true);
    });
  });

  describe("Slashing", function () {
    let deviceId;

    beforeEach(async function () {
      const stakeAmount = ethers.parseEther("10000");
      await rewardDistribution.connect(owner).stakeRewards(stakeAmount, { value: stakeAmount });

      await depinManager.connect(addr1).registerDevice("ipfs://QmTest123");
      deviceId = 1;

      await rewardDistribution.connect(owner).distributeRewards(deviceId, 10);
    });

    it("Should slash device for violations", async function () {
      const violationType = 1; // Offline
      const slashPercentage = 10;

      await expect(
        rewardDistribution.connect(owner).slashDevice(deviceId, violationType, slashPercentage)
      ).to.emit(rewardDistribution, "DeviceSlashed");

      expect(await rewardDistribution.checkClaimable(deviceId)).to.equal(false);
    });

    it("Should track slashing history", async function () {
      await rewardDistribution.connect(owner).slashDevice(deviceId, 1, 10);

      const history = await rewardDistribution.getSlashingHistory(deviceId);
      expect(history.length).to.equal(1);
      expect(history[0].violationType).to.equal(1);
    });
  });
});
