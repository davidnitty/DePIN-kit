// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./DePINManager.sol";

/**
 * @title RewardDistribution
 * @dev Manages reward distribution and slashing for IoTeX DePIN network
 * @author IoTeX DePIN Kit
 */
contract RewardDistribution is Ownable, Pausable, ReentrancyGuard {

    DePINManager public depinManager;

    // Reward Pool
    uint256 public totalRewardPool;
    uint256 public stakedRewards;
    uint256 public distributedRewards;

    // Reward Configuration
    uint256 public constant BASE_REWARD_RATE = 100 * 10**18; // 100 tokens per report
    uint256 public constant SLASHING_PERCENTAGE = 10; // 10% slash for violations
    uint256 public constant MIN_STAKE_AMOUNT = 1000 * 10**18; // Minimum stake

    // Slashing Conditions
    enum ViolationType {
        None,
        Offline,
        DataInconsistency,
        MaliciousActivity
    }

    struct SlashingEvent {
        uint256 deviceId;
        ViolationType violationType;
        uint256 amount;
        uint256 timestamp;
        bool resolved;
    }

    mapping(uint256 => SlashingEvent[]) public slashingHistory;
    mapping(uint256 => bool) public canClaim;

    uint256 private _slashingCounter;

    // Events
    event RewardsStaked(address indexed staker, uint256 amount, uint256 timestamp);
    event RewardsDistributed(uint256 indexed deviceId, uint256 amount, uint256 timestamp);
    event DeviceSlashed(uint256 indexed deviceId, uint256 amount, ViolationType violationType, uint256 timestamp);
    event RewardsClaimed(uint256 indexed deviceId, address indexed owner, uint256 amount, uint256 timestamp);
    event StakeWithdrawn(address indexed staker, uint256 amount, uint256 timestamp);

    // Modifiers
    modifier validDevice(uint256 _deviceId) {
        require(_deviceId > 0 && _deviceId <= depinManager.getTotalDevices(), "Invalid device ID");
        _;
    }

    constructor(address _depinManagerAddress) Ownable(msg.sender) {
        depinManager = DePINManager(_depinManagerAddress);
    }

    /**
     * @dev Stake rewards into the reward pool
     * @param _amount Amount to stake
     */
    function stakeRewards(uint256 _amount)
        external
        payable
        onlyOwner
        whenNotPaused
    {
        require(msg.value >= _amount, "Insufficient value sent");
        require(_amount >= MIN_STAKE_AMOUNT, "Below minimum stake amount");

        stakedRewards += _amount;
        totalRewardPool += _amount;

        emit RewardsStaked(msg.sender, _amount, block.timestamp);
    }

    /**
     * @dev Distribute rewards to a device
     * @param _deviceId Device ID
     * @param _metricCount Number of metrics reported
     */
    function distributeRewards(uint256 _deviceId, uint256 _metricCount)
        external
        onlyOwner
        validDevice(_deviceId)
        whenNotPaused
        nonReentrant
    {
        require(totalRewardPool >= distributedRewards, "Insufficient reward pool");

        uint256 rewardAmount = _calculateRewards(_metricCount);
        require(totalRewardPool >= distributedRewards + rewardAmount, "Insufficient rewards available");

        distributedRewards += rewardAmount;
        depinManager.addRewards(_deviceId, rewardAmount);
        canClaim[_deviceId] = true;

        emit RewardsDistributed(_deviceId, rewardAmount, block.timestamp);
    }

    /**
     * @dev Calculate rewards based on metrics
     * @param _metricCount Number of metrics reported
     */
    function _calculateRewards(uint256 _metricCount) internal pure returns (uint256) {
        return BASE_REWARD_RATE * _metricCount;
    }

    /**
     * @dev Slash a device for violations
     * @param _deviceId Device ID
     * @param _violationType Type of violation
     * @param _slashPercentage Percentage to slash (0-100)
     */
    function slashDevice(
        uint256 _deviceId,
        ViolationType _violationType,
        uint256 _slashPercentage
    )
        external
        onlyOwner
        validDevice(_deviceId)
        whenNotPaused
    {
        require(_slashPercentage <= 100, "Invalid slash percentage");
        require(_violationType != ViolationType.None, "Invalid violation type");

        DePINManager.Device memory device = depinManager.getDeviceInfo(_deviceId);
        uint256 totalRewards = device.totalRewards;

        uint256 slashAmount = (totalRewards * _slashPercentage) / 100;
        require(slashAmount > 0, "No rewards to slash");

        _slashingCounter++;

        SlashingEvent memory slashingEvent = SlashingEvent({
            deviceId: _deviceId,
            violationType: _violationType,
            amount: slashAmount,
            timestamp: block.timestamp,
            resolved: false
        });

        slashingHistory[_deviceId].push(slashingEvent);
        canClaim[_deviceId] = false;

        // Return slashed amount to pool
        totalRewardPool += slashAmount;

        emit DeviceSlashed(_deviceId, slashAmount, _violationType, block.timestamp);
    }

    /**
     * @dev Claim rewards for a device
     * @param _deviceId Device ID
     */
    function claimRewards(uint256 _deviceId)
        external
        validDevice(_deviceId)
        whenNotPaused
        nonReentrant
    {
        require(canClaim[_deviceId], "No claimable rewards");

        DePINManager.Device memory device = depinManager.getDeviceInfo(_deviceId);
        require(device.owner == msg.sender, "Not device owner");

        require(totalRewardPool >= device.totalRewards, "Insufficient pool balance");
        require(device.totalRewards > 0, "No rewards to claim");

        canClaim[_deviceId] = false;
        totalRewardPool -= device.totalRewards;

        payable(device.owner).transfer(device.totalRewards);

        emit RewardsClaimed(_deviceId, device.owner, device.totalRewards, block.timestamp);
    }

    /**
     * @dev Withdraw stake from reward pool
     * @param _amount Amount to withdraw
     */
    function withdrawStake(uint256 _amount)
        external
        onlyOwner
        whenNotPaused
        nonReentrant
    {
        require(_amount <= stakedRewards, "Insufficient staked amount");
        require(_amount <= address(this).balance, "Insufficient contract balance");

        stakedRewards -= _amount;
        totalRewardPool -= _amount;

        payable(owner()).transfer(_amount);

        emit StakeWithdrawn(msg.sender, _amount, block.timestamp);
    }

    /**
     * @dev Get slashing history for a device
     * @param _deviceId Device ID
     */
    function getSlashingHistory(uint256 _deviceId)
        external
        view
        validDevice(_deviceId)
        returns (SlashingEvent[] memory)
    {
        return slashingHistory[_deviceId];
    }

    /**
     * @dev Get reward pool statistics
     */
    function getPoolStats()
        external
        view
        returns (
            uint256 pool,
            uint256 staked,
            uint256 distributed,
            uint256 available
        )
    {
        return (
            totalRewardPool,
            stakedRewards,
            distributedRewards,
            totalRewardPool - distributedRewards
        );
    }

    /**
     * @dev Check if device can claim rewards
     * @param _deviceId Device ID
     */
    function checkClaimable(uint256 _deviceId) external view returns (bool) {
        return canClaim[_deviceId];
    }

    /**
     * @dev Update base reward rate (Owner only)
     * @param _newRate New base reward rate
     */
    function updateBaseRewardRate(uint256 _newRate) external onlyOwner {
        // In a full implementation, this would update the BASE_REWARD_RATE
        // For now, this is a placeholder for configuration updates
    }

    /**
     * @dev Pause contract
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @dev Unpause contract
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @dev Emergency withdraw
     */
    function emergencyWithdraw() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }

    // Allow contract to receive ETH
    receive() external payable {}
}
