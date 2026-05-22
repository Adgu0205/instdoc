// API Base URL config (defaults to localhost:8000 for local development)
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Uploads a document file (.pdf, .docx, .txt) to the backend for parsing and risk analysis.
 */
export async function analyzeFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/analyze/file`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorDetails = await response.json().catch(() => ({}));
    throw new Error(errorDetails.detail || 'An error occurred during file parsing and analysis.');
  }

  return response.json();
}

/**
 * Uploads a document file and tracks real-time upload progress.
 */
export function analyzeFileWithProgress(file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);

    if (xhr.upload && onProgress) {
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          onProgress(percent);
        }
      });
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const res = JSON.parse(xhr.responseText);
          resolve(res);
        } catch (e) {
          reject(new Error('Failed to parse analysis response.'));
        }
      } else {
        let errMsg = 'An error occurred during file parsing and analysis.';
        try {
          const errRes = JSON.parse(xhr.responseText);
          errMsg = errRes.detail || errMsg;
        } catch (e) {}
        reject(new Error(errMsg));
      }
    };

    xhr.onerror = () => {
      reject(new Error('Network error. Please check if the server is accessible.'));
    };

    xhr.open('POST', `${API_BASE_URL}/api/analyze/file`);
    xhr.send(formData);
  });
}

/**
 * Sends pasted contract text to the backend for risk analysis.
 */
export async function analyzeText(text) {
  const response = await fetch(`${API_BASE_URL}/api/analyze/text`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    const errorDetails = await response.json().catch(() => ({}));
    throw new Error(errorDetails.detail || 'An error occurred during text analysis.');
  }

  return response.json();
}

/**
 * Retrieves aggregate system usage analytics.
 */
export async function getAnalytics() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/analyze/analytics`);
    if (!response.ok) return null;
    return await response.json();
  } catch (e) {
    console.error('Failed to fetch analytics:', e);
    return null;
  }
}
