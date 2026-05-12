import client from "./client";

export function getUserProfile(username) {
  return client.get(`/users/${username}`);
}
