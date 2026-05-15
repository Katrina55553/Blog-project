import client from "./client";

export function createComment(topicId, content, parentId = null) {
  return client.post("/comments", { content, topic_id: topicId, parent_id: parentId });
}

export function deleteComment(id) {
  return client.delete(`/comments/${id}`);
}
