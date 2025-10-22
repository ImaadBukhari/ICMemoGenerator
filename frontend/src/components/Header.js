import React from 'react';
import './Header.css';

// Header component with logo, title, and user info
function Header({ user, onLogout }) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <img src="/logo.jpg" alt="Logo" className="logo" />
          <h1 className="header-title">IC Memo Generator</h1>
        </div>
        <div className="header-right">
          <span className="user-email">{user?.email}</span>
          <button onClick={onLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header;