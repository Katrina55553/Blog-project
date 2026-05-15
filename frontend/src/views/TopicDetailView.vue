<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { marked } from "marked";
import hljs from "highlight.js";
import "highlight.js/styles/github-dark.css";
import { getTopicById, deleteTopic } from "../api/topic";
import { createComment } from "../api/comment";
import { likeTopic, unlikeTopic } from "../api/like";
import { useAuthStore } from "../stores/auth";
import CommentItem from "../components/CommentItem.vue";
import { showConfirm } from "../composables/confirm";
import { showToast } from "../composables/toast";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const topic = ref(null);
const loading = ref(true);
const error = ref("");

const commentText = ref("");
const commentLoading = ref(false);
const commentError = ref("");

const likeLoading = ref(false);

function isLiked() {
  return topic.value?.is_liked || false;
}

async function handleLike() {
  if (!auth.user) {
    router.push("/login");
    return;
  }
  likeLoading.value = true;
  try {
    if (isLiked()) {
      const res = await unlikeTopic(topic.value.id);
      topic.value.likes_count = res.data.likes_count;
      topic.value.is_liked = false;
    } else {
      const res = await likeTopic(topic.value.id);
      topic.value.likes_count = res.data.likes_count;
      topic.value.is_liked = true;
    }
  } catch {
    // ignore duplicate
  } finally {
    likeLoading.value = false;
  }
}

marked.setOptions({
  highlight(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value;
    }
    return hljs.highlightAuto(code).value;
  },
});

const isAuthor = computed(() =>
  auth.user && topic.value && auth.user.id === topic.value.author?.id,
);

const isAdmin = computed(() => auth.user?.is_admin);

const renderedContent = computed(() => {
  if (!topic.value?.content) return "";
  return marked(topic.value.content);
});

function handleEdit() {
  router.push(`/topic/${topic.value.id}/edit`);
}

async function handleDelete() {
  if (!await showConfirm("确定删除这个帖子？")) return;
  try {
    await deleteTopic(topic.value.id);
    router.push("/");
    showToast.success("删除成功");
  } catch {
    showToast.error("删除失败");
  }
}

async function fetchTopic() {
  loading.value = true;
  error.value = "";
  try {
    const res = await getTopicById(route.params.id);
    topic.value = res.data;
  } catch {
    error.value = "帖子不存在或加载失败";
  } finally {
    loading.value = false;
  }
}

async function handleComment(parentId = null, content = null) {
  const text = content || commentText.value;
  if (!text.trim()) return;
  commentLoading.value = true;
  commentError.value = "";
  try {
    await createComment(topic.value.id, text, parentId);
    if (!parentId) commentText.value = "";
    await fetchTopic();
  } catch (e) {
    commentError.value = e.response?.data?.detail || "评论失败";
  } finally {
    commentLoading.value = false;
  }
}

function handleReplyCreated({ parentId, content }) {
  handleComment(parentId, content);
}

async function handleCommentDeleted() {
  await fetchTopic();
}

onMounted(fetchTopic);
</script>

<template>
  <div class="topic-detail">
    <div v-if="loading" class="skeleton-detail">
      <div class="skeleton-line w-70 h-32"></div>
      <div class="skeleton-line w-40 h-14"></div>
      <div class="skeleton-line w-100 h-14"></div>
      <div class="skeleton-line w-100 h-14"></div>
      <div class="skeleton-line w-80 h-14"></div>
    </div>
    <div v-else-if="error" class="state error">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="fetchTopic">重试</button>
    </div>

    <article v-else>
      <h1>{{ topic.title }}</h1>
      <div class="meta">
        <router-link :to="`/user/${topic.author?.username}`" class="author">{{ topic.author?.username }}</router-link>
        <span>{{ new Date(topic.created_at).toLocaleDateString() }}</span>
        <span>👁️ {{ topic.view_count || 0 }}</span>
        <button
          class="like-btn"
          :class="{ liked: isLiked() }"
          :disabled="likeLoading"
          @click="handleLike"
        >
          {{ isLiked() ? '❤️' : '🤍' }} {{ topic.likes_count || 0 }}
        </button>
      </div>
      <div v-if="isAuthor || isAdmin" class="author-actions">
        <button class="btn-edit" @click="handleEdit">编辑</button>
        <button class="btn-delete" @click="handleDelete">删除</button>
      </div>
      <div class="content" v-html="renderedContent"></div>

      <section class="comments">
        <h3>回复 ({{ topic.comments?.length || 0 }})</h3>

        <div v-if="auth.user" class="comment-form">
          <textarea
            v-model="commentText"
            placeholder="写下你的回复..."
            rows="3"
          ></textarea>
          <div class="comment-actions">
            <button :disabled="commentLoading" @click="handleComment()">
              {{ commentLoading ? "提交中..." : "发表回复" }}
            </button>
            <span v-if="commentError" class="error">{{ commentError }}</span>
          </div>
        </div>
        <p v-else class="login-hint">
          <router-link to="/login">登录</router-link> 后发表回复
        </p>

        <div v-if="topic.comments?.length" class="comment-list">
          <CommentItem
            v-for="c in topic.comments"
            :key="c.id"
            :comment="c"
            :auth="auth.user"
            @reply-created="handleReplyCreated"
            @comment-deleted="handleCommentDeleted"
          />
        </div>
        <p v-else class="state">暂无回复</p>
      </section>
    </article>
  </div>
