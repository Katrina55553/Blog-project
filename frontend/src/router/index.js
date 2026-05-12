import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "home",
    component: () => import("../views/HomeView.vue"),
    meta: { title: "首页" },
  },
  {
    path: "/post/:slug",
    name: "post-detail",
    component: () => import("../views/PostDetailView.vue"),
    meta: { title: "文章" },
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
    path: "/admin",
    name: "admin-dashboard",
    component: () => import("../views/AdminDashboard.vue"),
    meta: { requiresAuth: true, title: "后台管理" },
  },
  {
    path: "/admin/posts/new",
    name: "admin-post-new",
    component: () => import("../views/AdminPostEdit.vue"),
    meta: { requiresAuth: true, title: "写文章" },
  },
  {
    path: "/admin/posts/:id/edit",
    name: "admin-post-edit",
    component: () => import("../views/AdminPostEdit.vue"),
    meta: { requiresAuth: true, title: "编辑文章" },
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
  document.title = to.meta.title ? `${to.meta.title} - My Blog` : "My Blog";
});

export default router;
