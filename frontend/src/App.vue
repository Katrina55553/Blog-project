<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "./stores/auth";

const router = useRouter();
const auth = useAuthStore();

const isDark = ref(false);
const menuOpen = ref(false);

function initTheme() {
  const saved = localStorage.getItem("theme");
  if (saved === "dark" || (!saved && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
    isDark.value = true;
    document.documentElement.setAttribute("data-theme", "dark");
  }
}

function toggleTheme() {
  isDark.value = !isDark.value;
  document.documentElement.setAttribute("data-theme", isDark.value ? "dark" : "");
  localStorage.setItem("theme", isDark.value ? "dark" : "light");
}

function closeMenu() {
  menuOpen.value = false;
}

onMounted(() => {
  initTheme();
  auth.restoreUser();
});

function logout() {
  auth.logout();
  closeMenu();
  router.push("/");
}
</script>

<template>
  <header class="navbar">
    <router-link to="/" class="brand" @click="closeMenu">My Blog</router-link>
    <button class="hamburger" @click="menuOpen = !menuOpen" :aria-label="menuOpen ? '关闭菜单' : '打开菜单'">
      <span></span><span></span><span></span>
    </button>
    <nav :class="{ open: menuOpen }">
      <router-link to="/" @click="closeMenu">首页</router-link>
      <template v-if="auth.user">
        <router-link to="/admin" @click="closeMenu">后台</router-link>
        <router-link to="/admin/posts/new" @click="closeMenu">写文章</router-link>
        <span class="user">{{ auth.user.username }}</span>
        <a href="#" @click.prevent="logout">退出</a>
      </template>
      <template v-else>
        <router-link to="/login" @click="closeMenu">登录</router-link>
        <router-link to="/register" @click="closeMenu">注册</router-link>
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
  padding: 0 1rem;
  height: 56px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
  transition: background 0.3s, border-color 0.3s;
  position: sticky;
  top: 0;
  z-index: 100;
}
.brand {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--color-text);
  text-decoration: none;
  flex-shrink: 0;
}

/* Hamburger */
.hamburger {
  display: none;
  flex-direction: column;
  gap: 4px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
}
.hamburger span {
  display: block;
  width: 22px;
  height: 2px;
  background: var(--color-text);
  transition: transform 0.2s;
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
  white-space: nowrap;
}
nav a:hover { color: var(--color-text); }
.user {
  color: var(--color-text-muted);
  font-size: 0.9rem;
  white-space: nowrap;
}
.theme-toggle {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 0.2rem 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  flex-shrink: 0;
}

.container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 0 1rem;
}

/* Mobile */
@media (max-width: 640px) {
  .hamburger { display: flex; }
  nav {
    display: none;
    position: absolute;
    top: 56px;
    left: 0;
    right: 0;
    flex-direction: column;
    align-items: flex-start;
    gap: 0;
    background: var(--color-bg);
    border-bottom: 1px solid var(--color-border);
    padding: 0.5rem 1rem;
    box-shadow: var(--shadow-md);
  }
  nav.open { display: flex; }
  nav a, nav .user {
    padding: 0.7rem 0;
    width: 100%;
    border-bottom: 1px solid var(--color-border-light);
  }
  .theme-toggle { margin-top: 0.5rem; }
}
</style>