</template>

<style scoped>
.topic-detail { max-width: 700px; margin: 0 auto; }
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

.skeleton-detail {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.skeleton-line {
  background: var(--color-border);
  border-radius: 4px;
  animation: shimmer 1.5s infinite;
}
.skeleton-line.w-70 { width: 70%; }
.skeleton-line.w-40 { width: 40%; }
.skeleton-line.w-80 { width: 80%; }
.skeleton-line.w-100 { width: 100%; }
.skeleton-line.h-32 { height: 32px; }
.skeleton-line.h-14 { height: 14px; }
@keyframes shimmer {
  0% { opacity: 0.4; }
  50% { opacity: 0.8; }
  100% { opacity: 0.4; }
}

h1 { font-size: 1.8rem; margin-bottom: 0.5rem; color: var(--color-text); }
.meta {
  display: flex;
  gap: 0.8rem;
  color: var(--color-text-muted);
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  align-items: center;
}
.author { color: var(--color-text-muted); text-decoration: none; }
.author:hover { color: var(--color-primary); }
.like-btn {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 0.2rem 0.6rem;
  cursor: pointer;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}
.like-btn:hover { border-color: var(--color-danger); }
.like-btn.liked { border-color: var(--color-danger); }
.like-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.author-actions {
  margin-bottom: 1.5rem;
  display: flex;
  gap: 0.5rem;
}
.author-actions button {
  padding: 0.3rem 0.9rem;
  border: 1px solid var(--color-border);
  border-radius: 3px;
  background: var(--color-bg);
  color: var(--color-text);
  cursor: pointer;
  font-size: 0.85rem;
}
.btn-edit:hover { border-color: var(--color-primary); color: var(--color-primary); }
.btn-delete { color: var(--color-danger); }
.btn-delete:hover { background: var(--color-danger-bg); border-color: var(--color-danger); }

.content {
  line-height: 1.8;
  font-size: 1.05rem;
  color: var(--color-text);
}
.content :deep(pre) {
  background: var(--color-pre-bg);
  padding: 1rem;
  border-radius: var(--radius);
  overflow-x: auto;
}
.content :deep(code) {
  font-family: var(--font-mono);
  font-size: 0.9rem;
}
.content :deep(p > code) {
  background: var(--color-code-bg);
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
}
.content :deep(blockquote) {
  border-left: 3px solid var(--color-primary);
  margin-left: 0;
  padding-left: 1rem;
  color: var(--color-text-secondary);
}
.content :deep(img) { max-width: 100%; }
.content :deep(table) {
  border-collapse: collapse;
  width: 100%;
}
.content :deep(th), .content :deep(td) {
  border: 1px solid var(--color-border);
  padding: 0.5rem;
  text-align: left;
}

.comments {
  margin-top: 3rem;
  border-top: 1px solid var(--color-border);
  padding-top: 1.5rem;
}
.comments h3 { margin-bottom: 1rem; color: var(--color-text); }
.login-hint { font-size: 0.9rem; color: var(--color-text-muted); }
.comment-form textarea {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  resize: vertical;
  font-size: 0.95rem;
  box-sizing: border-box;
  background: var(--color-bg);
  color: var(--color-text);
}
.comment-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.5rem;
}
.comment-actions button {
  padding: 0.5rem 1.2rem;
  background: var(--color-text);
  color: var(--color-bg);
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
}
.comment-actions button:disabled { opacity: 0.5; }
.comment-list { margin-top: 1rem; }
</style>
