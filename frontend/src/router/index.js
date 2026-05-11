import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "home",
    component: () => import("../views/HomeView.vue"),
  },
  {
    path: "/post/:slug",
    name: "post-detail",
    component: () => import("../views/PostDetailView.vue"),
  },
  {
    path: "/login",
    name: "login",
    component: () => import("../views/LoginView.vue"),
  },
  {
    path: "/register",
    name: "register",
    component: () => import("../views/RegisterView.vue"),
  },
  {
    path: "/admin",
    name: "admin-dashboard",
    component: () => import("../views/AdminDashboard.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/admin/posts/new",
    name: "admin-post-new",
    component: () => import("../views/AdminPostEdit.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/admin/posts/:id/edit",
    name: "admin-post-edit",
    component: () => import("../views/AdminPostEdit.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: () => import("../views/NotFoundView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const token = localStorage.getItem("token");
  if (to.meta.requiresAuth && !token) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
});

export default router;
