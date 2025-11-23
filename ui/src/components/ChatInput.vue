<template>
  <div class="max-w-4xl mx-auto mb-6 px-4">
    <div class="relative bg-white rounded-2xl shadow-xl border border-gray-100 transition-all duration-300 hover:shadow-2xl ring-1 ring-black/5">
      <!-- Main Input Area -->
      <div class="p-4 pb-2">
        <textarea
          ref="textareaRef"
          v-model="localValue"
          @keydown.enter.exact="handleEnter"
          @input="adjustHeight"
          :disabled="disabled"
          placeholder="Type your message..."
          class="w-full px-0 py-2 border-0 bg-transparent text-gray-800 placeholder-gray-400 focus:ring-0 resize-none min-h-[52px] max-h-[200px] text-base leading-relaxed"
          :class="{ 'opacity-50 cursor-not-allowed': disabled }"
          rows="1"
        ></textarea>
      </div>

      <!-- Footer Controls -->
      <div class="flex items-center justify-between px-3 pb-3 pt-1">
        
        <!-- Left: Selectors -->
        <div class="flex items-center gap-2">
          <!-- Provider Selector -->
          <div class="relative group">
            <select
              v-model="selectedProvider"
              @change="onProviderChange"
              class="appearance-none pl-3 pr-8 py-1.5 rounded-full text-xs font-semibold bg-gray-50 text-gray-600 border border-gray-200 hover:border-primary-300 hover:bg-primary-50 hover:text-primary-700 transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary-100"
              :disabled="disabled"
            >
              <option v-for="provider in providers" :key="provider.id" :value="provider.id">
                {{ provider.name }}
              </option>
            </select>
            <svg class="w-3 h-3 absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none group-hover:text-primary-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
          
          <!-- Model Selector -->
          <div class="relative group">
            <select
              v-model="selectedModel"
              @change="onModelChange"
              class="appearance-none pl-3 pr-8 py-1.5 rounded-full text-xs font-semibold bg-gray-50 text-gray-600 border border-gray-200 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-100"
              :disabled="disabled"
            >
              <option v-for="(model, modelId) in currentModels" :key="modelId" :value="modelId">
                {{ model.name }}
              </option>
            </select>
            <svg class="w-3 h-3 absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none group-hover:text-blue-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>

        <!-- Right: Send Button -->
        <div class="flex items-center gap-2">
           <span class="text-xs text-gray-400 hidden sm:inline-block mr-2">
            Press <kbd class="font-sans px-1 py-0.5 bg-gray-100 border border-gray-200 rounded text-[10px]">Enter</kbd> to send
          </span>
          <button
            @click="handleSend"
            :disabled="disabled || !localValue.trim()"
            class="flex items-center justify-center w-10 h-10 rounded-full bg-primary-600 text-white shadow-md hover:bg-primary-700 hover:shadow-lg hover:scale-105 active:scale-95 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none disabled:hover:scale-100"
          >
            <svg class="w-5 h-5 translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7" />
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
