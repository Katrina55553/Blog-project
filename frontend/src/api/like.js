import client from "./client";

export function likeTopic(topicId) {
  return client.post(`/likes/${topicId}`);
}

export function unlikeTopic(topicId) {
  return client.delete(`/likes/${topicId}`);
}
