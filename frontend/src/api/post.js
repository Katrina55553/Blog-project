import client from "./client";

export function getPosts(page = 1, size = 10, tag = "") {
  return client.get("/posts", { params: { page, size, tag } });
}

export function getMyPosts(page = 1, size = 20) {
  return client.get("/admin/posts", { params: { page, size } });
}

export function getPostBySlug(slug) {
  return client.get(`/posts/${slug}`);
}

export function getPostById(id) {
  return client.get(`/admin/posts/${id}`);
}

export function createPost(data) {
  return client.post("/admin/posts", data);
}

export function updatePost(id, data) {
  return client.put(`/admin/posts/${id}`, data);
}

export function deletePost(id) {
  return client.delete(`/admin/posts/${id}`);
}
