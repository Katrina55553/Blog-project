<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { getNotifications, markRead, markAllRead } from "../api/notification";

const router = useRouter();

const items = ref([]);
const total = ref(0);
const pages = ref(0);
const page = ref(1);
const loading = ref(true);
const error = ref("");
const size = 20;

async function fetchNotifications() {
  loading.value = true;
  error.value = "";
  try {
    const res = await getNotifications(page.value, size);
    items.value = res.data.items;
    total.value = res.data.total;
    pages.value = res.data.pages;
  } catch {
    error.value = "加载失败";
  } finally {
    loading.value = false;
  }
}

async function goTopic(notif) {
  if (!notif.is_read) {
    await markRead(notif.id);
    notif.is_read = true;
  }
  if (notif.topic_id) {
    router.push(`/topic/${notif.topic_id}`);
  }
}

async function handleMarkAll() {
  await markAllRead();
  items.value.forEach((n) => (n.is_read = true));
}

function goPage(p) {
  page.value = p;
}

function formatTime(t) {
  if (!t) return "";
  const diff = Date.now() - new Date(t).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "刚刚";
  if (mins < 60) return `${mins}分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}小时前`;
  return new Date(t).toLocaleDateString();
}

onMounted(fetchNotifications);
</script>

<template>
  <div class="notifications">
    <div class="notif-header">
      <h1>通知</h1>
      <button v-if="items.some((n) => !n.is_read)" class="btn-mark-all" @click="handleMarkAll">
        全部已读
      </button>
    </div>

    <div v-if="loading" class="state">加载中...</div>
    <div v-else-if="error" class="state error">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="fetchNotifications">重试</button>
    </div>
    <div v-else-if="items.length === 0" class="state">暂无通知</div>

    <div v-else class="notif-list">
      <div
        v-for="n in items"
        :key="n.id"
        class="notif-item"
        :class="{ unread: !n.is_read }"
        @click="goTopic(n)"
      >
        <span class="notif-type">💬</span>
        <span class="notif-text">有人回复了你的帖子</span>
        <span class="notif-time">{{ formatTime(n.created_at) }}</span>
      </div>

      <div v-if="pages > 1" class="pagination">
        <button :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
        <span v-for="p in pages" :key="p">
          <button :class="{ current: p === page }" @click="goPage(p)">{{ p }}</button>
        </span>
        <button :disabled="page >= pages" @click="goPage(pages)">下一页</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notifications { max-width: 700px; margin: 0 auto; }
.notif-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}
.notif-header h1 { margin: 0; color: var(--color-text); }
.btn-mark-all {
  padding: 0.4rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
  color: var(--color-text);
  cursor: pointer;
  font-size: 0.85rem;
}
.btn-mark-all:hover { border-color: var(--color-primary); color: var(--color-primary); }

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

.notif-list { display: flex; flex-direction: column; gap: 0.3rem; }
.notif-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.9rem 1.2rem;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius);
  cursor: pointer;
  transition: background 0.2s;
}
.notif-item:hover { background: var(--color-card-hover); }
.notif-item.unread {
  border-left: 3px solid var(--color-primary);
  background: var(--color-card-hover);
}
.notif-type { font-size: 1.1rem; flex-shrink: 0; }
.notif-text { flex: 1; font-size: 0.95rem; color: var(--color-text); }
.notif-time { font-size: 0.8rem; color: var(--color-text-muted); flex-shrink: 0; }

.pagination {
  display: flex;
  justify-content: center;
  gap: 0.4rem;
  margin-top: 2rem;
}
.pagination button {
  padding: 0.4rem 0.8rem;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text);
  border-radius: 4px;
  cursor: pointer;
}
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.pagination button.current { background: var(--color-text); color: var(--color-bg); border-color: var(--color-text); }
</style>
