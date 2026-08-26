<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Pain clusters</h1>
        <p class="page-subtitle">Recurring problems grouped by shared language, ranked by desperation × mention count.</p>
      </div>
      <span class="tag">{{ pains.clusters?.length || 0 }} clusters</span>
    </div>
    <div v-if="pains.clusters?.length" class="card">
      <table>
        <thead>
          <tr><th>Cluster</th><th class="num">Mentions</th><th class="num">Desperation</th><th>Seen</th></tr>
        </thead>
        <tbody>
          <tr v-for="c in pains.clusters" :key="c.id">
            <td><router-link :to="`/pains/${c.id}`">{{ c.label }}</router-link></td>
            <td class="num">{{ c.mention_count }}</td>
            <td class="num" style="color: var(--accent)">{{ c.desperation_score?.toFixed(1) }}</td>
            <td class="num" style="color: var(--fg-tertiary)">{{ c.first_seen || '?' }} → {{ c.last_seen || '?' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="card empty">
      <h3>Nothing collected yet</h3>
      <p>Run <code>./run.sh fetch</code> then <code>./run.sh analyze</code> to cluster pain points.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
const pains = ref({})
onMounted(async () => {
  const { data } = await axios.get('/api/pains')
  pains.value = data
})
</script>
