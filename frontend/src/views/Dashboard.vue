<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Daily digest</h1>
        <p class="page-subtitle">What hurt today, which phrases are new, and who is actively asking.</p>
      </div>
    </div>
    <div v-if="digest?.html" class="card digest-md" v-html="digest.html"></div>
    <div v-else class="card empty">
      <h3>No digest yet</h3>
      <p>Run <code>./run.sh fetch analyze digest</code> to generate the morning brief.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
const digest = ref(null)
onMounted(async () => {
  const { data } = await axios.get('/api/digest')
  digest.value = data
})
</script>

<style scoped>
.digest-md :deep(h1) { font-size: 1.375rem; margin: 0 0 1rem; }
.digest-md :deep(h2) { font-size: 1.125rem; margin: 1.5rem 0 0.75rem; color: var(--accent); }
.digest-md :deep(h3) { font-size: 1rem; margin: 1rem 0 0.5rem; }
.digest-md :deep(p) { margin: 0 0 0.75rem; }
.digest-md :deep(ol), .digest-md :deep(ul) { margin: 0 0 0.75rem; padding-left: 1.4rem; }
.digest-md :deep(li) { margin-bottom: 0.25rem; }
.digest-md :deep(blockquote) {
  border-left: 3px solid var(--accent); margin: 0.5rem 0; padding: 0.25rem 1rem;
  color: var(--fg-secondary); background: var(--bg-tertiary);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}
.digest-md :deep(code) { background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 4px; padding: 0 0.3rem; font-size: 0.85em; }
.digest-md :deep(strong) { color: var(--fg-primary); }
</style>
