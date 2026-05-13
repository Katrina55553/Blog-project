<script setup>
import { ref, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import { getMyPosts, deletePost } from "../api/post";
import { showConfirm } from "../composables/confirm";
import { showToast } from "../composables/toast";

const router = useRouter();
const posts = ref([]);
const loading = ref(true);
const error = ref("");
const page = ref(1);
const total = ref(0);
const pages = ref(0);
const size = 10;

async function fetchPosts() {
  loading.value = true;
  error.value = "";
  try {
    const res = await getMyPosts(page.value, size);
    posts.value = res.data.items;
    total.value = res.data.total;
    pages.value = res.data.pages;
  } catch {
    error.value = "加载失败";
  } finally {
    loading.value = false;
  }
}

function goPage(p) {
  page.value = p;
}

async function handleDelete(post) {
  if (!await showConfirm(`确定删除「${post.title}」？`)) return;
  try {
    await deletePost(post.id);
    posts.value = posts.value.filter((p) => p.id !== post.id);
    showToast.success("删除成功");
  } catch {
    showToast.error("删除失败");
  }
}

function goEdit(post) {
  router.push(`/admin/posts/${post.id}/edit`);
}

onMounted(fetchPosts);
watch(page, fetchPosts);
</script>

<template>
  <div class="admin-dashboard">
    <h1>我的文章</h1>
    <router-link to="/admin/posts/new" class="btn-new">+ 写新文章</router-link>

    <div v-if="loading" class="skeleton-list">
      <div v-for="n in 5" :key="n" class="skeleton-row">
        <div class="skeleton-line w-50"></div>
        <div class="skeleton-line w-20"></div>
      </div>
    </div>
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

    <div v-if="pages > 1" class="pagination">
      <button :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
      <span v-for="p in pages" :key="p">
        <button :class="{ current: p === page }" @click="goPage(p)">{{ p }}</button>
      </span>
      <button :disabled="page >= pages" @click="goPage(pages)">下一页</button>
    </div>
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

/* Skeleton */
.skeleton-list { display: flex; flex-direction: column; gap: 0.5rem; }
.skeleton-row {
  display: flex;
  gap: 2rem;
  padding: 0.7rem 0.5rem;
  border-bottom: 1px solid var(--color-border-light);
}
.skeleton-line {
  height: 14px;
  background: var(--color-border);
  border-radius: 4px;
  animation: shimmer 1.5s infinite;
}
.skeleton-line.w-50 { width: 50%; }
.skeleton-line.w-20 { width: 20%; }
@keyframes shimmer {
  0% { opacity: 0.4; }
  50% { opacity: 0.8; }
  100% { opacity: 0.4; }
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  gap: 0.4rem;
  margin-top: 2rem;
}
.pagination button {
  padding: 0.4rem 0.8rem;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text);
  border-radius: 4px;
  cursor: pointer;
}
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.pagination button.current { background: var(--color-text); color: var(--color-bg); border-color: var(--color-text); }
</style>
