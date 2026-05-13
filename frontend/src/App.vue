<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "./stores/auth";
import AppToast from "./components/AppToast.vue";
import BackToTop from "./components/BackToTop.vue";
import ConfirmDialog from "./components/ConfirmDialog.vue";

const router = useRouter();
const auth = useAuthStore();

const isDark = ref(false);
const menuOpen = ref(false);
const navRef = ref(null);
const userMenuOpen = ref(false);
const userMenuRef = ref(null);

function onDocClick(e) {
  if (menuOpen.value && navRef.value && !navRef.value.contains(e.target)) {
    closeMenu();
  }
  if (userMenuOpen.value && userMenuRef.value && !userMenuRef.value.contains(e.target)) {
    userMenuOpen.value = false;
  }
}

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

function userInitial() {
  return auth.user?.username?.[0]?.toUpperCase() || "?";
}

function goProfile() {
  userMenuOpen.value = false;
  router.push("/profile/edit");
}

function logout() {
  auth.logout();
  closeMenu();
  userMenuOpen.value = false;
  router.push("/");
}

onMounted(() => {
  initTheme();
  auth.restoreUser();
  document.addEventListener("click", onDocClick);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", onDocClick);
});
</script>

<template>
  <header class="navbar">
    <router-link to="/" class="brand" @click="closeMenu">My Blog</router-link>

    <button class="hamburger" @click="menuOpen = !menuOpen" :aria-label="menuOpen ? '关闭菜单' : '打开菜单'">
      <span></span><span></span><span></span>
    </button>

    <nav ref="navRef" :class="{ open: menuOpen }">
      <router-link to="/" @click="closeMenu">首页</router-link>

      <template v-if="auth.user">
        <router-link to="/admin" @click="closeMenu">后台</router-link>
        <router-link to="/admin/posts/new" @click="closeMenu">写文章</router-link>
      </template>
      <template v-else>
        <router-link to="/login" @click="closeMenu">登录</router-link>
        <router-link to="/register" @click="closeMenu">注册</router-link>
      </template>

      <!-- User avatar + dropdown -->
      <div v-if="auth.user" ref="userMenuRef" class="user-menu">
        <button class="avatar-btn" @click="userMenuOpen = !userMenuOpen" :aria-label="'用户菜单'">
          <img v-if="auth.user.avatar" :src="auth.user.avatar" class="avatar-img" />
          <span v-else class="avatar-text">{{ userInitial() }}</span>
        </button>
        <div v-if="userMenuOpen" class="dropdown">
          <button class="dropdown-item" @click="goProfile">编辑信息</button>
          <button class="dropdown-item logout" @click="logout">退出账号</button>
        </div>
      </div>

      <button class="theme-toggle" @click="toggleTheme" :aria-label="isDark ? '切换亮色' : '切换暗色'">
        {{ isDark ? '🌙' : '☀️' }}
      </button>

      <a
        href="https://github.com/Katrina55553/Blog-project"
        target="_blank"
        rel="noopener noreferrer"
        class="github-link"
        :aria-label="'GitHub'"
      >
        <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor">
          <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
        </svg>
      </a>
    </nav>
  </header>
  <main class="container">
    <router-view />
  </main>
  <BackToTop />
  <AppToast />
  <ConfirmDialog />
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
  gap: 1.2rem;
}
nav > a {
  color: var(--color-text-secondary);
  font-size: 0.95rem;
  text-decoration: none;
  white-space: nowrap;
}
nav > a:hover { color: var(--color-text); }

/* GitHub link */
.github-link {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  padding: 0.35rem;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  transition: border-color 0.2s, color 0.2s;
}
.github-link:hover {
  border-color: var(--color-text);
  color: var(--color-text);
}

/* Theme toggle */
.theme-toggle {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  padding: 0.35rem;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.2s;
}
.theme-toggle:hover { border-color: var(--color-text); }

/* User avatar + dropdown */
.user-menu {
  position: relative;
  flex-shrink: 0;
}
.avatar-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 2px solid var(--color-border);
  background: var(--color-primary);
  cursor: pointer;
  padding: 0;
  overflow: hidden;
  transition: border-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.avatar-btn:hover { border-color: var(--color-text); }
.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}
.avatar-text {
  color: #fff;
  font-weight: 700;
  font-size: 0.9rem;
  user-select: none;
}

.dropdown {
  position: absolute;
  top: 42px;
  right: 0;
  min-width: 140px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-md);
  z-index: 200;
  overflow: hidden;
}
.dropdown-item {
  display: block;
  width: 100%;
  padding: 0.7rem 1rem;
  border: none;
  background: none;
  color: var(--color-text);
  font-size: 0.9rem;
  text-align: left;
  cursor: pointer;
  white-space: nowrap;
}
.dropdown-item:hover { background: var(--color-card-hover); }
.dropdown-item.logout {
  border-top: 1px solid var(--color-border-light);
  color: var(--color-text-muted);
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
    align-items: stretch;
    gap: 0;
    background: var(--color-bg);
    border-bottom: 1px solid var(--color-border);
    box-shadow: var(--shadow-md);
  }
  nav.open { display: flex; }
  nav > a {
    padding: 0.8rem 1.5rem;
    border-bottom: 1px solid var(--color-border-light);
  }
  .theme-toggle,
  .github-link {
    align-self: flex-end;
    margin: 0.5rem 1.5rem;
  }
  .user-menu {
    padding: 0.5rem 1.5rem 0.8rem;
  }
  .dropdown {
    left: 1.5rem;
    right: auto;
  }
}
</style>
