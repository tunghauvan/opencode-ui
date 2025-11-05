<template>
  <div class="model-selector">
    <div class="flex items-center gap-2">
      <label class="text-sm font-medium text-gray-700">Model:</label>
      <select 
        v-model="selectedProvider" 
        @change="onProviderChange"
        class="px-3 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option v-for="provider in providers" :key="provider.id" :value="provider.id">
          {{ provider.name }}
        </option>
      </select>
      
      <select 
        v-model="selectedModel" 
        @change="onModelChange"
        class="px-3 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option v-for="(model, modelId) in currentModels" :key="modelId" :value="modelId">
          {{ model.name }}
        </option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()

const selectedProvider = ref(chatStore.selectedProvider)
const selectedModel = ref(chatStore.selectedModel)

const providers = computed(() => {
  if (!chatStore.availableModels || !chatStore.availableModels.providers) return []
  return chatStore.availableModels.providers
})

const currentModels = computed(() => {
  if (!chatStore.availableModels || !selectedProvider.value) return {}
  const provider = providers.value.find(p => p.id === selectedProvider.value)
  return provider?.models || {}
})

function onProviderChange() {
  // Select first model of the new provider
  const models = currentModels.value
  const firstModelId = Object.keys(models)[0]
  if (firstModelId) {
    selectedModel.value = firstModelId
    chatStore.setModel(selectedProvider.value, selectedModel.value)
  }
}

function onModelChange() {
  chatStore.setModel(selectedProvider.value, selectedModel.value)
}

// Sync with store changes
watch(() => chatStore.selectedProvider, (newVal) => {
  selectedProvider.value = newVal
})

watch(() => chatStore.selectedModel, (newVal) => {
  selectedModel.value = newVal
})

// Load models on mount
onMounted(async () => {
  if (!chatStore.availableModels) {
    await chatStore.fetchModels()
  }
})
</script>

<style scoped>
.model-selector {
  padding: 0.5rem 0;
}
</style>
