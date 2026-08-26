<template>
  <div class="app">
    <Sidebar />
    <main class="main">
      <Topbar />
      <div class="content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue'
import Topbar from './components/Topbar.vue'
</script>

<style scoped>
.app {
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 100vh;
}
.main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.content {
  padding: 2rem;
  max-width: 1200px;
  width: 100%;
}
@media (max-width: 880px) {
  .app { grid-template-columns: 1fr; }
}
</style>
