<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { updateMe } from "../api/auth";

const router = useRouter();
const auth = useAuthStore();

const avatar = ref("");
const bio = ref("");
const githubUrl = ref("");
const saving = ref(false);
const error = ref("");
const success = ref(false);

onMounted(() => {
  if (auth.user) {
    avatar.value = auth.user.avatar || "";
    bio.value = auth.user.bio || "";
    githubUrl.value = auth.user.github_url || "";
  }
});

async function handleSave() {
  error.value = "";
  success.value = false;
  saving.value = true;
  try {
    const res = await updateMe({
      avatar: avatar.value || null,
      bio: bio.value || null,
      github_url: githubUrl.value || null,
    });
    auth.user = res.data;
    localStorage.setItem("user", JSON.stringify(res.data));
    success.value = true;
  } catch (e) {
    error.value = e.response?.data?.detail || "保存失败";
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="profile-edit">
    <h1>编辑资料</h1>

    <form @submit.prevent="handleSave" class="edit-form">
      <div v-if="success" class="success">保存成功</div>
      <div v-if="error" class="error">{{ error }}</div>

      <label>
        <span>头像 URL</span>
        <input v-model="avatar" type="text" placeholder="https://..." />
      </label>

      <label>
        <span>个人简介</span>
        <textarea v-model="bio" rows="3" placeholder="介绍一下自己..."></textarea>
      </label>

      <label>
        <span>GitHub</span>
        <input v-model="githubUrl" type="text" placeholder="https://github.com/..." />
      </label>

      <div class="form-actions">
        <button type="submit" :disabled="saving" class="btn-save">
          {{ saving ? "保存中..." : "保存" }}
        </button>
        <router-link to="/" class="btn-cancel">取消</router-link>
      </div>
    </form>
  </div>
</template>

<style scoped>
.profile-edit { max-width: 480px; margin: 0 auto; }
h1 { margin-bottom: 1.5rem; color: var(--color-text); }
.edit-form { display: flex; flex-direction: column; gap: 1rem; }
.success {
  color: #2e7d32;
  background: #e8f5e9;
  padding: 0.5rem;
  border-radius: var(--radius);
  font-size: 0.9rem;
}
.error {
  color: var(--color-danger);
  background: var(--color-danger-bg);
  padding: 0.5rem;
  border-radius: var(--radius);
  font-size: 0.9rem;
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
</style>
