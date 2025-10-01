import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ApiProvider } from './contexts/ApiContext';
import Header from './components/Header';
import MemoGenerator from './components/MemoGenerator';
import MemoProgress from './components/MemoProgress';
import MemoHistory from './components/MemoHistory';

function App() {
  return (
    <ApiProvider>
      <Router>
        <div className="min-h-screen bg-gradient-to-br from-dark-50 via-cyber-900 to-dark-100">
          <Header />
          <main className="container mx-auto px-4 py-6 max-w-7xl">
            <Routes>
              <Route path="/" element={<Navigate to="/generate" replace />} />
              <Route path="/generate" element={<MemoGenerator />} />
              <Route path="/memo/:memoId/progress" element={<MemoProgress />} />
              <Route path="/history" element={<MemoHistory />} />
            </Routes>
          </main>
        </div>
      </Router>
    </ApiProvider>
  );
}

export default App;