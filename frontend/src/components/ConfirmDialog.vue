<script setup>
import { useConfirmState } from "../composables/confirm";

const state = useConfirmState();

function handleConfirm() {
  state.resolve?.(true);
  state.visible = false;
}

function handleCancel() {
  state.resolve?.(false);
  state.visible = false;
}

function onKeydown(e) {
  if (e.key === "Escape") handleCancel();
}
</script>

<template>
  <Teleport to="body">
    <div v-if="state.visible" class="confirm-overlay" @click.self="handleCancel" @keydown="onKeydown">
      <div class="confirm-box">
        <p class="confirm-msg">{{ state.message }}</p>
        <div class="confirm-actions">
          <button class="btn-confirm" @click="handleConfirm">确认</button>
          <button class="btn-cancel" @click="handleCancel">取消</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style>
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.confirm-box {
  background: var(--color-bg);
  border-radius: var(--radius);
  padding: 2rem;
  min-width: 320px;
  max-width: 420px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}
.confirm-msg {
  margin: 0 0 1.5rem;
  font-size: 1rem;
  color: var(--color-text);
  line-height: 1.5;
}
.confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
}
.confirm-actions button {
  padding: 0.5rem 1.2rem;
  border-radius: var(--radius);
  font-size: 0.9rem;
  cursor: pointer;
}
.btn-confirm {
  background: var(--color-danger);
  color: #fff;
  border: none;
}
.btn-confirm:hover {
  opacity: 0.9;
}
.btn-cancel {
  background: none;
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
}
.btn-cancel:hover {
  border-color: var(--color-text);
  color: var(--color-text);
}
</style>
