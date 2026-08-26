<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">r/{{ route.params.sub }}</h1>
        <p class="page-subtitle">A living community profile: distinctive phrases, active hours, and the language people use when they are stuck.</p>
      </div>
      <button class="btn" @click="buildProfile"><i data-lucide="refresh-cw" style="width:16px;height:16px"></i> Rebuild</button>
    </div>
    <div v-if="profile.snapshots?.length" class="card">
      <h3 style="margin-bottom: 1rem;">Latest snapshot</h3>
      <pre style="white-space: pre-wrap; font-family: inherit; margin: 0; line-height: 1.7;">{{ profile.snapshots[0].snapshot_md }}</pre>
    </div>
    <div v-else class="card empty">
      <h3>No profile yet</h3>
      <p>Run <code>./run.sh analyze</code> first, then build.</p>
      <button class="btn btn-primary" style="margin-top: 1rem;" @click="buildProfile">Build profile</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
const route = useRoute()
const profile = ref({})
const load = async () => {
  const { data } = await axios.get(`/api/profile/${route.params.sub}`)
  profile.value = data
}
const buildProfile = async () => {
  const { data } = await axios.get(`/api/profile/${route.params.sub}?build=true`)
  profile.value = data
}
onMounted(load)
</script>
