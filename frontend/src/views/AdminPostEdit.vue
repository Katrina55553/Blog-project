<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Editor } from "@bytemd/vue-next";
import gfm from "@bytemd/plugin-gfm";
import highlight from "@bytemd/plugin-highlight";
import zhHans from "bytemd/locales/zh_Hans.json";
import { createPost, updatePost, getPostById } from "../api/post";
import "bytemd/dist/index.css";
import "highlight.js/styles/github.css";

const route = useRoute();
const router = useRouter();

const isEdit = computed(() => !!route.params.id);

const title = ref("");
const slug = ref("");
const content = ref("");
const summary = ref("");
const tagsInput = ref("");

const loading = ref(false);
const saving = ref(false);
const error = ref("");

const plugins = [gfm(), highlight()];

const handleChange = (v) => {
  content.value = v;
};

function autoSlug() {
  if (!isEdit.value) {
    slug.value = title.value
      .toLowerCase()
      .replace(/\s+/g, "-")
      .replace(/[^a-z0-9-]/g, "");
  }
}

watch(title, () => {
  if (!isEdit.value) autoSlug();
});

async function fetchPost() {
  loading.value = true;
  try {
    const res = await getPostById(route.params.id);
    const p = res.data;
    title.value = p.title;
    slug.value = p.slug;
    content.value = p.content;
    summary.value = p.summary;
    tagsInput.value = (p.tags || []).join(", ");
  } catch {
    error.value = "加载文章失败";
  } finally {
    loading.value = false;
  }
}

async function handleSave() {
  error.value = "";
  if (!title.value || !content.value) {
    error.value = "标题和内容不能为空";
    return;
  }
  const tags = tagsInput.value
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);

  saving.value = true;
  try {
    let res;
    if (isEdit.value) {
      res = await updatePost(route.params.id, {
        title: title.value,
        slug: slug.value,
        content: content.value,
        summary: summary.value,
        tags,
      });
    } else {
      res = await createPost({
        title: title.value,
        slug: slug.value,
        content: content.value,
        summary: summary.value,
        tags,
      });
    }
    router.push(`/post/${res.data.slug}`);
  } catch (e) {
    error.value = e.response?.data?.detail || "保存失败";
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  if (isEdit.value) fetchPost();
});
</script>

<template>
  <div class="admin-post-edit">
    <h1>{{ isEdit ? "编辑文章" : "写新文章" }}</h1>

    <div v-if="loading" class="skeleton-edit">
      <div class="skeleton-line w-60 h-28"></div>
      <div class="skeleton-line w-30 h-14"></div>
      <div class="skeleton-line w-100 h-200"></div>
    </div>

    <form v-else @submit.prevent="handleSave" class="editor-form">
      <div v-if="error" class="error">{{ error }}</div>

      <label>
        <span>标题</span>
        <input v-model="title" type="text" @input="autoSlug" placeholder="文章标题" />
      </label>

      <label>
        <span>Slug</span>
        <input v-model="slug" type="text" placeholder="url-friendly-slug" />
      </label>

      <label>
        <span>标签（逗号分隔）</span>
        <input v-model="tagsInput" type="text" placeholder="Python, FastAPI" />
      </label>

      <label>
        <span>摘要</span>
        <input v-model="summary" type="text" placeholder="简短描述" />
      </label>

      <Editor
        :value="content"
        :plugins="plugins"
        :locale="zhHans"
        mode="split"
        placeholder="写点东西..."
        @change="handleChange"
      />

      <div class="form-actions">
        <button type="submit" :disabled="saving" class="btn-save">
          {{ saving ? "保存中..." : "发布" }}
        </button>
        <router-link to="/admin" class="btn-cancel">取消</router-link>
      </div>
    </form>
  </div>
</template>

<style scoped>
.admin-post-edit {
  max-width: 900px;
  margin: 0 auto;
}
h1 {
  margin-bottom: 1.5rem;
  color: var(--color-text);
}
.error {
  color: var(--color-danger);
  background: var(--color-danger-bg);
  padding: 0.5rem;
  border-radius: var(--radius);
  margin-bottom: 1rem;
}
.editor-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
label span {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}
input, textarea {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 1rem;
  box-sizing: border-box;
  font-family: inherit;
  background: var(--color-bg);
  color: var(--color-text);
}
textarea { resize: vertical; }

.form-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-top: 0.5rem;
}
.btn-save {
  padding: 0.6rem 2rem;
  background: var(--color-text);
  color: var(--color-bg);
  border: none;
  border-radius: var(--radius);
  font-size: 1rem;
  cursor: pointer;
}
.btn-save:disabled { opacity: 0.5; }
.btn-cancel { color: var(--color-text-muted); text-decoration: none; font-size: 0.95rem; }
.btn-cancel:hover { color: var(--color-text); }

:deep(.bytemd) {
  height: 600px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}

