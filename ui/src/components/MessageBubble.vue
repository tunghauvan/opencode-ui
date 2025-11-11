<template>
  <div 
    class="flex gap-3"
    :class="[
      message.info?.role === 'user' ? 'justify-end' : 'justify-start'
    ]"
  >
    <!-- Avatar -->
    <div 
      v-if="message.info?.role === 'assistant'"
      class="flex-shrink-0 w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-semibold"
    >
      AI
    </div>

    <!-- Message Content -->
    <div 
      class="max-w-4xl rounded-2xl px-4 py-3 shadow-sm"
      :class="[
        message.info?.role === 'user' 
          ? 'bg-primary-600 text-white' 
          : message.isError
            ? 'bg-red-50 text-red-900 border border-red-200'
            : 'bg-white text-gray-900 border border-gray-200'
      ]"
    >
      <!-- Message Header -->
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <span class="text-sm font-medium" :class="message.info?.role === 'user' ? 'text-white' : 'text-gray-900'">
            {{ message.info?.role || 'unknown' }}
          </span>
          <span class="text-xs opacity-70" :class="message.info?.role === 'user' ? 'text-white' : 'text-gray-500'">
            {{ formattedTime }}
          </span>
          <span v-if="completionDuration" class="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
            {{ completionDuration }}ms
          </span>
        </div>
        
        <!-- Collapsible details toggle -->
        <button 
          v-if="hasTechnicalDetails"
          @click="showDetails = !showDetails"
          class="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
        >
          <svg class="w-4 h-4" :class="{ 'rotate-180': showDetails }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
          Details
        </button>
      </div>

      <!-- Main Content -->
      <div class="space-y-3">
        <!-- Primary Text Content -->
        <div v-if="primaryText" class="prose prose-sm max-w-none" v-html="formatText(primaryText)"></div>
        
        <!-- Tool Executions -->
        <div v-if="toolParts.length > 0" class="space-y-2">
          <h4 class="text-sm font-medium text-gray-700 flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Tool Executions
          </h4>
          
          <div v-for="tool in toolParts" :key="tool.id" class="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div class="flex items-center gap-2 mb-2">
              <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span class="font-medium text-blue-900">{{ tool.tool }} command</span>
              <span class="text-xs px-2 py-1 rounded" :class="getStatusClass(tool.state?.status)">
                {{ tool.state?.status || 'unknown' }}
              </span>
            </div>
            
            <div v-if="tool.state?.input?.command" class="text-sm text-gray-700 mb-2">
              <strong class="text-gray-900">Command:</strong> 
              <code class="bg-gray-100 px-2 py-1 rounded text-xs">{{ tool.state.input.command }}</code>
            </div>
            
            <div v-if="tool.state?.input?.description" class="text-sm text-gray-600 mb-2">
              {{ tool.state.input.description }}
            </div>
            
            <div v-if="tool.state?.output" class="bg-gray-900 text-green-400 p-3 rounded font-mono text-sm overflow-x-auto">
              <pre>{{ tool.state.output }}</pre>
            </div>
            
            <div v-if="tool.state?.time" class="text-xs text-gray-500 mt-2">
              Duration: {{ toolDuration(tool) }}ms
            </div>
          </div>
        </div>
      </div>

      <!-- Technical Details (Collapsible) -->
      <div v-if="showDetails && hasTechnicalDetails" class="mt-4 pt-4 border-t border-gray-200">
        <h4 class="text-sm font-medium text-gray-700 mb-3">Technical Details</h4>
        
        <div class="space-y-2">
          <div class="text-xs text-gray-600">
            <strong>Message ID:</strong> {{ message.info?.id }}
          </div>
          
          <div v-if="message.info?.modelID" class="text-xs text-gray-600">
            <strong>Model:</strong> {{ message.info.providerID }}/{{ message.info.modelID }}
          </div>
          
          <div v-if="message.info?.tokens" class="text-xs text-gray-600">
            <strong>Tokens:</strong> {{ message.info.tokens.input }} in / {{ message.info.tokens.output }} out
            <span v-if="message.info.tokens.cache"> ({{ message.info.tokens.cache.read }} cached)</span>
          </div>
          
          <div v-if="message.info?.cost !== undefined" class="text-xs text-gray-600">
            <strong>Cost:</strong> ${{ message.info.cost }}
          </div>
          
          <!-- All Parts Details -->
          <details class="mt-3">
            <summary class="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
              Show all message parts ({{ message.parts?.length || 0 }})
            </summary>
            
            <div class="mt-2 space-y-2 max-h-60 overflow-y-auto">
              <div 
                v-for="(part, index) in message.parts" 
                :key="index"
                class="border-l-2 pl-3 text-xs"
                :class="getPartBorderClass(part.type)"
              >
                <div class="flex items-center gap-2 mb-1">
                  <span class="font-medium uppercase tracking-wide" :class="getPartTypeClass(part.type)">
                    {{ part.type }}
                  </span>
                  <span v-if="part.time?.start && part.time?.end" class="text-gray-500">
                    {{ partDuration(part) }}ms
                  </span>
                </div>
                
                <div v-if="part.type === 'text' && part.text" class="text-gray-700 bg-gray-50 p-2 rounded text-xs">
                  {{ part.text }}
                </div>
                
                <div v-else-if="part.type === 'reasoning'" class="text-gray-700 bg-yellow-50 p-2 rounded text-xs">
                  {{ part.text || 'No reasoning content' }}
                </div>
                
                <div v-else class="text-gray-600 bg-gray-50 p-2 rounded text-xs">
                  <pre>{{ JSON.stringify(part, null, 2) }}</pre>
                </div>
              </div>
            </div>
          </details>
        </div>
      </div>
    </div>

    <!-- Avatar -->
    <div 
      v-if="message.info?.role === 'user'"
      class="flex-shrink-0 w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-white font-semibold"
    >
      U
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const showDetails = ref(false)

