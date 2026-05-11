<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const username = ref("");

onMounted(() => {
  const stored = localStorage.getItem("user");
  if (stored) {
    try {
      username.value = JSON.parse(stored).username;
    } catch {
      username.value = "";
    }
  }
});

function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  username.value = "";
  router.push("/");
}
</script>

<template>
  <header class="navbar">
    <router-link to="/" class="brand">My Blog</router-link>
    <nav>
      <router-link to="/">首页</router-link>
      <template v-if="username">
        <router-link to="/admin">后台</router-link>
        <router-link to="/admin/posts/new">写文章</router-link>
        <span class="user">{{ username }}</span>
        <a href="#" @click.prevent="logout">退出</a>
      </template>
      <template v-else>
        <router-link to="/login">登录</router-link>
        <router-link to="/register">注册</router-link>
      </template>
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
  border-bottom: 1px solid #e5e5e5;
  background: #fff;
}
.brand {
  font-size: 1.2rem;
  font-weight: 700;
  text-decoration: none;
  color: #333;
}
nav {
  display: flex;
  align-items: center;
  gap: 1rem;
}
nav a {
  text-decoration: none;
  color: #555;
  font-size: 0.95rem;
}
nav a:hover {
  color: #111;
}
.user {
  color: #888;
  font-size: 0.9rem;
}
.container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 0 1rem;
}
</style>
