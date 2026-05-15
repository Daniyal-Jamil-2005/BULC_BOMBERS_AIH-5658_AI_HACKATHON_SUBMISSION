/**
 * Centralized API Configuration
 * 
 * This file provides a single source of truth for all API endpoints
 * and configuration used throughout the frontend application.
 * 
 * Environment Variables:
 * - REACT_APP_API_URL: Base URL for the backend API (defaults to localhost:8000)
 */

const API_CONFIG = {
  // Base URL for all API requests
  // Uses environment variable if available, falls back to localhost for development
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  
  // API endpoint paths
  endpoints: {
    // Core scanning endpoints
    processFiles: '/process-files',
    sampleData: '/sample-data',
    health: '/health',
    
    // Email scanning endpoints
    scanGmail: '/scan-gmail',
    scanOutlook: '/scan-outlook',
    emailCredentials: '/email-credentials',
    
    // Analytics endpoints
    analytics: '/process-with-analytics',
    history: '/analytics/history',
    
    // User profile endpoints
    profile: '/profile',
    
    // Bookmark endpoints
    bookmarks: '/bookmarks',
    
    // Checklist endpoints
    checklists: '/checklists'
  },
  
  // Request timeout in milliseconds (30 seconds)
  timeout: 30000
};

export default API_CONFIG;
