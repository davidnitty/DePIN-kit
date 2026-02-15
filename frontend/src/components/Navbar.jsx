/**
 * Navbar Component
 * Main navigation bar for the application
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navbar.css';

const Navbar = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/devices', label: 'Devices', icon: '🔧' },
    { path: '/analytics', label: 'Analytics', icon: '📈' },
    { path: '/profile', label: 'Profile', icon: '👤' },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <Link to="/" className="navbar-logo">
            <span className="logo-icon">⚡</span>
            <span className="logo-text">IoTeX DePIN Kit</span>
          </Link>
        </div>

        <ul className="navbar-menu">
          {navItems.map((item) => (
            <li key={item.path} className="navbar-item">
              <Link
                to={item.path}
                className={`navbar-link ${
                  location.pathname === item.path ? 'active' : ''
                }`}
              >
                <span className="navbar-icon">{item.icon}</span>
                <span className="navbar-label">{item.label}</span>
              </Link>
            </li>
          ))}
        </ul>

        <div className="navbar-actions">
          <button className="navbar-button connect-wallet">
            Connect Wallet
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
