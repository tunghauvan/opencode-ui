<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center">
        <!-- Backdrop -->
        <div 
          class="absolute inset-0 bg-black bg-opacity-50"
          @click="close"
        ></div>
        
        <!-- Modal -->
        <div class="relative bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
          <!-- Header -->
          <div class="px-6 py-4 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-900">Select Model</h3>
              <button 
                @click="close"
                class="text-gray-400 hover:text-gray-600"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          
          <!-- Content -->
          <div class="px-6 py-4 overflow-y-auto max-h-[calc(80vh-140px)]">
            <div v-if="modelsLoading" class="text-center py-8">
              <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
              <p class="mt-2 text-gray-500">Loading models...</p>
            </div>
            
            <div v-else-if="!availableModels || !availableModels.providers" class="text-center py-8 text-gray-500">
              No models available
            </div>
            
            <div v-else class="space-y-6">
              <div v-for="provider in availableModels.providers" :key="provider.id" class="space-y-3">
                <h4 class="text-sm font-semibold text-gray-700 uppercase tracking-wider">
                  {{ provider.name }}
                </h4>
                
                <div class="grid grid-cols-1 gap-2">
                  <button
                    v-for="(model, modelId) in provider.models"
                    :key="modelId"
                    @click="selectModel(provider.id, modelId)"
                    class="text-left p-3 rounded-lg border transition-all"
                    :class="isSelected(provider.id, modelId) 
                      ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-200' 
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'"
                  >
                    <div class="flex items-center justify-between">
                      <div>
                        <div class="font-medium text-gray-900">{{ model.name }}</div>
                        <div class="text-xs text-gray-500 mt-1">
                          {{ modelId }}
                          <span v-if="model.knowledge" class="mx-1">•</span>
                          <span v-if="model.knowledge">Knowledge: {{ model.knowledge }}</span>
                        </div>
                      </div>
                      
                      <div v-if="isSelected(provider.id, modelId)" class="ml-2">
                        <svg class="w-5 h-5 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                        </svg>
                      </div>
                    </div>
                    
                    <div class="flex gap-2 mt-2 text-xs">
                      <span v-if="model.reasoning" class="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">Reasoning</span>
                      <span v-if="model.tool_call" class="px-2 py-0.5 bg-green-100 text-green-700 rounded">Tools</span>
                      <span v-if="model.attachment" class="px-2 py-0.5 bg-purple-100 text-purple-700 rounded">Attachments</span>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Footer -->
          <div class="px-6 py-4 border-t border-gray-200 bg-gray-50">
            <div class="flex items-center justify-between">
              <div class="text-sm text-gray-600">
                <span class="font-medium">Selected:</span>
                {{ currentModelName }}
              </div>
              <button 
                @click="close"
                class="btn btn-primary"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useChatStore } from '../stores/chat'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const chatStore = useChatStore()

const availableModels = computed(() => chatStore.availableModels)
const modelsLoading = computed(() => chatStore.modelsLoading)
const selectedProvider = computed(() => chatStore.selectedProvider)
const selectedModel = computed(() => chatStore.selectedModel)

const currentModelName = computed(() => {
  if (!availableModels.value || !selectedProvider.value || !selectedModel.value) {
    return 'None'
  }
  
  const provider = availableModels.value.providers.find(p => p.id === selectedProvider.value)
  if (!provider) return 'None'
  
  const model = provider.models[selectedModel.value]
  return model ? `${provider.name} / ${model.name}` : 'None'
})

function isSelected(providerId, modelId) {
  return selectedProvider.value === providerId && selectedModel.value === modelId
}

function selectModel(providerId, modelId) {
  chatStore.setModel(providerId, modelId)
}

function close() {
  emit('close')
}
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .relative,
.modal-leave-active .relative {
  transition: transform 0.3s ease;
}

.modal-enter-from .relative,
.modal-leave-to .relative {
  transform: scale(0.95);
}
</style>
