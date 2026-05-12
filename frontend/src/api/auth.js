import client from "./client";

export function register(username, password) {
  return client.post("/auth/register", { username, password });
}

export function login(username, password) {
  return client.post("/auth/login", { username, password });
}

export function getMe() {
  return client.get("/auth/me");
}

export function updateMe(data) {
  return client.put("/auth/me", data);
}
