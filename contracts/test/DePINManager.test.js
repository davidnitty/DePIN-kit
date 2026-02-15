const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("DePINManager", function () {
  let depinManager;
  let owner;
  let addr1;
  let addr2;

  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();

    const DePINManager = await ethers.getContractFactory("DePINManager");
    depinManager = await DePINManager.deploy();
    await depinManager.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await depinManager.owner()).to.equal(owner.address);
    });

    it("Should start with zero devices", async function () {
      expect(await depinManager.getTotalDevices()).to.equal(0);
    });
  });

  describe("Device Registration", function () {
    it("Should register a new device", async function () {
      const metadataURI = "ipfs://QmTest123";

      const tx = await depinManager.connect(addr1).registerDevice(metadataURI);
      const receipt = await tx.wait();

      const deviceId = 1;
      const device = await depinManager.getDeviceInfo(deviceId);

      expect(device.owner).to.equal(addr1.address);
      expect(device.metadataURI).to.equal(metadataURI);
      expect(await depinManager.getTotalDevices()).to.equal(1);
    });

    it("Should emit DeviceRegistered event", async function () {
      const metadataURI = "ipfs://QmTest123";

      await expect(depinManager.connect(addr1).registerDevice(metadataURI))
        .to.emit(depinManager, "DeviceRegistered")
        .withArgs(1, addr1.address, metadataURI, await ethers.provider.getBlock('latest').then(b => b.timestamp + 1));
    });

    it("Should track devices by owner", async function () {
      await depinManager.connect(addr1).registerDevice("ipfs://QmTest1");
      await depinManager.connect(addr1).registerDevice("ipfs://QmTest2");
      await depinManager.connect(addr2).registerDevice("ipfs://QmTest3");

      const addr1Devices = await depinManager.getDevicesByOwner(addr1.address);
      const addr2Devices = await depinManager.getDevicesByOwner(addr2.address);

      expect(addr1Devices.length).to.equal(2);
      expect(addr2Devices.length).to.equal(1);
    });
  });

  describe("Metrics Reporting", function () {
    let deviceId;

    beforeEach(async function () {
      const tx = await depinManager.connect(addr1).registerDevice("ipfs://QmTest123");
      deviceId = 1;
    });

    it("Should report metrics for a device", async function () {
      const value = 250;
      const dataType = "temperature";

      await depinManager.connect(addr1).reportMetrics(deviceId, value, dataType);

      const metrics = await depinManager.getMetrics(deviceId);
      expect(metrics.length).to.equal(1);
      expect(metrics[0].value).to.equal(value);
      expect(metrics[0].dataType).to.equal(dataType);
    });

    it("Should only allow device owner to report metrics", async function () {
      await expect(
        depinManager.connect(addr2).reportMetrics(deviceId, 250, "temperature")
      ).to.be.revertedWith("Not device owner");
    });

    it("Should emit MetricsReported event", async function () {
      await expect(depinManager.connect(addr1).reportMetrics(deviceId, 250, "temperature"))
        .to.emit(depinManager, "MetricsReported");
    });
  });

  describe("Pausing", function () {
    it("Should pause and unpause", async function () {
      await depinManager.pause();
      expect(await depinManager.paused()).to.equal(true);

      await depinManager.unpause();
      expect(await depinManager.paused()).to.equal(false);
    });

    it("Should prevent registration when paused", async function () {
      await depinManager.pause();

      await expect(
        depinManager.connect(addr1).registerDevice("ipfs://QmTest123")
      ).to.be.revertedWithCustomError(depinManager, "EnforcedPause");
    });
  });
});
