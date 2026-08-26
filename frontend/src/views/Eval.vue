<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Eval queue</h1>
        <p class="page-subtitle">Mark each flagged item as <em>real problem</em> or <em>noise</em>.</p>
      </div>
    </div>
    <div class="kpi-row">
      <div class="kpi">
        <div class="kpi-label">Sample</div>
        <div class="kpi-value">{{ eval_data.sample_size || 0 }}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Marked</div>
        <div class="kpi-value">{{ eval_data.evaluated || 0 }}</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Precision@10</div>
        <div class="kpi-value" :style="{ color: pctColor }">{{ (eval_data.p10 || 0).toFixed(2) }}</div>
      </div>
    </div>
    <div v-if="eval_data.flagged?.length" class="card">
      <div v-for="f in eval_data.flagged" :key="f.ref_id" class="intent-card" style="display: flex; align-items: center; gap: 1rem; padding: 0.75rem 1rem; margin-bottom: 0.5rem; background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 8px;">
        <div class="intent-score" style="width: 36px; height: 36px; border-radius: 50%; background: var(--accent); color: white; display: flex; align-items: center; justify-content: center; font-weight: 700;">{{ f.score }}</div>
        <div style="flex: 1; min-width: 0;">
          <div style="font-size: 0.9rem;">{{ f.snippet || f.ref_id }}</div>
          <div style="font-size: 0.8rem; color: var(--fg-tertiary);">{{ f.scored_at?.slice(0, 10) }}</div>
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button class="btn" style="background: var(--success); color: white; border: none;" @click="mark(f.ref_type, f.ref_id, 'real_problem')">Real</button>
          <button class="btn" style="background: var(--danger); color: white; border: none;" @click="mark(f.ref_type, f.ref_id, 'noise')">Noise</button>
        </div>
      </div>
    </div>
    <div v-else class="card empty">
      <h3>No high-intent items yet</h3>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
const eval_data = ref({})
const pctColor = computed(() => {
  const p = (eval_data.value.p10 || 0) * 100
  return p >= 70 ? 'var(--success)' : p < 50 ? 'var(--danger)' : 'var(--warning)'
})
const load = async () => {
  const { data } = await axios.get('/api/eval')
  eval_data.value = data
}
const mark = async (ref_type, ref_id, verdict) => {
  await axios.post(`/api/eval/${ref_type}/${ref_id}?verdict=${verdict}`)
  load()
}
onMounted(load)
</script>
