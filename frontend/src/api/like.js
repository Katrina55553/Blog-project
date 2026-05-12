import client from "./client";

export function likePost(postId) {
  return client.post(`/likes/${postId}`);
}

export function unlikePost(postId) {
  return client.delete(`/likes/${postId}`);
}
