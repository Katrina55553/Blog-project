import client from "./client";

export function createComment(postId, content) {
  return client.post("/comments", { post_id: postId, content });
}
