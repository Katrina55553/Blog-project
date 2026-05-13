<script setup>
import { ref } from "vue";
import { showConfirm } from "../composables/confirm";
import { showToast } from "../composables/toast";
import { deleteComment } from "../api/comment";

const props = defineProps({
  comment: { type: Object, required: true },
  depth: { type: Number, default: 0 },
  auth: { type: Object, default: null },
});

const emit = defineEmits(["reply-created", "comment-deleted"]);

const showReplyForm = ref(false);
const replyText = ref("");

function handleSubmit() {
  if (!replyText.value.trim()) return;
  emit("reply-created", {
    parentId: props.comment.id,
    content: replyText.value,
  });
  replyText.value = "";
  showReplyForm.value = false;
}

function canDelete() {
  if (!props.auth) return false;
  return props.auth.id === props.comment.user_id || props.auth.is_admin;
}

async function handleDelete() {
  const ok = await showConfirm("确定删除这条评论吗？");
  if (!ok) return;
  try {
    await deleteComment(props.comment.id);
    showToast.success("评论已删除");
    emit("comment-deleted", props.comment.id);
  } catch (e) {
    showToast.error(e.response?.data?.detail || "删除失败");
  }
}
</script>

<template>
  <div class="comment-thread" :class="{ nested: depth > 0 }">
    <div class="comment-item">
      <div class="comment-header">
        <router-link :to="`/user/${comment.username}`" class="comment-author">{{ comment.username }}</router-link>
        <span>{{ new Date(comment.created_at).toLocaleDateString() }}</span>
      </div>
      <p class="comment-body">{{ comment.content }}</p>
      <div class="comment-actions">
        <button v-if="auth" class="btn-reply" @click="showReplyForm = !showReplyForm">回复</button>
        <button v-if="canDelete()" class="btn-delete" @click="handleDelete">删除</button>
      </div>

      <div v-if="showReplyForm" class="reply-form">
        <textarea
          v-model="replyText"
          placeholder="写下你的回复..."
          rows="2"
        ></textarea>
        <div class="reply-actions">
          <button class="btn-submit" @click="handleSubmit">提交</button>
          <button class="btn-cancel" @click="showReplyForm = false">取消</button>
        </div>
      </div>
    </div>

    <CommentItem
      v-for="reply in comment.replies"
      :key="reply.id"
      :comment="reply"
      :depth="depth + 1"
      :auth="auth"
      @reply-created="emit('reply-created', $event)"
      @comment-deleted="emit('comment-deleted', $event)"
    />
  </div>
</template>

<style scoped>
.comment-thread.nested {
  margin-left: 24px;
  border-left: 1px solid var(--color-border-light);
  padding-left: 12px;
}
.comment-item {
  padding: 0.8rem 0;
  border-bottom: 1px solid var(--color-border-light);
}
.comment-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  margin-bottom: 0.3rem;
}
.comment-author {
  color: var(--color-text);
  text-decoration: none;
  font-weight: 600;
}
.comment-author:hover { color: var(--color-primary); }
.comment-header span { color: var(--color-text-muted); font-size: 0.8rem; }
.comment-body { margin: 0; font-size: 0.95rem; color: var(--color-text-secondary); }

.comment-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.3rem;
}
.btn-reply {
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-size: 0.8rem;
  cursor: pointer;
  padding: 0.2rem 0;
}
.btn-reply:hover { color: var(--color-primary); }
.btn-delete {
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-size: 0.8rem;
  cursor: pointer;
  padding: 0.2rem 0;
}
.btn-delete:hover { color: var(--color-danger); }

.reply-form { margin-top: 0.6rem; }
.reply-form textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  resize: vertical;
  font-size: 0.9rem;
  box-sizing: border-box;
  background: var(--color-bg);
  color: var(--color-text);
}
.reply-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.4rem;
}
.btn-submit {
  padding: 0.3rem 1rem;
  background: var(--color-text);
  color: var(--color-bg);
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 0.85rem;
}
.btn-cancel {
  padding: 0.3rem 1rem;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}
.btn-cancel:hover { border-color: var(--color-text-muted); }
</style>
