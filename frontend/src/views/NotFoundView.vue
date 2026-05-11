<template>
  <div class="not-found">
    <h1>404</h1>
    <p>页面未找到</p>
    <router-link to="/">返回首页</router-link>
  </div>
</template>

<style scoped>
.not-found {
  text-align: center;
  padding: 4rem 1rem;
}
h1 {
  font-size: 4rem;
  margin: 0;
  color: var(--color-text-muted);
}
p {
  color: var(--color-text-secondary);
  margin: 0.5rem 0 1.5rem;
}
</style>
