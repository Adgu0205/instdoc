// API Base URL config (defaults to localhost:8000 for local development)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
