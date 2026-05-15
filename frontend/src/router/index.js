import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "home",
    component: () => import("../views/HomeView.vue"),
    meta: { title: "首页" },
  },
  {
    path: "/topic/new",
    name: "topic-new",
    component: () => import("../views/TopicEditView.vue"),
    meta: { requiresAuth: true, title: "发帖" },
  },
  {
    path: "/topic/:id",
    name: "topic-detail",
    component: () => import("../views/TopicDetailView.vue"),
    meta: { title: "帖子" },
  },
  {
    path: "/topic/:id/edit",
    name: "topic-edit",
    component: () => import("../views/TopicEditView.vue"),
    meta: { requiresAuth: true, title: "编辑" },
  },
  {
    path: "/notifications",
    name: "notifications",
    component: () => import("../views/NotificationsView.vue"),
    meta: { requiresAuth: true, title: "通知" },
  },
  {
    path: "/login",
    name: "login",
    component: () => import("../views/LoginView.vue"),
    meta: { title: "登录" },
  },
  {
    path: "/register",
    name: "register",
    component: () => import("../views/RegisterView.vue"),
    meta: { title: "注册" },
  },
  {
    path: "/profile/edit",
    name: "profile-edit",
    component: () => import("../views/ProfileEdit.vue"),
    meta: { requiresAuth: true, title: "编辑资料" },
  },
  {
    path: "/user/:username",
    name: "user-profile",
    component: () => import("../views/UserProfile.vue"),
    meta: { title: "用户主页" },
  },
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: () => import("../views/NotFoundView.vue"),
    meta: { title: "404" },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach((to) => {
  const token = localStorage.getItem("token");
  if (to.meta.requiresAuth && !token) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
});

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} - Forum` : "Forum";
});

export default router;
