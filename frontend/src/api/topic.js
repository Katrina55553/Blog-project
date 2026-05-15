import client from "./client";

export function getTopics(page = 1, size = 10, q = "") {
  return client.get("/topics", { params: { page, size, q } });
}

export function getTopicById(id) {
  return client.get(`/topics/${id}`);
}

export function getTopicForEdit(id) {
  return client.get(`/topics/${id}/edit`);
}

export function createTopic(data) {
  return client.post("/topics", data);
}

export function updateTopic(id, data) {
  return client.put(`/topics/${id}`, data);
}

export function deleteTopic(id) {
  return client.delete(`/topics/${id}`);
}
