<template>
  <div class="max-w-4xl mx-auto">
    <div class="flex gap-2">
      <textarea
        ref="textareaRef"
        v-model="localValue"
        @keydown.enter.exact="handleEnter"
        @input="adjustHeight"
        :disabled="disabled"
        placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
        class="flex-1 input resize-none min-h-[44px] max-h-[200px]"
        rows="1"
      ></textarea>
      
      <select
        v-model="selectedProvider"
        @change="onProviderChange"
        class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
        :disabled="disabled"
      >
        <option v-for="provider in providers" :key="provider.id" :value="provider.id">
          {{ provider.name }}
        </option>
      </select>
      
      <select
        v-model="selectedModel"
        @change="onModelChange"
        class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
        :disabled="disabled"
      >
        <option v-for="(model, modelId) in currentModels" :key="modelId" :value="modelId">
          {{ model.name }}
        </option>
      </select>
      
      <button
        @click="handleSend"
        :disabled="disabled || !localValue.trim()"
        class="btn btn-primary px-6 self-end"
        :class="{ 'opacity-50 cursor-not-allowed': disabled || !localValue.trim() }"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { useChatStore } from '../stores/chat'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'send'])

const chatStore = useChatStore()
const localValue = ref(props.modelValue)
const textareaRef = ref(null)
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

watch(() => props.modelValue, (newValue) => {
  localValue.value = newValue
})

watch(localValue, (newValue) => {
  emit('update:modelValue', newValue)
})

watch(() => chatStore.selectedProvider, (newVal) => {
  selectedProvider.value = newVal
})

watch(() => chatStore.selectedModel, (newVal) => {
  selectedModel.value = newVal
})

watch(() => chatStore.selectedProvider, () => {
  // If provider changes, select first model
  const models = currentModels.value
  const firstModelId = Object.keys(models)[0]
  if (firstModelId) {
    selectedModel.value = firstModelId
    chatStore.setModel(chatStore.selectedProvider, selectedModel.value)
  }
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

function handleEnter(event) {
  if (event.shiftKey) {
    // Allow new line with Shift+Enter
    return
  }
  
  event.preventDefault()
  handleSend()
}

function handleSend() {
  if (props.disabled || !localValue.value.trim()) return
  emit('send')
}

function adjustHeight() {
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto'
      textareaRef.value.style.height = textareaRef.value.scrollHeight + 'px'
    }
  })
}
</script>
