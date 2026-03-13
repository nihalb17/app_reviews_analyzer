// ============================================
// Frontend Configuration
// ============================================
// This file is used to configure the frontend for different environments
// For production deployment, set API_BASE_URL to your backend URL

// Production backend URL - UPDATE THIS when deploying
// Example: "https://your-app.onrender.com/api"
const PRODUCTION_API_URL = "https://app-reviews-analyzer-1.onrender.com/api";

// Auto-detect environment
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';

// Set the API base URL
window.API_BASE_URL = isProduction ? PRODUCTION_API_URL : null;
