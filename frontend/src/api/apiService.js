import api from "./client";

// Common, reusable methods for calling the FastAPI backend.
// Use these from pages instead of calling axios directly, so every
// call goes through the same request/response handling.

export async function get(url, config = {}) {
  const res = await api.get(url, config);
  return res.data;
}

export async function post(url, body = {}, config = {}) {
  const res = await api.post(url, body, config);
  return res.data;
}

export async function put(url, body = {}, config = {}) {
  const res = await api.put(url, body, config);
  return res.data;
}

export async function del(url, config = {}) {
  const res = await api.delete(url, config);
  return res.data;
}
