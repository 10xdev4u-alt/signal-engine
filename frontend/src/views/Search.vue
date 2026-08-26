<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Search</h1>
        <p class="page-subtitle">Full-text search across every collected post and comment.</p>
      </div>
    </div>
    <div class="card">
      <form @submit.prevent="doSearch" style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
        <input v-model="q" placeholder='e.g. chargebacks or "dispute template"' style="flex: 1; min-width: 200px;">
        <input v-model="sub" placeholder="subreddit" style="width: 120px;">
        <select v-model="type">
          <option value="">all</option>
          <option value="post">posts</option>
          <option value="comment">comments</option>
        </select>
        <button type="submit" class="btn btn-primary">Search</button>
      </form>
    </div>
    <p style="color: var(--fg-tertiary); font-size: 0.8rem; margin-bottom: 1rem;">{{ indexed }} items indexed</p>
    <div v-if="results.length" class="card">
      <table>
        <thead>
          <tr><th>Type</th><th>Sub</th><th>Title</th><th>Match</th><th>Date</th></tr>
        </thead>
        <tbody>
          <tr v-for="(r, i) in results" :key="i">
            <td>{{ r.ref_type }}</td>
            <td>r/{{ r.subreddit }}</td>
            <td>{{ r.title }}</td>
            <td v-html="r.snip"></td>
            <td style="color: var(--fg-tertiary)">{{ r.created_utc?.slice(0, 10) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else-if="searched" class="card empty">
      <h3>No matches</h3>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
const q = ref('')
const sub = ref('')
const type = ref('')
const results = ref([])
const indexed = ref(0)
const searched = ref(false)
const doSearch = async () => {
  const { data } = await axios.get('/api/search', { params: { q: q.value, sub: sub.value, type: type.value } })
  results.value = data.results
  indexed.value = data.indexed
  searched.value = true
}
onMounted(async () => {
  const { data } = await axios.get('/api/search')
  indexed.value = data.indexed
})
</script>
