<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { marked } from "marked";
import { createTopic, updateTopic, getTopicForEdit } from "../api/topic";
import { showToast } from "../composables/toast";

const route = useRoute();
const router = useRouter();

const isEdit = computed(() => !!route.params.id);
const title = ref("");
const content = ref("");
const loading = ref(false);
const pageLoading = ref(false);
const error = ref("");

const previewHtml = computed(() => {
  if (!content.value) return "<em>暂无内容</em>";
  return marked(content.value);
});

async function init() {
  if (isEdit.value) {
    pageLoading.value = true;
    try {
      const res = await getTopicForEdit(route.params.id);
      title.value = res.data.title;
      content.value = res.data.content;
    } catch {
      error.value = "加载失败";
    } finally {
      pageLoading.value = false;
    }
  }
}

async function handleSubmit() {
  if (!title.value.trim()) {
    error.value = "标题不能为空";
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    if (isEdit.value) {
      const res = await updateTopic(route.params.id, {
        title: title.value.trim(),
        content: content.value,
      });
      router.push(`/topic/${res.data.id}`);
      showToast.success("更新成功");
    } else {
      const res = await createTopic({
        title: title.value.trim(),
        content: content.value,
      });
      router.push(`/topic/${res.data.id}`);
      showToast.success("发帖成功");
    }
  } catch (e) {
    error.value = e.response?.data?.detail || "操作失败";
  } finally {
    loading.value = false;
  }
}

onMounted(init);
</script>

<template>
  <div class="topic-edit">
    <h1>{{ isEdit ? "编辑帖子" : "发布新帖" }}</h1>

    <div v-if="pageLoading" class="skeleton-form">
      <div class="skeleton-line w-100 h-40"></div>
      <div class="skeleton-line w-100 h-200"></div>
    </div>

    <form v-else @submit.prevent="handleSubmit" class="edit-form">
      <div class="field">
        <label for="title">标题</label>
        <input
          id="title"
          v-model="title"
          type="text"
          placeholder="输入帖子标题..."
          maxlength="200"
        />
      </div>

      <div class="field">
        <label for="content">内容 (Markdown)</label>
        <div class="editor-wrap">
          <textarea
            id="content"
            v-model="content"
            placeholder="支持 Markdown 语法..."
            rows="18"
          ></textarea>
          <div class="preview" v-html="previewHtml"></div>
        </div>
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <div class="actions">
        <button type="submit" :disabled="loading">
          {{ loading ? "提交中..." : (isEdit ? "更新" : "发布") }}
        </button>
        <button type="button" class="btn-cancel" @click="router.back()">取消</button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.topic-edit { max-width: 700px; margin: 0 auto; }
h1 { margin-bottom: 1.5rem; color: var(--color-text); }

.skeleton-form { display: flex; flex-direction: column; gap: 1rem; }
.skeleton-line {
  background: var(--color-border);
  border-radius: 4px;
  animation: shimmer 1.5s infinite;
}
.skeleton-line.w-100 { width: 100%; }
.skeleton-line.h-40 { height: 40px; }
.skeleton-line.h-200 { height: 200px; }
@keyframes shimmer {
  0% { opacity: 0.4; }
  50% { opacity: 0.8; }
  100% { opacity: 0.4; }
}

.field { margin-bottom: 1.2rem; }
.field label {
  display: block;
  margin-bottom: 0.4rem;
  font-weight: 600;
  color: var(--color-text);
  font-size: 0.95rem;
}
.field input {
  width: 100%;
  padding: 0.6rem 0.8rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 1rem;
  box-sizing: border-box;
  background: var(--color-bg);
  color: var(--color-text);
}
.field input:focus { border-color: var(--color-primary); outline: none; }

.editor-wrap { display: flex; gap: 1rem; }
.editor-wrap textarea,
.editor-wrap .preview {
  flex: 1;
  min-height: 360px;
  padding: 0.6rem 0.8rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 0.95rem;
  line-height: 1.6;
  background: var(--color-bg);
  color: var(--color-text);
  resize: vertical;
}
.editor-wrap textarea:focus { border-color: var(--color-primary); outline: none; }
.editor-wrap .preview {
  overflow-y: auto;
  background: var(--color-bg-secondary);
}

.error { color: var(--color-danger); font-size: 0.9rem; }
.actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}
.actions button {
  padding: 0.6rem 1.5rem;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 0.95rem;
}
.actions button[type="submit"] {
  background: var(--color-text);
  color: var(--color-bg);
}
.actions button[type="submit"]:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-cancel {
  background: var(--color-bg);
  color: var(--color-text);
  border: 1px solid var(--color-border) !important;
}
.btn-cancel:hover { border-color: var(--color-text) !important; }

@media (max-width: 640px) {
  .editor-wrap { flex-direction: column; }
}
</style>
