<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();

const username = ref("");
const password = ref("");
const confirm = ref("");
const error = ref("");
const loading = ref(false);

async function handleRegister() {
  error.value = "";
  if (!username.value || !password.value) {
    error.value = "请填写用户名和密码";
    return;
  }
  if (password.value !== confirm.value) {
    error.value = "两次密码不一致";
    return;
  }
  loading.value = true;
  try {
    await auth.register(username.value, password.value);
    router.push("/login");
  } catch (e) {
    error.value = e.response?.data?.detail || "注册失败";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="form-page">
    <h1>注册</h1>
    <form @submit.prevent="handleRegister">
      <div v-if="error" class="error">{{ error }}</div>
      <label>
        <span>用户名</span>
        <input v-model="username" type="text" autocomplete="username" />
      </label>
      <label>
        <span>密码</span>
        <input v-model="password" type="password" autocomplete="new-password" />
      </label>
      <label>
        <span>确认密码</span>
        <input v-model="confirm" type="password" autocomplete="new-password" />
      </label>
      <button type="submit" :disabled="loading">
        {{ loading ? "注册中..." : "注册" }}
      </button>
    </form>
    <p class="switch">
      已有账号？<router-link to="/login">去登录</router-link>
    </p>
  </div>
</template>

<style scoped>
.form-page {
  max-width: 360px;
  margin: 4rem auto;
}
h1 {
  text-align: center;
  margin-bottom: 1.5rem;
  color: var(--color-text);
}
form {
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
input {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 1rem;
  box-sizing: border-box;
  background: var(--color-bg);
  color: var(--color-text);
}
button {
  padding: 0.7rem;
  background: var(--color-text);
  color: var(--color-bg);
  border: none;
  border-radius: var(--radius);
  font-size: 1rem;
  cursor: pointer;
}
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.error {
  color: var(--color-danger);
  background: var(--color-danger-bg);
  padding: 0.5rem;
  border-radius: var(--radius);
  font-size: 0.9rem;
}
.switch {
  text-align: center;
  margin-top: 1rem;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}
</style>
