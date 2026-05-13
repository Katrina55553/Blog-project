import { reactive } from "vue";

const state = reactive({
  toasts: [],
  _id: 0,
});

export function showToast(message, type = "info", duration = 3000) {
  const id = ++state._id;
  state.toasts.push({ id, message, type });
  if (duration > 0) {
    setTimeout(() => {
      const idx = state.toasts.findIndex((t) => t.id === id);
      if (idx > -1) state.toasts.splice(idx, 1);
    }, duration);
  }
}

showToast.success = (msg, d) => showToast(msg, "success", d);
showToast.error = (msg, d) => showToast(msg, "error", d);
showToast.info = (msg, d) => showToast(msg, "info", d);

export function useToastState() {
  return state;
}
