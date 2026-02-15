/**
 * Dashboard Component
 * Main dashboard displaying network overview and statistics
 */

import React, { useState, useEffect } from 'react';
import { healthAPI, deviceAPI, blockchainAPI } from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
  const [health, setHealth] = useState(null);
  const [devices, setDevices] = useState([]);
  const [blockchainStats, setBlockchainStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [healthRes, devicesRes, blockchainRes] = await Promise.all([
          healthAPI.check(),
          deviceAPI.getAll(),
          blockchainAPI.getStats(),
        ]);

        setHealth(healthRes);
        setDevices(devicesRes.devices || []);
        setBlockchainStats(blockchainRes.blockchain);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-container">
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>IoTeX DePIN Dashboard</h1>
        <p>Monitor and manage your decentralized physical infrastructure network</p>
      </div>

      {/* Health Status */}
      {health && (
        <div className="status-banner">
          <span className="status-indicator online"></span>
          <span>System Online</span>
        </div>
      )}

      {/* Statistics Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">🔧</div>
          <div className="stat-content">
            <div className="stat-label">Total Devices</div>
            <div className="stat-value">{devices.length}</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <div className="stat-label">Active Devices</div>
            <div className="stat-value">
              {devices.filter(d => d.status === 'Active').length}
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <div className="stat-label">Reward Pool</div>
            <div className="stat-value">
              {blockchainStats?.reward_pool?.available
                ? `${blockchainStats.reward_pool.available / 1e18} IOTX`
                : 'N/A'}
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⚡</div>
          <div className="stat-content">
            <div className="stat-label">Total Rewards</div>
            <div className="stat-value">
              {blockchainStats?.reward_pool?.distributed
                ? `${blockchainStats.reward_pool.distributed / 1e18} IOTX`
                : 'N/A'}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Devices */}
      <div className="recent-section">
        <h2>Recent Devices</h2>
        <div className="device-list">
          {devices.slice(0, 5).map((device) => (
            <div key={device.device_id} className="device-item">
              <div className="device-info">
                <div className="device-name">Device #{device.device_id}</div>
                <div className="device-type">{device.type}</div>
              </div>
              <div className={`device-status ${device.status.toLowerCase()}`}>
                {device.status}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Network Overview */}
      <div className="network-overview">
        <h2>Network Overview</h2>
        <div className="overview-content">
          <div className="overview-item">
            <div className="overview-label">Network Status</div>
            <div className="overview-value">Testnet</div>
          </div>
          <div className="overview-item">
            <div className="overview-label">Chain ID</div>
            <div className="overview-value">4690</div>
          </div>
          <div className="overview-item">
            <div className="overview-label">Connected Services</div>
            <div className="overview-value">
              {Object.values(health?.services || {}).filter(Boolean).length} / 4
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
