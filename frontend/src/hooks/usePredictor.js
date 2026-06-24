// src/hooks/usePredictor.js
import { useState, useCallback } from "react";

const API = import.meta.env.VITE_API_URL || "";

async function callApi(endpoint, body) {
  const res = await fetch(`${API}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export function usePredictor() {
  const [state, setState] = useState({
    loading: false,
    result:  null,
    error:   null,
    step:    null, // "scraping" | "analyzing"
  });

  const predictUrl = useCallback(async (url, threshold = 0.5) => {
    setState({ loading: true, result: null, error: null, step: "scraping" });
    try {
      // Simulate step transition
      const timer = setTimeout(() =>
        setState(s => ({ ...s, step: "analyzing" })), 1800);
      const data = await callApi("/predict/url", { url, threshold });
      clearTimeout(timer);
      setState({ loading: false, result: data, error: null, step: null });
      return data;
    } catch (e) {
      setState({ loading: false, result: null, error: e.message, step: null });
    }
  }, []);

  const predictText = useCallback(async (text, threshold = 0.5) => {
    setState({ loading: true, result: null, error: null, step: "analyzing" });
    try {
      const data = await callApi("/predict/text", { text, threshold });
      setState({ loading: false, result: data, error: null, step: null });
      return data;
    } catch (e) {
      setState({ loading: false, result: null, error: e.message, step: null });
    }
  }, []);

  const reset = useCallback(() =>
    setState({ loading: false, result: null, error: null, step: null }), []);

  const setResult = useCallback((res) =>
    setState(s => ({ ...s, result: res, error: null, step: null })), []);

  return { ...state, predictUrl, predictText, reset, setResult };
}
