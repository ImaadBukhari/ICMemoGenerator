import React from 'react';
import './Header.css';

function Header() {
  return (
    <header className="header">
      <div className="header-content">
        <img src="/logo.jpg" alt="Logo" className="logo" />
        <h1 className="header-title">IC Memo Generator</h1>
      </div>
    </header>
  );
}

export default Header;