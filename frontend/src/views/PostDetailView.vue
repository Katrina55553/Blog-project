<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import { marked } from "marked";
import hljs from "highlight.js";
import "highlight.js/styles/github-dark.css";
import { getPostBySlug } from "../api/post";
import { createComment } from "../api/comment";
import { useAuthStore } from "../stores/auth";

const route = useRoute();
const auth = useAuthStore();

const post = ref(null);
const loading = ref(true);
const error = ref("");

const commentText = ref("");
const commentLoading = ref(false);
const commentError = ref("");

marked.setOptions({
  highlight(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value;
    }
    return hljs.highlightAuto(code).value;
  },
});

const renderedContent = computed(() => {
  if (!post.value?.content) return "";
  return marked(post.value.content);
});

async function fetchPost() {
  loading.value = true;
  error.value = "";
  try {
    const res = await getPostBySlug(route.params.slug);
    post.value = res.data;
  } catch {
    error.value = "文章不存在或加载失败";
  } finally {
    loading.value = false;
  }
}

async function handleComment() {
  if (!commentText.value.trim()) return;
  commentLoading.value = true;
  commentError.value = "";
  try {
    await createComment(post.value.id, commentText.value);
    commentText.value = "";
    await fetchPost(); // refresh to show new comment
  } catch (e) {
    commentError.value = e.response?.data?.detail || "评论失败";
  } finally {
    commentLoading.value = false;
  }
}

onMounted(fetchPost);
</script>

<template>
  <div class="post-detail">
    <div v-if="loading" class="state">加载中...</div>
    <div v-else-if="error" class="state error">{{ error }}</div>

    <article v-else>
      <h1>{{ post.title }}</h1>
      <div class="meta">
        <span>{{ new Date(post.created_at).toLocaleDateString() }}</span>
        <span v-if="post.tags?.length" class="tags">
          <span v-for="t in post.tags" :key="t" class="tag">{{ t }}</span>
        </span>
      </div>
      <div class="content" v-html="renderedContent"></div>

      <section class="comments">
        <h3>评论 ({{ post.comments?.length || 0 }})</h3>

        <div v-if="auth.user" class="comment-form">
          <textarea
            v-model="commentText"
            placeholder="写下你的评论..."
            rows="3"
          ></textarea>
          <div class="comment-actions">
            <button :disabled="commentLoading" @click="handleComment">
              {{ commentLoading ? "提交中..." : "发表评论" }}
            </button>
            <span v-if="commentError" class="error">{{ commentError }}</span>
          </div>
        </div>
        <p v-else class="login-hint">
          <router-link to="/login">登录</router-link> 后发表评论
        </p>

        <div v-if="post.comments?.length" class="comment-list">
          <div v-for="c in post.comments" :key="c.id" class="comment-item">
            <div class="comment-header">
              <strong>{{ c.username }}</strong>
              <span>{{ new Date(c.created_at).toLocaleDateString() }}</span>
            </div>
            <p>{{ c.content }}</p>
          </div>
        </div>
        <p v-else class="state">暂无评论</p>
      </section>
    </article>
  </div>
</template>

<style scoped>
.post-detail { max-width: 700px; margin: 0 auto; }
.state { text-align: center; padding: 2rem; color: #888; }
.error { color: #d32f2f; }
h1 { font-size: 1.8rem; margin-bottom: 0.5rem; }
.meta {
  display: flex;
  gap: 0.6rem;
  color: #999;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}
.tags { display: flex; gap: 0.3rem; }
.tag {
  background: #f0f0f0;
  padding: 0.1rem 0.5rem;
  border-radius: 3px;
  font-size: 0.8rem;
  color: #555;
}
.content {
  line-height: 1.8;
  font-size: 1rem;
}
/* Markdown content styles */
.content :deep(pre) {
  background: #1e1e1e;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
}
.content :deep(code) {
  font-family: "Fira Code", monospace;
  font-size: 0.9rem;
}
.content :deep(p > code) {
  background: #f5f5f5;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
}
.content :deep(blockquote) {
  border-left: 3px solid #1976d2;
  margin-left: 0;
  padding-left: 1rem;
  color: #666;
}
.content :deep(img) { max-width: 100%; }
.content :deep(table) {
  border-collapse: collapse;
  width: 100%;
}
.content :deep(th), .content :deep(td) {
  border: 1px solid #ddd;
  padding: 0.5rem;
  text-align: left;
}

.comments { margin-top: 3rem; border-top: 1px solid #eee; padding-top: 1.5rem; }
.comments h3 { margin-bottom: 1rem; }
.login-hint { font-size: 0.9rem; color: #888; }
.comment-form textarea {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: vertical;
  font-size: 0.95rem;
  box-sizing: border-box;
}
.comment-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.5rem;
}
.comment-actions button {
  padding: 0.5rem 1.2rem;
  background: #333;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.comment-actions button:disabled { opacity: 0.5; }
.comment-list { margin-top: 1rem; }
.comment-item {
  padding: 0.8rem 0;
  border-bottom: 1px solid #f0f0f0;
}
.comment-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  margin-bottom: 0.3rem;
}
.comment-header span { color: #999; font-size: 0.8rem; }
.comment-item p { margin: 0; font-size: 0.95rem; color: #444; }
</style>
