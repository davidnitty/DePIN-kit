// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title DePINManager
 * @dev Main registry contract for managing IoTeX DePIN devices
 * @author IoTeX DePIN Kit
 */
contract DePINManager is Ownable, Pausable, ReentrancyGuard {

    // Structs
    struct Device {
        uint256 id;
        address owner;
        string metadataURI; // IPFS hash
        DeviceStatus status;
        uint256 totalRewards;
        uint256 registrationTime;
        uint256 lastReportTime;
    }

    struct MetricData {
        uint256 deviceId;
        uint256 timestamp;
        uint256 value;
        string dataType; // e.g., "temperature", "humidity", "energy"
        bool isVerified;
    }

    enum DeviceStatus {
        Inactive,
        Active,
        Paused,
        Suspended
    }

    // State Variables
    uint256 private _deviceCounter;
    uint256 private _metricsCounter;

    mapping(uint256 => Device) public devices;
    mapping(uint256 => MetricData[]) public deviceMetrics;
    mapping(address => uint256[]) public ownerDevices;
    mapping(uint256 => bool) public deviceExists;

    // Arrays for enumeration
    uint256[] public allDeviceIds;

    // Events
    event DeviceRegistered(
        uint256 indexed deviceId,
        address indexed owner,
        string metadataURI,
        uint256 timestamp
    );

    event MetricsReported(
        uint256 indexed deviceId,
        uint256 indexed metricId,
        uint256 value,
        string dataType,
        uint256 timestamp
    );

    event DeviceStatusUpdated(
        uint256 indexed deviceId,
        DeviceStatus newStatus,
        uint256 timestamp
    );

    event RewardsDistributed(
        uint256 indexed deviceId,
        uint256 amount,
        uint256 timestamp
    );

    // Modifiers
    modifier onlyDeviceOwner(uint256 _deviceId) {
        require(devices[_deviceId].owner == msg.sender, "Not device owner");
        _;
    }

    modifier onlyActiveDevice(uint256 _deviceId) {
        require(deviceExists[_deviceId], "Device does not exist");
        require(devices[_deviceId].status == DeviceStatus.Active, "Device not active");
        _;
    }

    // Constructor
    constructor() Ownable(msg.sender) {
        _deviceCounter = 0;
        _metricsCounter = 0;
    }

    /**
     * @dev Register a new DePIN device
     * @param _metadataURI IPFS hash containing device metadata
     */
    function registerDevice(string memory _metadataURI)
        external
        whenNotPaused
        returns (uint256)
    {
        _deviceCounter++;
        uint256 deviceId = _deviceCounter;

        devices[deviceId] = Device({
            id: deviceId,
            owner: msg.sender,
            metadataURI: _metadataURI,
            status: DeviceStatus.Active,
            totalRewards: 0,
            registrationTime: block.timestamp,
            lastReportTime: block.timestamp
        });

        deviceExists[deviceId] = true;
        ownerDevices[msg.sender].push(deviceId);
        allDeviceIds.push(deviceId);

        emit DeviceRegistered(deviceId, msg.sender, _metadataURI, block.timestamp);

        return deviceId;
    }

    /**
     * @dev Report metrics from a device
     * @param _deviceId Device ID
     * @param _value Metric value
     * @param _dataType Type of metric data
     */
    function reportMetrics(
        uint256 _deviceId,
        uint256 _value,
        string memory _dataType
    )
        external
        onlyDeviceOwner(_deviceId)
        onlyActiveDevice(_deviceId)
        whenNotPaused
    returns (uint256)
    {
        _metricsCounter++;

        MetricData memory newMetric = MetricData({
            deviceId: _deviceId,
            timestamp: block.timestamp,
            value: _value,
            dataType: _dataType,
            isVerified: false
        });

        deviceMetrics[_deviceId].push(newMetric);
        devices[_deviceId].lastReportTime = block.timestamp;

        emit MetricsReported(_deviceId, _metricsCounter, _value, _dataType, block.timestamp);

        return _metricsCounter;
    }

    /**
     * @dev Get device information
     * @param _deviceId Device ID
     */
    function getDeviceInfo(uint256 _deviceId)
        external
        view
        returns (Device memory)
    {
        require(deviceExists[_deviceId], "Device does not exist");
        return devices[_deviceId];
    }

    /**
     * @dev Get all devices owned by an address
     * @param _owner Owner address
     */
    function getDevicesByOwner(address _owner)
        external
        view
        returns (uint256[] memory)
    {
        return ownerDevices[_owner];
    }

    /**
     * @dev Get metrics for a device
     * @param _deviceId Device ID
     */
    function getMetrics(uint256 _deviceId)
        external
        view
        returns (MetricData[] memory)
    {
        require(deviceExists[_deviceId], "Device does not exist");
        return deviceMetrics[_deviceId];
    }

    /**
     * @dev Get total number of devices
     */
    function getTotalDevices() external view returns (uint256) {
        return _deviceCounter;
    }

    /**
     * @dev Get all device IDs
     */
    function getAllDeviceIds() external view returns (uint256[] memory) {
        return allDeviceIds;
    }

    /**
     * @dev Update device status (Owner only)
     * @param _deviceId Device ID
     * @param _newStatus New status
     */
    function updateDeviceStatus(uint256 _deviceId, DeviceStatus _newStatus)
        external
        onlyOwner
    {
        require(deviceExists[_deviceId], "Device does not exist");
        devices[_deviceId].status = _newStatus;
        emit DeviceStatusUpdated(_deviceId, _newStatus, block.timestamp);
    }

    /**
     * @dev Add rewards to a device
     * @param _deviceId Device ID
     * @param _amount Reward amount
     */
    function addRewards(uint256 _deviceId, uint256 _amount)
        external
        onlyOwner
    {
        require(deviceExists[_deviceId], "Device does not exist");
        devices[_deviceId].totalRewards += _amount;
        emit RewardsDistributed(_deviceId, _amount, block.timestamp);
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
}
