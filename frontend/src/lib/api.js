/**
 * Centralized API configuration.
 * 
 * Priority order:
 * 1. VITE_API_BASE env variable (set in .env or Vercel dashboard)
 * 2. Fallback to localhost:8000 for local dev
 */
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export default API_BASE;
