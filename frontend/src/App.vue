<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "./stores/auth";

const router = useRouter();
const auth = useAuthStore();

const isDark = ref(false);

function initTheme() {
  const saved = localStorage.getItem("theme");
  if (saved === "dark" || (!saved && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
    isDark.value = true;
    document.documentElement.setAttribute("data-theme", "dark");
  }
}

function toggleTheme() {
  isDark.value = !isDark.value;
  const theme = isDark.value ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", isDark.value ? "dark" : "");
  localStorage.setItem("theme", theme);
}

onMounted(() => {
  initTheme();
  auth.restoreUser();
});

function logout() {
  auth.logout();
  router.push("/");
}
</script>

<template>
  <header class="navbar">
    <router-link to="/" class="brand">My Blog</router-link>
    <nav>
      <router-link to="/">首页</router-link>
      <template v-if="auth.user">
        <router-link to="/admin">后台</router-link>
        <router-link to="/admin/posts/new">写文章</router-link>
        <span class="user">{{ auth.user.username }}</span>
        <a href="#" @click.prevent="logout">退出</a>
      </template>
      <template v-else>
        <router-link to="/login">登录</router-link>
        <router-link to="/register">注册</router-link>
      </template>
      <button class="theme-toggle" @click="toggleTheme" :title="isDark ? '切换亮色' : '切换暗色'">
        {{ isDark ? '🌙' : '☀️' }}
      </button>
    </nav>
  </header>
  <main class="container">
    <router-view />
  </main>
</template>

<style scoped>
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  height: 56px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
  transition: background 0.3s, border-color 0.3s;
}
.brand {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--color-text);
  text-decoration: none;
}
nav {
  display: flex;
  align-items: center;
  gap: 1rem;
}
nav a {
  color: var(--color-text-secondary);
  font-size: 0.95rem;
  text-decoration: none;
}
nav a:hover {
  color: var(--color-text);
}
.user {
  color: var(--color-text-muted);
  font-size: 0.9rem;
}
.theme-toggle {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 0.2rem 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
}
.container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 0 1rem;
}
</style>
