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

    <div v-if="loading" class="state">加载中...</div>
    <div v-else-if="error" class="state error">{{ error }}</div>
    <div v-else-if="posts.length === 0" class="state">暂无文章</div>

    <div v-else class="posts">
      <article v-for="post in posts" :key="post.id" class="card">
        <router-link :to="`/post/${post.slug}`" class="title">
          {{ post.title }}
        </router-link>
        <p class="summary">{{ post.summary }}</p>
        <div class="meta">
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
h1 { margin-bottom: 1.5rem; }
.state { text-align: center; padding: 2rem; color: #888; }
.error { color: #d32f2f; }
.card {
  padding: 1.2rem 0;
  border-bottom: 1px solid #eee;
}
.title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #222;
  text-decoration: none;
}
.title:hover { color: #1976d2; }
.summary {
  margin: 0.4rem 0;
  color: #666;
  font-size: 0.95rem;
}
.meta {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  font-size: 0.85rem;
  color: #999;
}
.tags { display: flex; gap: 0.3rem; }
.tag {
  background: #f0f0f0;
  border: none;
  padding: 0.15rem 0.5rem;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.8rem;
  color: #555;
}
.tag.active { background: #1976d2; color: #fff; }
.pagination {
  display: flex;
  justify-content: center;
  gap: 0.4rem;
  margin-top: 2rem;
}
.pagination button {
  padding: 0.4rem 0.8rem;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.pagination button.current { background: #333; color: #fff; border-color: #333; }
</style>
