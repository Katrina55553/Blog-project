<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { marked } from "marked";
import { createPost, updatePost, getPostBySlug, getPostById } from "../api/post";

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

const preview = computed(() => {
  if (!content.value) return "";
  return marked(content.value);
});

function autoSlug() {
  if (!isEdit.value) {
    slug.value = title.value
      .toLowerCase()
      .replace(/\s+/g, "-")
      .replace(/[^a-z0-9-]/g, "");
  }
}

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

    <div v-if="loading" class="state">加载中...</div>

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

      <div class="editor-panes">
        <div class="pane">
          <span class="pane-label">Markdown</span>
          <textarea
            v-model="content"
            placeholder="写点东西..."
            rows="16"
          ></textarea>
        </div>
        <div class="pane">
          <span class="pane-label">预览</span>
          <div class="preview" v-html="preview"></div>
        </div>
      </div>

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
.admin-post-edit { max-width: 900px; margin: 0 auto; }
h1 { margin-bottom: 1.5rem; }
.state { text-align: center; padding: 2rem; color: #888; }
.error { color: #d32f2f; background: #fdecea; padding: 0.5rem; border-radius: 4px; margin-bottom: 1rem; }
.editor-form { display: flex; flex-direction: column; gap: 1rem; }
label span {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
  color: #555;
}
input, textarea {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  box-sizing: border-box;
  font-family: inherit;
}
textarea { resize: vertical; }
.editor-panes {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
.pane { display: flex; flex-direction: column; }
.pane-label {
  font-size: 0.85rem;
  color: #888;
  margin-bottom: 0.25rem;
}
.pane textarea {
  flex: 1;
  font-family: "Fira Code", "Consolas", monospace;
  font-size: 0.9rem;
  line-height: 1.6;
}
.preview {
  flex: 1;
  border: 1px solid #eee;
  border-radius: 4px;
  padding: 0.8rem;
  overflow-y: auto;
  line-height: 1.7;
  font-size: 0.95rem;
}
.preview :deep(pre) { background: #1e1e1e; padding: 0.8rem; border-radius: 4px; overflow-x: auto; }
.preview :deep(code) { font-size: 0.85rem; }
.preview :deep(p > code) { background: #f5f5f5; padding: 0.1rem 0.3rem; border-radius: 3px; }
.preview :deep(blockquote) { border-left: 3px solid #1976d2; margin-left: 0; padding-left: 0.8rem; color: #666; }

.form-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-top: 0.5rem;
}
.btn-save {
  padding: 0.6rem 2rem;
  background: #333;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
}
.btn-save:disabled { opacity: 0.5; }
.btn-cancel { color: #888; text-decoration: none; font-size: 0.95rem; }
.btn-cancel:hover { color: #333; }
</style>
