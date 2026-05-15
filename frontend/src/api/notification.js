import client from "./client";

export function getNotifications(page = 1, size = 20) {
  return client.get("/notifications", { params: { page, size } });
}

export function getUnreadCount() {
  return client.get("/notifications/unread-count");
}

export function markRead(id) {
  return client.put(`/notifications/${id}/read`);
}

export function markAllRead() {
  return client.put("/notifications/read-all");
}
