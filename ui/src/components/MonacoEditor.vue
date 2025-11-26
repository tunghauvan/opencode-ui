<template>
  <div class="monaco-editor-wrapper h-full flex flex-col">
    <!-- Tab Bar -->
    <div class="editor-tabs glass border-b border-white/20 flex items-center min-h-[40px] px-2 gap-1 overflow-x-auto">
      <div
        v-for="file in openFiles"
        :key="file.path"
        class="editor-tab flex items-center gap-2 px-3 py-1.5 rounded-t-lg cursor-pointer text-sm whitespace-nowrap transition-all"
        :class="[
          file.path === activeFilePath
            ? 'bg-white/80 text-gray-800 shadow-sm'
            : 'text-gray-600 hover:bg-white/50'
        ]"
        @click="selectFile(file.path)"
      >
        <span class="file-icon">{{ getFileIcon(file.path) }}</span>
        <span>{{ getFileName(file.path) }}</span>
        <span v-if="file.modified" class="w-2 h-2 rounded-full bg-primary-500" title="Unsaved changes"></span>
        <button
          @click.stop="handleCloseFile(file.path)"
          class="ml-1 p-0.5 rounded hover:bg-gray-200 text-gray-400 hover:text-gray-600"
          title="Close file"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div v-if="openFiles.length === 0" class="text-gray-400 text-sm px-3">
        No files open
      </div>
    </div>

    <!-- Editor Container -->
    <div class="editor-container flex-1 relative">
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
        <div class="flex items-center gap-3">
          <div class="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
          <span class="text-gray-600">Loading...</span>
        </div>
      </div>

      <div v-if="!activeFile && !loading" class="absolute inset-0 flex items-center justify-center bg-gray-50">
        <div class="text-center">
          <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
            <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <p class="text-gray-500 text-sm">Select a file from the explorer to edit</p>
        </div>
      </div>

      <div ref="editorContainer" class="h-full w-full"></div>
    </div>

    <!-- Status Bar -->
    <div class="editor-statusbar glass border-t border-white/20 px-4 py-1 flex items-center justify-between text-xs text-gray-500">
      <div class="flex items-center gap-4">
        <span v-if="activeFile">{{ activeFile.path }}</span>
        <span v-if="activeFile && activeFile.modified" class="text-primary-500 font-medium">Modified</span>
      </div>
      <div class="flex items-center gap-4">
        <span v-if="activeFile">{{ activeFile.language }}</span>
        <span v-if="activeFile">{{ activeFile.encoding }}</span>
        <button
          v-if="activeFile && activeFile.modified"
          @click="handleSave"
          :disabled="saving"
          class="px-2 py-0.5 bg-primary-500 text-white rounded hover:bg-primary-600 disabled:opacity-50"
        >
          {{ saving ? 'Saving...' : 'Save' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import loader from '@monaco-editor/loader'
import { useFileStore } from '../stores/file'
import { useSessionStore } from '../stores/session'

const fileStore = useFileStore()
const sessionStore = useSessionStore()

const editorContainer = ref(null)
let monacoEditor = null
let monaco = null

const loading = computed(() => fileStore.loading)
const saving = computed(() => fileStore.saving)
const openFiles = computed(() => fileStore.openFiles)
const activeFilePath = computed(() => fileStore.activeFilePath)
const activeFile = computed(() => fileStore.activeFile)

// Get file name from path
function getFileName(path) {
  return path.split('/').pop()
}

// Get file icon based on extension
function getFileIcon(path) {
  const ext = path.split('.').pop().toLowerCase()
  const iconMap = {
    'js': '📜',
    'jsx': '⚛️',
    'ts': '💙',
    'tsx': '💙',
    'vue': '💚',
    'html': '🌐',
    'css': '🎨',
    'scss': '🎨',
    'json': '📋',
    'md': '📝',
    'py': '🐍',
    'go': '🐹',
    'rs': '🦀',
    'java': '☕',
    'sh': '💻',
    'yaml': '📄',
    'yml': '📄',
    'dockerfile': '🐳'
  }
  return iconMap[ext] || '📄'
}

// Select a file tab
function selectFile(path) {
  fileStore.activeFilePath = path
}

// Handle close file with unsaved changes check
function handleCloseFile(path) {
  const file = fileStore.openFiles.find(f => f.path === path)
  if (file && file.modified) {
    if (!confirm('This file has unsaved changes. Close anyway?')) {
      return
    }
  }
  fileStore.closeFile(path)
}

// Handle save file
async function handleSave() {
  if (!activeFilePath.value || !sessionStore.currentSessionId) return
  
  try {
    await fileStore.saveFile(sessionStore.currentSessionId, activeFilePath.value)
  } catch (e) {
    console.error('Failed to save file:', e)
    alert('Failed to save file: ' + e.message)
  }
}

// Initialize Monaco Editor
async function initMonaco() {
  try {
    // Configure Monaco loader to use CDN
    loader.config({
      paths: {
        vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs'
      }
    })
    
    monaco = await loader.init()
    
    if (editorContainer.value) {
      monacoEditor = monaco.editor.create(editorContainer.value, {
        value: '',
        language: 'plaintext',
        theme: 'vs',
        automaticLayout: true,
        minimap: { enabled: true },
        fontSize: 14,
        lineNumbers: 'on',
        wordWrap: 'on',
        scrollBeyondLastLine: false,
        renderWhitespace: 'selection',
        tabSize: 2,
        insertSpaces: true,
        formatOnPaste: true,
        formatOnType: true
      })

      // Listen for content changes
      monacoEditor.onDidChangeModelContent(() => {
        if (activeFilePath.value) {
          const content = monacoEditor.getValue()
          fileStore.updateFileContent(activeFilePath.value, content)
        }
      })

      // Add keyboard shortcuts
      monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
        handleSave()
      })
    }
  } catch (e) {
    console.error('Failed to initialize Monaco Editor:', e)
  }
}

// Update editor content when active file changes
watch(activeFile, (newFile) => {
  if (monacoEditor && newFile) {
    const model = monacoEditor.getModel()
    if (model) {
      monaco.editor.setModelLanguage(model, newFile.language)
    }
    monacoEditor.setValue(newFile.content)
  } else if (monacoEditor && !newFile) {
    monacoEditor.setValue('')
  }
}, { immediate: true })

onMounted(() => {
  initMonaco()
})

onUnmounted(() => {
  if (monacoEditor) {
    monacoEditor.dispose()
  }
})
</script>

<style scoped>
.monaco-editor-wrapper {
  background: linear-gradient(to bottom right, #f8fafc, #f1f5f9);
}

.editor-tabs {
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) transparent;
}

.editor-tabs::-webkit-scrollbar {
  height: 4px;
}

.editor-tabs::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
}

.editor-container {
  min-height: 200px;
}
</style>
