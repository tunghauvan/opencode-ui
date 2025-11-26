<template>
  <div class="file-explorer h-full flex flex-col bg-gradient-to-b from-gray-50 to-gray-100">
    <!-- Header -->
    <div class="explorer-header glass border-b border-white/20 px-4 py-3 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <svg class="w-5 h-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
        <span class="font-semibold text-gray-700">Explorer</span>
      </div>
      <button
        @click="refreshTree"
        :disabled="loading"
        class="p-1.5 rounded-lg hover:bg-white/50 text-gray-500 hover:text-gray-700 transition-colors"
        title="Refresh"
      >
        <svg class="w-4 h-4" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
    </div>

    <!-- Current Path -->
    <div class="path-bar px-4 py-2 text-xs text-gray-500 border-b border-gray-200/50 bg-white/30">
      <span class="font-mono">{{ currentPath }}</span>
    </div>

    <!-- File Tree -->
    <div class="tree-container flex-1 overflow-y-auto px-2 py-2">
      <div v-if="loading && fileTree.length === 0" class="flex items-center justify-center py-8">
        <div class="flex items-center gap-2 text-gray-500">
          <div class="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
          <span class="text-sm">Loading...</span>
        </div>
      </div>

      <div v-else-if="error" class="text-red-500 text-sm px-2 py-4 text-center">
        {{ error }}
      </div>

      <div v-else-if="fileTree.length === 0" class="text-gray-400 text-sm px-2 py-8 text-center">
        <p>No files found</p>
        <p class="text-xs mt-1">Container might not have file API enabled</p>
      </div>

      <FileTreeNode
        v-for="item in fileTree"
        :key="item.path"
        :item="item"
        :depth="0"
        :expanded-dirs="expandedDirs"
        @toggle-dir="handleToggleDir"
        @select-file="handleSelectFile"
      />
    </div>

    <!-- Footer -->
    <div class="explorer-footer glass border-t border-white/20 px-4 py-2 text-xs text-gray-500">
      <div v-if="hasUnsavedChanges" class="flex items-center gap-1 text-primary-500">
        <span class="w-2 h-2 bg-primary-500 rounded-full animate-pulse"></span>
        <span>Unsaved changes</span>
      </div>
      <div v-else>
        {{ fileTree.length }} items
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useFileStore } from '../stores/file'
import { useSessionStore } from '../stores/session'
import FileTreeNode from './FileTreeNode.vue'

const fileStore = useFileStore()
const sessionStore = useSessionStore()

const loading = computed(() => fileStore.loading)
const error = computed(() => fileStore.error)
const fileTree = computed(() => fileStore.fileTree)
const currentPath = computed(() => fileStore.currentPath)
const expandedDirs = computed(() => fileStore.expandedDirs)
const hasUnsavedChanges = computed(() => fileStore.hasUnsavedChanges)

// Refresh the file tree
async function refreshTree() {
  if (!sessionStore.currentSessionId) return
  await fileStore.loadFileTree(sessionStore.currentSessionId, '/')
}

// Handle directory toggle
async function handleToggleDir(path) {
  if (!sessionStore.currentSessionId) return
  await fileStore.toggleDirectory(sessionStore.currentSessionId, path)
}

// Handle file selection
async function handleSelectFile(path) {
  if (!sessionStore.currentSessionId) return
  try {
    await fileStore.openFile(sessionStore.currentSessionId, path)
  } catch (e) {
    console.error('Failed to open file:', e)
  }
}

// Load file tree when session changes
watch(() => sessionStore.currentSessionId, async (sessionId) => {
  if (sessionId) {
    await fileStore.loadFileTree(sessionId, '/')
  } else {
    fileStore.reset()
  }
}, { immediate: true })

onMounted(() => {
  if (sessionStore.currentSessionId) {
    fileStore.loadFileTree(sessionStore.currentSessionId, '/')
  }
})
</script>

<style scoped>
.file-explorer {
  min-width: 200px;
}

.tree-container {
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.1) transparent;
}

.tree-container::-webkit-scrollbar {
  width: 6px;
}

.tree-container::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.tree-container::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}
</style>
