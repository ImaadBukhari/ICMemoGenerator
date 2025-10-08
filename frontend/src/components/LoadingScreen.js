import React from 'react';
import './LoadingScreen.css';

// Loading screen component showing progress of memo generation
function LoadingScreen({ currentSection, progress, totalSections, completedSections }) {
  return (
    <div className="loading-screen">
      <div className="loading-content">
        <div className="loading-spinner">
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
        </div>

        <h2 className="loading-title">Generating Your Memo</h2>

        <div className="progress-container">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            />
          </div>
          
          <div className="progress-text">
            {completedSections} of {totalSections} sections complete ({Math.round(progress)}%)
          </div>
        </div>

        {currentSection && (
          <div className="current-section">
            <div className="current-section-label">Currently generating:</div>
            <div className="current-section-name">{currentSection}</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default LoadingScreen;