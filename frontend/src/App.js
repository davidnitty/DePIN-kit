/**
 * Main App Component
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';

// Placeholder pages
const Devices = () => (
  <div className="page-container">
    <h1>Devices</h1>
    <p>Manage your DePIN devices</p>
  </div>
);

const Analytics = () => (
  <div className="page-container">
    <h1>Analytics</h1>
    <p>View network analytics and insights</p>
  </div>
);

const Profile = () => (
  <div className="page-container">
    <h1>Profile</h1>
    <p>Manage your profile and settings</p>
  </div>
);

function App() {
  return (
    <Router>
      <div className="App">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/devices" element={<Devices />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/profile" element={<Profile />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
