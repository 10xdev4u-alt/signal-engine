<template>
  <header class="topbar">
    <nav class="crumbs">
      <router-link to="/dashboard">signal-engine</router-link>
      <span class="sep">/</span>
      <span>{{ pageTitle }}</span>
    </nav>
    <div class="topbar-actions">
      <router-link to="/search" class="search-pill">
        <SearchIcon :size="14" />
        <span>Search…</span>
        <kbd>⌘K</kbd>
      </router-link>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { SearchIcon } from 'lucide-vue-next'

const route = useRoute()
const titles = {
  dashboard: 'Digest',
  pains: 'Pain clusters',
  'pain-detail': 'Cluster',
  eval: 'Eval queue',
  search: 'Search',
  status: 'Status',
  profile: 'Profile',
}
const pageTitle = computed(() => titles[route.name] || 'Signal Engine')
</script>

<style scoped>
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  gap: 1rem; padding: 0 2rem; height: 60px;
  border-bottom: 1px solid var(--border); background: var(--bg-primary);
  position: sticky; top: 0; z-index: 50;
}
.crumbs { color: var(--fg-tertiary); font-size: 0.85rem; display: flex; align-items: center; gap: 0.5rem; }
.crumbs a { color: var(--fg-secondary); text-decoration: none; }
.crumbs a:hover { color: var(--accent); }
.sep { opacity: 0.4; }
.search-pill {
  display: inline-flex; align-items: center; gap: 0.5rem;
  background: var(--bg-tertiary); border: 1px solid var(--border);
  border-radius: 999px; padding: 0.5rem 1rem;
  color: var(--fg-quaternary); font-size: 0.8rem; min-height: 36px; text-decoration: none;
}
.search-pill:hover { border-color: var(--accent); color: var(--fg-primary); }
</style>
