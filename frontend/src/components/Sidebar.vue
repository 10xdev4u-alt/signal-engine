<template>
  <aside class="sidebar">
    <div class="brand">
      <span class="brand-mark">SE</span>
      <div>
        <div class="brand-name">signal-engine</div>
        <div class="brand-meta">v0.2.0 · local</div>
      </div>
    </div>
    <nav class="nav">
      <div class="nav-section">
        <div class="nav-title">Today</div>
        <router-link to="/dashboard" class="nav-link" active-class="active">
          <Newspaper :size="16" /> Digest
        </router-link>
        <router-link to="/pains" class="nav-link" active-class="active">
          <Flame :size="16" /> Pain clusters
        </router-link>
        <router-link to="/eval" class="nav-link" active-class="active">
          <CheckCircle :size="16" /> Eval queue
        </router-link>
      </div>
      <div class="nav-section">
        <div class="nav-title">Explore</div>
        <router-link to="/search" class="nav-link" active-class="active">
          <Search :size="16" /> Search
        </router-link>
        <router-link to="/status" class="nav-link" active-class="active">
          <Activity :size="16" /> Status
        </router-link>
      </div>
    </nav>
    <div class="sidebar-footer">
      <a class="nav-link" href="https://github.com/10xdev4u-alt/signal-engine" target="_blank" rel="noreferrer">
        <ExternalLink :size="16" /> Source
      </a>
      <button class="theme-toggle" @click="toggleTheme">
        <Moon v-if="theme === 'dark'" :size="16" />
        <Sun v-else :size="16" />
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Newspaper, Flame, CheckCircle, Search, Activity, ExternalLink, Moon, Sun } from 'lucide-vue-next'

const theme = ref('dark')
onMounted(() => {
  theme.value = localStorage.getItem('theme') || 'dark'
  document.documentElement.setAttribute('data-theme', theme.value)
})
const toggleTheme = () => {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  document.documentElement.setAttribute('data-theme', theme.value)
  localStorage.setItem('theme', theme.value)
}
</script>

<style scoped>
.sidebar {
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  position: sticky;
  top: 0;
  height: 100vh;
}
.brand { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem; margin-bottom: 0.5rem; }
.brand-mark {
  width: 32px; height: 32px; border-radius: 8px;
  background: var(--accent); color: white;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.8rem;
}
.brand-name { font-weight: 600; font-size: 0.9rem; }
.brand-meta { font-size: 0.7rem; color: var(--fg-quaternary); }
.nav { display: flex; flex-direction: column; gap: 2px; }
.nav-section { display: flex; flex-direction: column; gap: 2px; }
.nav-title {
  font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--fg-quaternary); margin-top: 1rem; padding: 0.25rem 0.75rem;
}
.nav-link {
  display: flex; align-items: center; gap: 0.75rem;
  color: var(--fg-secondary); padding: 0.5rem 0.75rem;
  border-radius: 6px; font-size: 0.85rem; font-weight: 500;
  text-decoration: none; transition: all 0.15s;
}
.nav-link:hover { background: var(--bg-tertiary); color: var(--fg-primary); }
.nav-link.active { background: var(--accent-subtle); color: var(--accent); font-weight: 600; }
.sidebar-footer { margin-top: auto; display: flex; flex-direction: column; gap: 0.5rem; }
.theme-toggle {
  background: var(--bg-tertiary); border: 1px solid var(--border); color: var(--fg-primary);
  border-radius: 6px; padding: 0.5rem; cursor: pointer; min-height: 36px;
  display: inline-flex; align-items: center; justify-content: center;
}
.theme-toggle:hover { border-color: var(--accent); }
@media (max-width: 880px) { .sidebar { display: none; } }
</style>
