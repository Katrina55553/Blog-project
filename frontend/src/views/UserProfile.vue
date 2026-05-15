<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { getUserProfile } from "../api/user";

const route = useRoute();
const profile = ref(null);
const loading = ref(true);
const error = ref("");

async function fetchProfile() {
  loading.value = true;
  error.value = "";
  try {
    const res = await getUserProfile(route.params.username);
    profile.value = res.data;
  } catch {
    error.value = "用户不存在或加载失败";
  } finally {
    loading.value = false;
  }
}

onMounted(fetchProfile);
</script>

<template>
  <div class="user-profile">
    <div v-if="loading" class="state">加载中...</div>
    <div v-else-if="error" class="state error">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="fetchProfile">重试</button>
    </div>
    <div v-else-if="profile">
      <div class="profile-header">
        <div class="avatar">{{ profile.username[0]?.toUpperCase() }}</div>
        <h1>{{ profile.username }}</h1>
        <div class="stats">
          <span>帖子 {{ profile.topic_count || 0 }}</span>
          <span>回复 {{ profile.comment_count || 0 }}</span>
        </div>
        <p v-if="profile.bio" class="bio">{{ profile.bio }}</p>
        <a v-if="profile.github_url" :href="profile.github_url" target="_blank" class="github-link">
          GitHub
        </a>
        <p class="join-date">加入于 {{ new Date(profile.created_at).toLocaleDateString() }}</p>
      </div>
      <section class="user-topics">
        <h2>帖子</h2>
        <div v-if="profile.topics?.length">
          <article v-for="t in profile.topics" :key="t.id" class="card">
            <router-link :to="`/topic/${t.id}`" class="card-link" :aria-label="t.title"></router-link>
            <h2 class="title">{{ t.title }}</h2>
            <div class="meta">
              <span>{{ new Date(t.created_at).toLocaleDateString() }}</span>
              <span>💬 {{ t.comment_count || 0 }}</span>
              <span>❤️ {{ t.likes_count || 0 }}</span>
            </div>
          </article>
        </div>
        <p v-else class="state">暂无帖子</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.user-profile { max-width: 700px; margin: 0 auto; }
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

.profile-header {
  text-align: center;
  padding: 2rem 0;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 2rem;
}
.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  font-size: 2rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
}
.stats {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  margin-bottom: 0.8rem;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}
h1 { color: var(--color-text); margin-bottom: 0.5rem; }
.bio { color: var(--color-text-secondary); max-width: 400px; margin: 0 auto 0.5rem; }
.github-link {
  display: inline-block;
  color: var(--color-primary);
  text-decoration: none;
  font-size: 0.9rem;
}
.join-date { color: var(--color-text-muted); font-size: 0.85rem; margin-top: 0.5rem; }

.user-topics h2 { margin-bottom: 1rem; color: var(--color-text); font-size: 1.2rem; }

.card {
  position: relative;
  padding: 1.2rem 1.4rem;
  margin-bottom: 0.6rem;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius);
  transition: background 0.2s;
}
.card:hover { background: var(--color-card-hover); }
.card-link {
  position: absolute;
  inset: 0;
  z-index: 1;
}
.title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.3rem 0;
}
.card:hover .title { color: var(--color-primary); }
.meta {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}
</style>
