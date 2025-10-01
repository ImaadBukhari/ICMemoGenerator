import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FileText, History } from 'lucide-react';

const Header = () => {
  const location = useLocation();

  const navItems = [
    { path: '/generate', label: 'GENERATE', icon: FileText },
    { path: '/history', label: 'HISTORY', icon: History },
  ];

  return (
    <header className="bg-surface border-b border-muted">
      <div className="container mx-auto px-6 max-w-7xl">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-4 group">
            <div className="logo-container group-hover:border-accent transition-colors duration-150">
              <img 
                src="/logo.jpg" 
                alt="Logo" 
                className="w-full h-full object-cover"
              />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-semibold text-accent font-mono tracking-wider">
                IC_MEMO_GENERATOR
              </span>
              <span className="text-xs text-secondary font-mono">
                v2.1.0 • Wyld VC
              </span>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="flex items-center space-x-1">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center space-x-2 px-4 py-2 text-xs font-mono font-medium transition-colors duration-150 border ${
                  location.pathname === path
                    ? 'bg-accent text-surface border-accent'
                    : 'text-accent border-muted hover:bg-hover hover:border-accent'
                }`}
              >
                <Icon className="w-3 h-3" />
                <span>{label}</span>
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;