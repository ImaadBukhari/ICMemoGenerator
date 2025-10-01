const config = {
    development: {
      API_URL: 'http://localhost:8000',
    },
    production: {
      API_URL: process.env.REACT_APP_API_URL || window.location.origin.replace('frontend', 'backend'),
    }
  };
  
  const environment = process.env.NODE_ENV || 'development';
  
  export default config[environment];