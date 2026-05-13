<script setup>
import { useToastState } from "../composables/toast";

const { toasts } = useToastState();

function remove(id) {
  const idx = toasts.findIndex((t) => t.id === id);
  if (idx > -1) toasts.splice(idx, 1);
}
</script>

<template>
  <Teleport to="body">
    <div class="toast-container" v-if="toasts.length">
      <TransitionGroup name="toast">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="toast-item"
          :class="t.type"
          @click="remove(t.id)"
        >
          {{ t.message }}
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style>
.toast-container {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}
.toast-item {
  pointer-events: auto;
  padding: 0.7rem 1.2rem;
  border-radius: var(--radius);
  font-size: 0.9rem;
  cursor: pointer;
  max-width: 320px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.toast-item.success {
  background: #16a34a;
  color: #fff;
}
.toast-item.error {
  background: #dc2626;
  color: #fff;
}
.toast-item.info {
  background: var(--color-text);
  color: var(--color-bg);
}

.toast-enter-active {
  transition: all 0.3s ease;
}
.toast-leave-active {
  transition: all 0.2s ease;
}
.toast-enter-from {
  transform: translateX(100%);
  opacity: 0;
}
.toast-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
