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
import { ref, watch, nextTick } from 'vue'

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

const localValue = ref(props.modelValue)
const textareaRef = ref(null)

watch(() => props.modelValue, (newValue) => {
  localValue.value = newValue
})

watch(localValue, (newValue) => {
  emit('update:modelValue', newValue)
})

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
