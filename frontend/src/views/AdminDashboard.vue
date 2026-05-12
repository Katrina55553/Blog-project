<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { getMyPosts, deletePost } from "../api/post";

const router = useRouter();
const posts = ref([]);
const loading = ref(true);
const error = ref("");

async function fetchPosts() {
  loading.value = true;
  error.value = "";
  try {
    const res = await getMyPosts(1, 100);
    posts.value = res.data.items;
  } catch {
    error.value = "加载失败";
  } finally {
    loading.value = false;
  }
}

async function handleDelete(post) {
  if (!confirm(`确定删除「${post.title}」？`)) return;
  try {
    await deletePost(post.id);
    posts.value = posts.value.filter((p) => p.id !== post.id);
  } catch {
    alert("删除失败");
  }
}

function goEdit(post) {
  router.push(`/admin/posts/${post.id}/edit`);
}

onMounted(fetchPosts);
</script>

<template>
  <div class="admin-dashboard">
    <h1>我的文章</h1>
    <router-link to="/admin/posts/new" class="btn-new">+ 写新文章</router-link>

    <div v-if="loading" class="state">加载中...</div>
    <div v-else-if="error" class="state">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="fetchPosts">重试</button>
    </div>
    <div v-else-if="posts.length === 0" class="state">还没有文章</div>

    <table v-else class="post-table">
      <thead>
        <tr>
          <th>标题</th>
          <th>日期</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="post in posts" :key="post.id">
          <td>
            <router-link :to="`/post/${post.slug}`">{{ post.title }}</router-link>
          </td>
          <td>{{ new Date(post.created_at).toLocaleDateString() }}</td>
          <td class="actions">
            <button class="btn-edit" @click="goEdit(post)">编辑</button>
            <button class="btn-delete" @click="handleDelete(post)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.admin-dashboard { max-width: 700px; margin: 0 auto; }
h1 { margin-bottom: 1rem; color: var(--color-text); }
.state { text-align: center; padding: 2rem; color: var(--color-text-muted); }
.btn-new {
  display: inline-block;
  margin-bottom: 1.5rem;
  padding: 0.5rem 1.2rem;
  background: var(--color-text);
  color: var(--color-bg);
  text-decoration: none;
  border-radius: var(--radius);
  font-size: 0.95rem;
}
.post-table {
  width: 100%;
  border-collapse: collapse;
}
.post-table th, .post-table td {
  text-align: left;
  padding: 0.7rem 0.5rem;
  border-bottom: 1px solid var(--color-border-light);
}
.post-table th {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}
.post-table a {
  color: var(--color-text);
  text-decoration: none;
}
.post-table a:hover { color: var(--color-primary); }
.actions { white-space: nowrap; }
.actions button {
  padding: 0.25rem 0.7rem;
  border: 1px solid var(--color-border);
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.85rem;
  background: var(--color-bg);
  color: var(--color-text);
}
.btn-edit { margin-right: 0.3rem; }
.btn-edit:hover { border-color: var(--color-primary); color: var(--color-primary); }
.btn-delete { color: var(--color-danger); }
.btn-delete:hover { background: var(--color-danger-bg); border-color: var(--color-danger); }
.btn-retry {
  margin-top: 0.5rem;
  padding: 0.4rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
  color: var(--color-text);
  cursor: pointer;
}
</style>
