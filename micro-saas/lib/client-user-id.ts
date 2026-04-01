const STORAGE_KEY = "pdf-saas-user-id";

function createUserId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `user-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
}

export function getOrCreateUserId() {
  if (typeof window === "undefined") {
    return "anonymous";
  }

  const existing = window.localStorage.getItem(STORAGE_KEY);
  if (existing) {
    return existing;
  }

  const nextId = createUserId();
  window.localStorage.setItem(STORAGE_KEY, nextId);
  return nextId;
}
