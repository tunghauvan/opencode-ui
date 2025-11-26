<template>
  <div 
    class="flex gap-3 animate-slide-up"
    :class="[
      message.info?.role === 'user' ? 'justify-end' : 'justify-start'
    ]"
  >
    <!-- Avatar for Assistant -->
    <div 
      v-if="message.info?.role === 'assistant'"
      class="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-primary-600 to-purple-600 flex items-center justify-center text-white font-bold shadow-lg shadow-primary-500/30 ring-2 ring-white"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    </div>

    <!-- Message Content -->
    <div 
      class="max-w-4xl rounded-3xl px-5 py-4 transition-all duration-300 hover:shadow-xl"
      :class="[
        message.info?.role === 'user' 
          ? 'message-user' 
          : message.isError
            ? 'bg-red-50 text-red-900 border border-red-200 shadow-md'
            : 'message-assistant'
      ]"
    >
      <!-- Message Header -->
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-3">
          <span class="text-xs font-bold uppercase tracking-wider" :class="message.info?.role === 'user' ? 'text-white/90' : 'text-gray-600'">
            {{ message.info?.role || 'unknown' }}
          </span>
          <span class="text-xs opacity-70" :class="message.info?.role === 'user' ? 'text-white/80' : 'text-gray-500'">
            {{ formattedTime }}
          </span>
          <span v-if="completionDuration" class="status-badge bg-primary-100 text-primary-800">
            {{ completionDuration }}ms
          </span>
        </div>
        
        <!-- Collapsible details toggle -->
        <button 
          v-if="hasTechnicalDetails"
          @click="showDetails = !showDetails"
          class="text-xs px-2.5 py-1 rounded-lg transition-all hover:scale-105"
          :class="message.info?.role === 'user' ? 'bg-white/20 text-white hover:bg-white/30' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
        >
          <div class="flex items-center gap-1">
            <svg class="w-3.5 h-3.5 transition-transform" :class="{ 'rotate-180': showDetails }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
            Details
          </div>
        </button>
      </div>

      <!-- Main Content -->
      <div class="space-y-3">
        <template v-for="(part, index) in visibleParts" :key="index">
          <!-- Text Content -->
          <div v-if="part.type === 'text'" class="prose prose-sm max-w-none" v-html="formatText(part.text)"></div>
          
          <!-- Reasoning Content -->
          <div v-else-if="part.type === 'reasoning'" class="bg-yellow-50 p-3 rounded-lg text-sm text-gray-700 border border-yellow-200 italic">
            <div class="flex items-center gap-2 mb-1 text-yellow-800 font-semibold text-xs uppercase tracking-wider">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
              Reasoning
            </div>
            {{ part.text }}
          </div>

          <!-- Tool Execution -->
          <div v-else-if="part.type === 'tool'" class="card bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200 p-4 hover:shadow-lg transition-shadow my-2">
            <div class="flex items-center gap-2 mb-3">
              <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span class="font-bold text-blue-900">{{ part.tool }} command</span>
              <span class="status-badge" :class="getStatusClass(part.state?.status)">
                {{ part.state?.status || 'unknown' }}
              </span>
            </div>
            
            <div v-if="part.state?.input?.command" class="text-sm text-gray-800 mb-2">
              <strong class="text-gray-900">Command:</strong> 
              <code class="bg-white px-2 py-1 rounded-lg text-xs font-mono border border-gray-200">{{ part.state.input.command }}</code>
            </div>
            
            <div v-if="part.state?.input?.description" class="text-sm text-gray-700 mb-2">
              {{ part.state.input.description }}
            </div>
            
            <div v-if="part.state?.output" class="bg-gray-900 text-green-400 p-4 rounded-xl font-mono text-sm overflow-x-auto shadow-inner">
              <pre>{{ part.state.output }}</pre>
            </div>
            
            <div v-if="part.state?.time" class="text-xs text-gray-600 mt-2 flex items-center gap-1">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Duration: {{ toolDuration(part) }}ms
            </div>
          </div>
        </template>
      </div>

      <!-- Technical Details (Collapsible) -->
      <div v-if="showDetails && hasTechnicalDetails" class="mt-4 pt-4 border-t" :class="message.info?.role === 'user' ? 'border-white/20' : 'border-gray-200'">
        <h4 class="text-sm font-bold mb-3" :class="message.info?.role === 'user' ? 'text-white/90' : 'text-gray-800'">Technical Details</h4>
        
        <div class="space-y-2">
          <div class="text-xs" :class="message.info?.role === 'user' ? 'text-white/80' : 'text-gray-600'">
            <strong>Message ID:</strong> {{ message.info?.id }}
          </div>
          
          <div v-if="message.info?.modelID" class="text-xs" :class="message.info?.role === 'user' ? 'text-white/80' : 'text-gray-600'">
            <strong>Model:</strong> {{ message.info.providerID }}/{{ message.info.modelID }}
          </div>
          
          <div v-if="message.info?.tokens" class="text-xs" :class="message.info?.role === 'user' ? 'text-white/80' : 'text-gray-600'">
            <strong>Tokens:</strong> {{ message.info.tokens.input }} in / {{ message.info.tokens.output }} out
            <span v-if="message.info.tokens.cache"> ({{ message.info.tokens.cache.read }} cached)</span>
          </div>
          
          <div v-if="message.info?.cost !== undefined" class="text-xs" :class="message.info?.role === 'user' ? 'text-white/80' : 'text-gray-600'">
            <strong>Cost:</strong> ${{ message.info.cost }}
          </div>
          
          <!-- All Parts Details -->
          <details class="mt-3">
            <summary class="text-xs cursor-pointer hover:opacity-80" :class="message.info?.role === 'user' ? 'text-white/70' : 'text-gray-500'">
              Show all message parts ({{ message.parts?.length || 0 }})
            </summary>
            
            <div class="mt-2 space-y-2 max-h-60 overflow-y-auto">
              <div 
                v-for="(part, index) in message.parts" 
                :key="index"
                class="border-l-2 pl-3 text-xs rounded-r-lg py-2"
                :class="getPartBorderClass(part.type)"
              >
                <div class="flex items-center gap-2 mb-1">
                  <span class="font-medium uppercase tracking-wide" :class="getPartTypeClass(part.type)">
                    {{ part.type }}
                  </span>
                  <span v-if="part.time?.start && part.time?.end" :class="message.info?.role === 'user' ? 'text-white/60' : 'text-gray-500'">
                    {{ partDuration(part) }}ms
                  </span>
                </div>
                
                <div v-if="part.type === 'text' && part.text" class="bg-white/50 p-2 rounded text-xs" :class="message.info?.role === 'user' ? 'text-white' : 'text-gray-700'">
                  {{ part.text }}
                </div>
                
                <div v-else-if="part.type === 'reasoning'" class="bg-yellow-50/50 p-2 rounded text-xs" :class="message.info?.role === 'user' ? 'text-white' : 'text-gray-700'">
                  {{ part.text || 'No reasoning content' }}
                </div>
                
                <div v-else class="bg-white/30 p-2 rounded text-xs" :class="message.info?.role === 'user' ? 'text-white' : 'text-gray-600'">
                  <pre>{{ JSON.stringify(part, null, 2) }}</pre>
                </div>
              </div>
            </div>
          </details>
        </div>
      </div>
    </div>

    <!-- Avatar for User -->
    <div 
      v-if="message.info?.role === 'user'"
      class="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-gray-700 to-gray-900 flex items-center justify-center text-white font-bold shadow-lg shadow-gray-500/30 ring-2 ring-white"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
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