// Filter visible parts (hide empty reasoning, empty text, step-start/finish)
const visibleParts = computed(() => {
  if (!props.message.parts) return []
  
  return props.message.parts.filter(part => {
    // Hide step-start and step-finish
    if (part.type === 'step-start' || part.type === 'step-finish') return false
    
    // Hide empty reasoning
    if (part.type === 'reasoning' && (!part.text || part.text.trim() === '')) return false
    
    // Hide empty text
    if (part.type === 'text' && (!part.text || part.text.trim() === '')) return false
    
    return true
  })
})

// Get primary text content (first non-empty text part)
const primaryText = computed(() => {
  const textParts = props.message.parts?.filter(part => 
    part.type === 'text' && part.text && part.text.trim() !== ''
  ) || []
  
  return textParts.length > 0 ? textParts[0].text : ''
})

// Get tool parts
const toolParts = computed(() => {
  return props.message.parts?.filter(part => part.type === 'tool') || []
})

// Check if message has technical details to show
const hasTechnicalDetails = computed(() => {
  return props.message.parts && props.message.parts.length > 1
})

const formattedTime = computed(() => {
  const timestamp = props.message.info?.time?.created
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  return date.toLocaleString('en-US', { 
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  })
})

const completionDuration = computed(() => {
  const created = props.message.info?.time?.created
  const completed = props.message.info?.time?.completed
  if (!created || !completed) return null
  
  return completed - created
})

function partDuration(part) {
  if (!part.time?.start || !part.time?.end) return null
  return part.time.end - part.time.start
}

function toolDuration(tool) {
  if (!tool.state?.time?.start || !tool.state?.time?.end) return null
  return tool.state.time.end - tool.state.time.start
}

function formatText(text) {
  if (!text) return ''
  
  // Configure marked for safe rendering
  marked.setOptions({
    breaks: true,
    gfm: true
  })
  
  try {
    return marked.parse(text)
  } catch (error) {
    console.error('Error parsing markdown:', error)
    return text.replace(/\n/g, '<br>')
  }
}

function getPartBorderClass(type) {
  const classes = {
    'text': 'border-blue-300',
    'reasoning': 'border-yellow-300',
    'tool': 'border-purple-300',
    'step-start': 'border-green-300',
    'step-finish': 'border-green-300'
  }
  return classes[type] || 'border-gray-300'
}

function getPartTypeClass(type) {
  const classes = {
    'text': 'text-blue-700',
    'reasoning': 'text-yellow-700',
    'tool': 'text-purple-700',
    'step-start': 'text-green-700',
    'step-finish': 'text-green-700'
  }
  return classes[type] || 'text-gray-700'
}

function getStatusClass(status) {
  const classes = {
    'completed': 'bg-green-100 text-green-800',
    'running': 'bg-blue-100 text-blue-800',
    'failed': 'bg-red-100 text-red-800'
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}
</script>

<style scoped>
:deep(.prose) {
  color: inherit;
}

:deep(.prose p) {
  margin: 0;
}

:deep(.prose p + p) {
  margin-top: 0.75rem;
}

:deep(.prose code) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
}

:deep(.prose pre) {
  background-color: #1e293b;
  color: #e2e8f0;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 0.75rem 0;
}

:deep(.prose pre code) {
  background-color: transparent;
  padding: 0;
  color: inherit;
}

:deep(.prose ul),
:deep(.prose ol) {
  margin: 0.75rem 0;
  padding-left: 1.5rem;
}

:deep(.prose li) {
  margin: 0.25rem 0;
}

:deep(.prose a) {
  color: inherit;
  text-decoration: underline;
}
</style>
