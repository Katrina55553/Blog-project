import { reactive } from "vue";

const state = reactive({
  visible: false,
  message: "",
  resolve: null,
});

export function showConfirm(message) {
  return new Promise((resolve) => {
    state.message = message;
    state.visible = true;
    state.resolve = resolve;
  });
}

export function useConfirmState() {
  return state;
}
