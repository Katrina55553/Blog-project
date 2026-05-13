import client from "./client";

export function createComment(postId, content, parentId = null) {
  return client.post("/comments", { post_id: postId, content, parent_id: parentId });
}

export function deleteComment(commentId) {
  return client.delete(`/comments/${commentId}`);
}
