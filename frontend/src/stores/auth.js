import { defineStore } from "pinia";
import { ref } from "vue";
import { login as apiLogin, register as apiRegister, getMe } from "../api/auth";

export const useAuthStore = defineStore("auth", () => {
  const user = ref(null);
  const token = ref(localStorage.getItem("token") || "");

  function setAuth(t, u) {
    token.value = t;
    user.value = u;
    localStorage.setItem("token", t);
    localStorage.setItem("user", JSON.stringify(u));
  }

  function clearAuth() {
    token.value = "";
    user.value = null;
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  }

  async function register(username, password) {
    const res = await apiRegister(username, password);
    return res.data;
  }

  async function login(username, password) {
    const res = await apiLogin(username, password);
    setAuth(res.data.access_token, { username });
    return res.data;
  }

  async function restoreUser() {
    if (token.value) {
      try {
        const res = await getMe();
        user.value = res.data;
      } catch {
        clearAuth();
      }
    }
  }

  function logout() {
    clearAuth();
  }

  return { user, token, setAuth, clearAuth, register, login, restoreUser, logout };
});
