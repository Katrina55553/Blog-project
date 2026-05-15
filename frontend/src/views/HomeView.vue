<script setup>
import { ref, onMounted, watch, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getTopics } from "../api/topic";

const route = useRoute();
const router = useRouter();

const topics = ref([]);
const total = ref(0);
const pages = ref(0);
const page = ref(1);
const searchInput = ref(route.query.q || "");
const loading = ref(true);
const error = ref("");

const q = computed(() => route.query.q || "");
const size = 10;

async function fetchTopics() {
  loading.value = true;
  error.value = "";
  try {
    const res = await getTopics(page.value, size, q.value);
    topics.value = res.data.items;
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

function doSearch() {
  const val = searchInput.value.trim();
  page.value = 1;
  if (val) {
    router.push({ name: "home", query: { q: val } });
  } else {
    router.push({ name: "home" });
  }
}

function formatTime(t) {
  if (!t) return "";
  const diff = Date.now() - new Date(t).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "刚刚";
  if (mins < 60) return `${mins}分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}小时前`;
  return new Date(t).toLocaleDateString();
}

onMounted(fetchTopics);
watch(page, fetchTopics);
watch(q, () => {
  page.value = 1;
  fetchTopics();
});
</script>

<template>
  <div class="home">
    <form class="search-bar" @submit.prevent="doSearch">
      <input v-model="searchInput" type="search" placeholder="搜索帖子..." class="search-input" />
    </form>

    <h1 v-if="q">搜索: "{{ q }}"</h1>
    <h1 v-else>最新帖子</h1>

    <p v-if="q && !loading" class="search-info">
      找到 {{ total }} 个帖子
      <router-link to="/" class="btn-clear">清除搜索</router-link>
    </p>

    <div v-if="loading" class="skeleton-list">
      <div v-for="n in 5" :key="n" class="skeleton-row">
        <div class="skeleton-line w-70"></div>
        <div class="skeleton-line w-40"></div>
      </div>
    </div>
    <div v-else-if="error" class="state error">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="fetchTopics">重试</button>
    </div>
    <div v-else-if="topics.length === 0" class="state">暂无帖子</div>

    <div v-else class="topic-list">
      <div v-for="t in topics" :key="t.id" class="topic-row">
        <div class="topic-main">
          <router-link :to="`/topic/${t.id}`" class="topic-title">{{ t.title }}</router-link>
          <div class="topic-meta">
            <router-link :to="`/user/${t.author?.username}`" class="author">{{ t.author?.username }}</router-link>
            <span>{{ formatTime(t.created_at) }}</span>
          </div>
        </div>
        <div class="topic-stats">
          <span title="回复">💬 {{ t.comment_count }}</span>
          <span title="点赞">❤️ {{ t.likes_count }}</span>
        </div>
      </div>

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
h1 { margin-bottom: 0.5rem; color: var(--color-text); }

.search-bar { margin-bottom: 1.5rem; }
.search-input {
  width: 100%;
  padding: 0.7rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 1rem;
  box-sizing: border-box;
  background: var(--color-bg);
  color: var(--color-text);
  outline: none;
  transition: border-color 0.2s;
}
.search-input:focus { border-color: var(--color-primary); }

.search-info {
  margin-bottom: 1rem;
  color: var(--color-text-muted);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.btn-clear {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 3px;
  padding: 0.15rem 0.5rem;
  cursor: pointer;
  color: var(--color-text-muted);
  font-size: 0.8rem;
  text-decoration: none;
}
.btn-clear:hover { color: var(--color-text); border-color: var(--color-text); }
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

.skeleton-list { display: flex; flex-direction: column; gap: 0.6rem; }
.skeleton-row {
  padding: 1rem 1.4rem;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.skeleton-line {
  height: 14px;
  background: var(--color-border);
  border-radius: 4px;
  animation: shimmer 1.5s infinite;
}
.skeleton-line.w-70 { width: 70%; }
.skeleton-line.w-40 { width: 40%; }
@keyframes shimmer {
  0% { opacity: 0.4; }
  50% { opacity: 0.8; }
  100% { opacity: 0.4; }
}

.topic-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.4rem;
  margin-bottom: 0.5rem;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius);
  transition: background 0.2s;
}
.topic-row:hover { background: var(--color-card-hover); }
.topic-main { flex: 1; min-width: 0; }
.topic-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--color-text);
  text-decoration: none;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.topic-title:hover { color: var(--color-primary); }
.topic-meta {
  display: flex;
  gap: 0.6rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin-top: 0.3rem;
}
.author { color: var(--color-text-muted); text-decoration: none; }
.author:hover { color: var(--color-primary); }
.topic-stats {
  display: flex;
  gap: 0.8rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
  flex-shrink: 0;
  margin-left: 1rem;
}
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