/* Skeleton for edit page */
.skeleton-edit {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem 0;
}
.skeleton-edit .skeleton-line {
  background: var(--color-border);
  border-radius: 4px;
  animation: shimmer 1.5s infinite;
}
.skeleton-edit .skeleton-line.w-60 { width: 60%; }
.skeleton-edit .skeleton-line.w-30 { width: 30%; }
.skeleton-edit .skeleton-line.w-100 { width: 100%; }
.skeleton-edit .skeleton-line.h-28 { height: 28px; }
.skeleton-edit .skeleton-line.h-14 { height: 14px; }
.skeleton-edit .skeleton-line.h-200 { height: 200px; }
@keyframes shimmer {
  0% { opacity: 0.4; }
  50% { opacity: 0.8; }
  100% { opacity: 0.4; }
}
</style>

<style>
/* ===== ByteMD editor dark mode ===== */
[data-theme="dark"] .bytemd {
  --bytemd-bg: #1a1a2e;
  --bytemd-border: #333355;
  --bytemd-text: #e0e0e0;
  --bytemd-text-secondary: #aaaaaa;
  background: var(--bytemd-bg);
  border-color: var(--bytemd-border);
  color: var(--bytemd-text);
}

[data-theme="dark"] .bytemd-toolbar {
  background: #16213e;
  border-bottom-color: #333355;
}

[data-theme="dark"] .bytemd-toolbar-icon {
  color: #aaaaaa;
}
[data-theme="dark"] .bytemd-toolbar-icon:hover {
  background: #2a2a44;
  color: #e0e0e0;
}

[data-theme="dark"] .bytemd-editor {
  background: #0d1117;
}

[data-theme="dark"] .bytemd-preview {
  background: #1a1a2e;
  color: #e0e0e0;
}

[data-theme="dark"] .bytemd-status {
  background: #16213e;
  border-top-color: #333355;
  color: #aaaaaa;
}

[data-theme="dark"] .bytemd-split .bytemd-split-bar {
  background: #333355;
}

[data-theme="dark"] .CodeMirror {
  background: #0d1117;
  color: #e0e0e0;
  border-right-color: #333355;
}

[data-theme="dark"] .CodeMirror-gutters {
  background: #0d1117;
  border-right-color: #333355;
}

[data-theme="dark"] .CodeMirror-linenumber {
  color: #555;
}

[data-theme="dark"] .CodeMirror-cursor {
  border-left-color: #e0e0e0;
}

[data-theme="dark"] .CodeMirror-selected {
  background: rgba(100, 180, 255, 0.15);
}

[data-theme="dark"] .CodeMirror-activeline-background {
  background: rgba(255, 255, 255, 0.04);
}

/* ===== highlight.js dark mode overrides (github-dark colors) ===== */
[data-theme="dark"] .hljs {
  color: #c9d1d9;
  background: #0d1117;
}
[data-theme="dark"] .hljs-doctag,
[data-theme="dark"] .hljs-keyword,
[data-theme="dark"] .hljs-meta .hljs-keyword,
[data-theme="dark"] .hljs-template-tag,
[data-theme="dark"] .hljs-template-variable,
[data-theme="dark"] .hljs-type,
[data-theme="dark"] .hljs-variable.language_ {
  color: #ff7b72;
}
[data-theme="dark"] .hljs-title,
[data-theme="dark"] .hljs-title.class_,
[data-theme="dark"] .hljs-title.class_.inherited__,
[data-theme="dark"] .hljs-title.function_ {
  color: #d2a8ff;
}
[data-theme="dark"] .hljs-attr,
[data-theme="dark"] .hljs-attribute,
[data-theme="dark"] .hljs-literal,
[data-theme="dark"] .hljs-meta,
[data-theme="dark"] .hljs-number,
[data-theme="dark"] .hljs-operator,
[data-theme="dark"] .hljs-variable,
[data-theme="dark"] .hljs-selector-attr,
[data-theme="dark"] .hljs-selector-class,
[data-theme="dark"] .hljs-selector-id {
  color: #79c0ff;
}
[data-theme="dark"] .hljs-regexp,
[data-theme="dark"] .hljs-string,
[data-theme="dark"] .hljs-meta .hljs-string {
  color: #a5d6ff;
}
[data-theme="dark"] .hljs-built_in,
[data-theme="dark"] .hljs-symbol {
  color: #ffa657;
}
[data-theme="dark"] .hljs-comment,
[data-theme="dark"] .hljs-code,
[data-theme="dark"] .hljs-formula {
  color: #8b949e;
}
[data-theme="dark"] .hljs-name,
[data-theme="dark"] .hljs-quote,
[data-theme="dark"] .hljs-selector-tag,
[data-theme="dark"] .hljs-selector-pseudo {
  color: #7ee787;
}
[data-theme="dark"] .hljs-subst {
  color: #c9d1d9;
}
[data-theme="dark"] .hljs-section {
  color: #79c0ff;
}
[data-theme="dark"] .hljs-bullet {
  color: #a5d6ff;
}
[data-theme="dark"] .hljs-emphasis {
  color: #c9d1d9;
  font-style: italic;
}
[data-theme="dark"] .hljs-strong {
  color: #c9d1d9;
  font-weight: bold;
}
[data-theme="dark"] .hljs-addition {
  color: #7ee787;
  background: rgba(46, 160, 67, 0.15);
}
[data-theme="dark"] .hljs-deletion {
  color: #ff7b72;
  background: rgba(248, 81, 73, 0.15);
}
[data-theme="dark"] .hljs-link {
  color: #79c0ff;
  text-decoration: underline;
}
</style>
