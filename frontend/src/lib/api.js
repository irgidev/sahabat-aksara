/**
 * Centralized API configuration + robust fetch utility.
 *
 * Priority order:
 * 1. VITE_API_BASE env variable (set in .env or Vercel dashboard)
 * 2. Fallback to localhost:8000 for local dev
 *
 * Includes fetchWithTimeout with auto-retry for unreliable networks
 * (e.g., ngrok free tier which can be slow or drop connections).
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

/**
 * Fetch with configurable timeout and automatic retry.
 * Essential for ngrok/tunnel connections that can be slow or flaky.
 *
 * @param {string} url - API endpoint path (e.g., '/api/dashboard/summary')
 * @param {object} options - Standard fetch options
 * @param {object} config - Optional config
 * @param {number} config.timeoutMs - Timeout in ms (default: 30000 for tunnel, 10000 for localhost)
 * @param {number} config.retries - Number of retries (default: 2)
 * @param {number} config.retryDelayMs - Delay between retries in ms (default: 1000)
 */
export async function apiFetch(url, options = {}, config = {}) {
  const isTunnel = API_BASE.includes('ngrok') || API_BASE.includes('trycloudflare') || API_BASE.includes('localtunnel');
  const timeoutMs = config.timeoutMs || (isTunnel ? 30000 : 15000);
  const retries = config.retries ?? (isTunnel ? 2 : 1);
  const retryDelayMs = config.retryDelayMs || 1000;

  const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

      const res = await fetch(fullUrl, {
        ...options,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      return res;
    } catch (err) {
      if (attempt < retries) {
        // Don't retry on abort from user navigation
        if (err.name === 'AbortError' && attempt === 0 && !config.silent) {
          console.warn(`[apiFetch] Request timed out (${timeoutMs}ms), retry ${attempt + 1}/${retries}: ${fullUrl}`);
        }
        await new Promise(r => setTimeout(r, retryDelayMs * (attempt + 1)));
        continue;
      }
      if (!config.silent) {
        console.error(`[apiFetch] Failed after ${retries + 1} attempts:`, fullUrl, err);
      }
      throw err;
    }
  }
}

export default API_BASE;
