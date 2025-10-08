import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import MemoGenerator from './components/MemoGenerator';
import './App.css';

// Main application component with routing
function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <Routes>
          <Route path="/" element={<MemoGenerator />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;