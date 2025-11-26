<template>
  <div class="split-view h-full flex">
    <!-- Left Panel: Chat -->
    <div 
      class="chat-panel flex flex-col transition-all duration-300"
      :style="{ width: isEditorVisible ? chatWidth : '100%' }"
    >
      <slot name="chat"></slot>
    </div>

    <!-- Resizer -->
    <div
      v-if="isEditorVisible"
      class="resizer w-1 bg-gray-200 hover:bg-primary-400 cursor-col-resize transition-colors relative z-10"
      @mousedown="startResize"
    >
      <div class="resizer-handle absolute inset-y-0 -left-1 -right-1"></div>
    </div>

    <!-- Right Panel: Editor -->
    <div 
      v-if="isEditorVisible"
      class="editor-panel flex transition-all duration-300 overflow-hidden"
      :style="{ width: editorWidth }"
    >
      <!-- File Explorer -->
      <div 
        class="file-explorer-panel border-r border-gray-200/50 transition-all duration-300"
        :style="{ width: showExplorer ? explorerWidth : '0px' }"
      >
        <FileExplorer v-if="showExplorer" />
      </div>

      <!-- Monaco Editor -->
      <div class="monaco-panel flex-1 flex flex-col min-w-0">
        <!-- Editor Toolbar -->
        <div class="editor-toolbar glass border-b border-white/20 px-4 py-2 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <button
              @click="toggleExplorer"
              class="p-1.5 rounded-lg hover:bg-white/50 text-gray-600 hover:text-gray-800 transition-colors"
              :title="showExplorer ? 'Hide Explorer' : 'Show Explorer'"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </button>
            <span class="text-sm font-medium text-gray-700">Code Editor</span>
          </div>

          <div class="flex items-center gap-2">
            <button
              @click="closeEditor"
              class="p-1.5 rounded-lg hover:bg-red-100 text-gray-500 hover:text-red-600 transition-colors"
              title="Close Editor"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Editor Content -->
        <div class="flex-1 min-h-0">
          <MonacoEditor />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useFileStore } from '../stores/file'
import FileExplorer from './FileExplorer.vue'
import MonacoEditor from './MonacoEditor.vue'

const fileStore = useFileStore()

// Panel sizes
const chatWidthPercent = ref(50)
const explorerWidthPx = ref(250)
const showExplorer = ref(true)
const isResizing = ref(false)

const isEditorVisible = computed(() => fileStore.isEditorVisible)

const chatWidth = computed(() => `${chatWidthPercent.value}%`)
const editorWidth = computed(() => `${100 - chatWidthPercent.value}%`)
const explorerWidth = computed(() => `${explorerWidthPx.value}px`)

// Resize handling
function startResize(e) {
  isResizing.value = true
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
}

function handleResize(e) {
  if (!isResizing.value) return
  
  const container = document.querySelector('.split-view')
  if (!container) return
  
  const containerRect = container.getBoundingClientRect()
  const newPercent = ((e.clientX - containerRect.left) / containerRect.width) * 100
  
  // Clamp between 20% and 80%
  chatWidthPercent.value = Math.max(20, Math.min(80, newPercent))
}

function stopResize() {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}

// Toggle file explorer
function toggleExplorer() {
  showExplorer.value = !showExplorer.value
}

// Close editor panel
function closeEditor() {
  fileStore.hideEditor()
}

// Cleanup
onUnmounted(() => {
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
})
</script>

<style scoped>
.split-view {
  position: relative;
}

.chat-panel {
  min-width: 300px;
}

.editor-panel {
  min-width: 400px;
  background: linear-gradient(to bottom right, #f8fafc, #f1f5f9);
}

.resizer {
  flex-shrink: 0;
}

.resizer-handle {
  cursor: col-resize;
}

.resizer:hover {
  background: linear-gradient(to bottom, #6366f1, #8b5cf6);
}

.file-explorer-panel {
  overflow: hidden;
}

.monaco-panel {
  background: #ffffff;
}
</style>
