import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import './Login.css';

function Login({ onLogin }) {
  const [error, setError] = useState('');

  const handleGoogleSuccess = async (credentialResponse) => {
    setError('');
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/auth/google-login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ credential: credentialResponse.credential }),
      });

      if (response.ok) {
        const data = await response.json();
        // Store the Google credential as the token
        localStorage.setItem('authToken', credentialResponse.credential);
        localStorage.setItem('user', JSON.stringify(data.user));
        onLogin(credentialResponse.credential, data.user);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Login failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
  };

  const handleGoogleError = () => {
    setError('Google login failed. Please try again.');
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>IC Memo Generator</h2>
        <p>Please login with your company Google account</p>
        
        {error && <div className="error-message">{error}</div>}
        
        <div className="google-login-container">
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
            theme="outline"
            size="large"
            width="300"
            text="signin_with"
            shape="rectangular"
            logo_alignment="left"
          />
        </div>
        
        <p className="login-note">
          Only company domain emails are allowed
        </p>
      </div>
    </div>
  );
}

export default Login;
