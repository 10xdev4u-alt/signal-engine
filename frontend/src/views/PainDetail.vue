<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ cluster.cluster?.label }}</h1>
        <p class="page-subtitle">
          <span style="color: var(--accent)">{{ cluster.cluster?.mentions }} mentions</span> ·
          desperation {{ cluster.cluster?.desperation_score?.toFixed(1) }}
        </p>
      </div>
      <router-link to="/pains" class="btn">← all pains</router-link>
    </div>
    <div class="card">
      <h3 style="margin-bottom: 1rem;">Evidence</h3>
      <div v-if="cluster.members?.length">
        <blockquote v-for="(m, i) in cluster.members" :key="i" class="quote" style="margin: 0.5rem 0; padding: 0.5rem 1rem; border-left: 3px solid var(--accent); background: var(--bg-tertiary); border-radius: 0 6px 6px 0;">
          {{ m.quote }}
          <div v-if="m.permalink" style="margin-top: 0.5rem; font-size: 0.8rem;"><a :href="m.permalink" target="_blank" rel="noreferrer">{{ m.ref_type }} ↗</a></div>
        </blockquote>
      </div>
      <p v-else class="empty">No stored quotes for this cluster.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
const route = useRoute()
const cluster = ref({})
onMounted(async () => {
  const { data } = await axios.get(`/api/pains/${route.params.id}`)
  cluster.value = data
})
</script>
