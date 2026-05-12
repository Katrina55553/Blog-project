<script setup>
import { ref, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getPosts } from "../api/post";

const route = useRoute();
const router = useRouter();

const posts = ref([]);
const total = ref(0);
const pages = ref(0);
const page = ref(1);
const tag = ref("");
const loading = ref(true);
const error = ref("");

const size = 10;

async function fetchPosts() {
  loading.value = true;
  error.value = "";
  try {
    const res = await getPosts(page.value, size, tag.value);
    posts.value = res.data.items;
    total.value = res.data.total;
    pages.value = res.data.pages;
  } catch {
    error.value = "加载失败，请稍后重试";
  } finally {
    loading.value = false;
  }
}

function goPage(p) {
  page.value = p;
}

function selectTag(t) {
  tag.value = tag.value === t ? "" : t;
}

onMounted(fetchPosts);
watch(page, fetchPosts);
watch(tag, () => {
  page.value = 1;
  fetchPosts();
});
</script>

<template>
  <div class="home">
    <h1>文章列表</h1>

    <div v-if="loading" class="skeleton-list">
      <div v-for="n in 3" :key="n" class="skeleton-card">
        <div class="skeleton-line w-60"></div>
        <div class="skeleton-line w-90"></div>
        <div class="skeleton-line w-40"></div>
      </div>
    </div>
    <div v-else-if="error" class="state error">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="fetchPosts">重试</button>
    </div>
    <div v-else-if="posts.length === 0" class="state">暂无文章</div>

    <div v-else class="posts">
      <article v-for="post in posts" :key="post.id" class="card">
        <router-link :to="`/post/${post.slug}`" class="title">
          {{ post.title }}
        </router-link>
        <p class="summary">{{ post.summary }}</p>
        <div class="meta">
          <span class="author">{{ post.author?.username }}</span>
          <span class="date">{{ new Date(post.created_at).toLocaleDateString() }}</span>
          <span v-if="post.tags?.length" class="tags">
            <button
              v-for="t in post.tags"
              :key="t"
              class="tag"
              :class="{ active: tag === t }"
              @click="selectTag(t)"
            >
              {{ t }}
            </button>
          </span>
        </div>
      </article>

      <div v-if="pages > 1" class="pagination">
        <button :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
        <span v-for="p in pages" :key="p">
          <button :class="{ current: p === page }" @click="goPage(p)">{{ p }}</button>
        </span>
        <button :disabled="page >= pages" @click="goPage(pages)">下一页</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home { max-width: 700px; margin: 0 auto; }
h1 { margin-bottom: 1.5rem; color: var(--color-text); }
.state { text-align: center; padding: 2rem; color: var(--color-text-muted); }
.error { color: var(--color-danger); }
.btn-retry {
  margin-top: 0.5rem;
  padding: 0.4rem 1.2rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
  color: var(--color-text);
  cursor: pointer;
  font-size: 0.9rem;
}
.btn-retry:hover { border-color: var(--color-primary); color: var(--color-primary); }

/* Skeleton */
.skeleton-list { display: flex; flex-direction: column; gap: 0.8rem; }
.skeleton-card {
  padding: 1.4rem;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.skeleton-line {
  height: 14px;
  background: var(--color-border);
  border-radius: 4px;
  animation: shimmer 1.5s infinite;
}
.skeleton-line.w-60 { width: 60%; }
.skeleton-line.w-90 { width: 90%; }
.skeleton-line.w-40 { width: 40%; }
@keyframes shimmer {
  0% { opacity: 0.4; }
  50% { opacity: 0.8; }
  100% { opacity: 0.4; }
}
.card {
  padding: 1.4rem;
  margin-bottom: 0.8rem;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius);
  transition: background 0.2s, box-shadow 0.2s;
}
.card:hover {
  background: var(--color-card-hover);
  box-shadow: var(--shadow-sm);
}
.title {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--color-text);
  text-decoration: none;
}
.title:hover { color: var(--color-primary); }
.summary {
  margin: 0.4rem 0;
  color: var(--color-text-secondary);
  font-size: 0.95rem;
}
.meta {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}
.tags { display: flex; gap: 0.3rem; }
.tag {
  background: var(--color-tag-bg);
  border: none;
  padding: 0.15rem 0.5rem;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.8rem;
  color: var(--color-tag-text);
}
.tag.active { background: var(--color-primary); color: #fff; }
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
