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
      <!-- Message Info -->
      <div class="mb-2 text-xs opacity-70 border-b border-gray-200 pb-2">
        <div class="flex justify-between items-center">
          <span>{{ message.info?.role || 'unknown' }}</span>
          <span>{{ formattedTime }}</span>
        </div>
        <div class="text-xs mt-1">
          ID: {{ message.info?.id?.slice(0, 8) }}
          <span v-if="message.info?.time?.completed" class="ml-2">
            Duration: {{ completionDuration }}ms
          </span>
        </div>
      </div>

      <!-- Message Parts -->
      <div class="space-y-3">
        <div 
          v-for="(part, index) in message.parts" 
          :key="index"
          class="border-l-2 pl-3"
          :class="getPartBorderClass(part.type)"
        >
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xs font-medium uppercase tracking-wide" :class="getPartTypeClass(part.type)">
              {{ part.type }}
            </span>
            <span v-if="part.time?.start && part.time?.end" class="text-xs opacity-60">
              {{ partDuration(part) }}ms
            </span>
          </div>
          
          <!-- Text Content -->
          <div v-if="part.type === 'text' && part.text" class="prose prose-sm max-w-none" v-html="formatText(part.text)"></div>
          
          <!-- Reasoning Content -->
          <div v-else-if="part.type === 'reasoning'" class="text-sm italic text-gray-600 bg-gray-50 p-2 rounded">
            {{ part.text || 'Reasoning in progress...' }}
          </div>
          
          <!-- Tool Call -->
          <div v-else-if="part.type === 'tool'" class="bg-blue-50 p-3 rounded border">
            <div class="font-medium text-blue-900">{{ part.tool }}: {{ part.state?.title || 'Tool execution' }}</div>
            <div v-if="part.state?.input" class="mt-2 text-sm">
              <strong>Input:</strong>
              <pre class="bg-white p-2 rounded mt-1 overflow-x-auto">{{ JSON.stringify(part.state.input, null, 2) }}</pre>
            </div>
            <div v-if="part.state?.output" class="mt-2 text-sm">
              <strong>Output:</strong>
              <pre class="bg-white p-2 rounded mt-1 overflow-x-auto">{{ JSON.stringify(part.state.output, null, 2) }}</pre>
            </div>
            <div class="mt-2 text-xs text-blue-700">
              Status: {{ part.state?.status || 'unknown' }}
            </div>
          </div>
          
          <!-- Step Start/Finish -->
          <div v-else-if="part.type === 'step-start'" class="text-sm text-green-700 bg-green-50 p-2 rounded">
            Started processing...
          </div>
          <div v-else-if="part.type === 'step-finish'" class="text-sm text-green-700 bg-green-50 p-2 rounded">
            Finished processing. Reason: {{ part.reason || 'unknown' }}
            <div v-if="part.cost !== undefined" class="mt-1 text-xs">
              Cost: ${{ part.cost }}, Tokens: {{ part.tokens?.input || 0 }} in / {{ part.tokens?.output || 0 }} out
            </div>
          </div>
          
          <!-- Other parts -->
          <div v-else class="text-sm text-gray-600 bg-gray-50 p-2 rounded">
            <pre>{{ JSON.stringify(part, null, 2) }}</pre>
          </div>
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
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
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
