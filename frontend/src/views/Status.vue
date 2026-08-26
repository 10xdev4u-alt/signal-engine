<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Collection status</h1>
        <p class="page-subtitle">Per-subreddit health and recent fetch problems.</p>
      </div>
    </div>
    <div v-if="status.subs?.length" class="card">
      <h3 style="margin-bottom: 1rem;">Subreddits</h3>
      <table>
        <thead>
          <tr><th>Subreddit</th><th class="num">Posts</th><th class="num">Comments</th></tr>
        </thead>
        <tbody>
          <tr v-for="s in status.subs" :key="s.name">
            <td><router-link :to="`/profile/${s.name}`">r/{{ s.name }}</router-link></td>
            <td class="num">{{ s.posts }}</td>
            <td class="num">{{ s.comments }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="card empty">
      <h3>No subreddits registered yet</h3>
    </div>
    <div class="card" style="margin-top: 1.5rem;">
      <h3 style="margin-bottom: 1rem;">Recent fetch problems</h3>
      <div v-if="status.recent_errors?.length">
        <table>
          <thead>
            <tr><th>When</th><th>Status</th><th>URL</th></tr>
          </thead>
          <tbody>
            <tr v-for="(e, i) in status.recent_errors" :key="i">
              <td style="color: var(--fg-tertiary)">{{ e.ts }}</td>
              <td>{{ e.http_status }}</td>
              <td style="color: var(--fg-tertiary)">{{ e.url }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="empty">Clean log — no failed fetches recorded.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
const status = ref({})
onMounted(async () => {
  const { data } = await axios.get('/api/status')
  status.value = data
})
</script>
