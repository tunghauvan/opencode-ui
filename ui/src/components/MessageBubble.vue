<template>
  <div 
    class="flex gap-3"
    :class="[
      message.role === 'user' ? 'justify-end' : 'justify-start'
    ]"
  >
    <!-- Avatar -->
    <div 
      v-if="message.role === 'assistant'"
      class="flex-shrink-0 w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-semibold"
    >
      AI
    </div>

    <!-- Message Content -->
    <div 
      class="max-w-3xl rounded-2xl px-4 py-3 shadow-sm"
      :class="[
        message.role === 'user' 
          ? 'bg-primary-600 text-white' 
          : message.isError
            ? 'bg-red-50 text-red-900 border border-red-200'
            : 'bg-white text-gray-900 border border-gray-200'
      ]"
    >
      <div class="prose prose-sm max-w-none" v-html="formattedContent"></div>
      
      <div 
        class="text-xs mt-2 opacity-70"
        :class="message.role === 'user' ? 'text-white' : 'text-gray-500'"
      >
        {{ formattedTime }}
      </div>
    </div>

    <!-- Avatar -->
    <div 
      v-if="message.role === 'user'"
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

const formattedContent = computed(() => {
  const content = props.message.content || ''
  
  // Configure marked for safe rendering
  marked.setOptions({
    breaks: true,
    gfm: true
  })
  
  try {
    return marked.parse(content)
  } catch (error) {
    console.error('Error parsing markdown:', error)
    return content.replace(/\n/g, '<br>')
  }
})

const formattedTime = computed(() => {
  if (!props.message.timestamp) return ''
  
  const date = new Date(props.message.timestamp)
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit'
  })
})
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
