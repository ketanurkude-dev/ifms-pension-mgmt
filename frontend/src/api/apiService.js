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

// Downloads a PDF (or any binary file) returned by the backend and saves
// it in the browser under the given filename.
export async function downloadFile(url, filename) {
  const res = await api.get(url, { responseType: "blob" });
  const blobUrl = window.URL.createObjectURL(res.data);
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(blobUrl);
}
