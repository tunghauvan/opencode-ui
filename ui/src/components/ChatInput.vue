<template>
  <div class="max-w-5xl mx-auto">
    <div class="card p-2 shadow-xl hover:shadow-2xl transition-all duration-300">
      <div class="flex gap-2 items-end">
        <div class="flex-1 relative">
          <textarea
            ref="textareaRef"
            v-model="localValue"
            @keydown.enter.exact="handleEnter"
            @input="adjustHeight"
            :disabled="disabled"
            placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
            class="w-full px-4 py-3 border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none min-h-[52px] max-h-[200px] bg-gray-50 hover:bg-white transition-colors"
            :class="{ 'opacity-50 cursor-not-allowed': disabled }"
            rows="1"
          ></textarea>
        </div>
        
        <div class="flex gap-2 items-end pb-1">
          <!-- Provider Selector -->
          <div class="relative">
            <select
              v-model="selectedProvider"
              @change="onProviderChange"
              class="px-3 py-3 pr-8 border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm font-medium bg-gradient-to-r from-primary-50 to-purple-50 text-gray-700 cursor-pointer hover:from-primary-100 hover:to-purple-100 transition-all appearance-none"
              :disabled="disabled"
            >
              <option v-for="provider in providers" :key="provider.id" :value="provider.id">
                {{ provider.name }}
              </option>
            </select>
            <svg class="w-4 h-4 absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
          
          <!-- Model Selector -->
          <div class="relative">
            <select
              v-model="selectedModel"
              @change="onModelChange"
              class="px-3 py-3 pr-8 border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm font-medium bg-gradient-to-r from-blue-50 to-cyan-50 text-gray-700 cursor-pointer hover:from-blue-100 hover:to-cyan-100 transition-all appearance-none"
              :disabled="disabled"
            >
              <option v-for="(model, modelId) in currentModels" :key="modelId" :value="modelId">
                {{ model.name }}
              </option>
            </select>
            <svg class="w-4 h-4 absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
          
          <!-- Send Button -->
          <button
            @click="handleSend"
            :disabled="disabled || !localValue.trim()"
            class="btn btn-primary px-5 py-3 self-end shadow-lg hover:shadow-xl group relative overflow-hidden"
            :class="{ 'opacity-50 cursor-not-allowed': disabled || !localValue.trim() }"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-purple-600 to-primary-600 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <svg class="w-5 h-5 relative z-10 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
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
