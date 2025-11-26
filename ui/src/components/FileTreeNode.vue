<template>
  <div class="tree-node">
    <!-- Node Item -->
    <div
      class="node-item group flex items-center gap-1 px-2 py-1 rounded-lg cursor-pointer hover:bg-white/60 transition-all"
      :style="{ paddingLeft: `${depth * 16 + 8}px` }"
      :class="{ 'bg-primary-100 text-primary-700': isActive }"
      @click="handleClick"
    >
      <!-- Expand/Collapse Arrow for directories -->
      <span v-if="item.type === 'directory'" class="expand-icon flex-shrink-0 w-4 h-4 flex items-center justify-center">
        <svg
          class="w-3 h-3 transition-transform"
          :class="{ 'rotate-90': isExpanded }"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
        </svg>
      </span>
      <span v-else class="w-4 h-4 flex-shrink-0"></span>

      <!-- Icon -->
      <span class="node-icon flex-shrink-0 text-sm">{{ getIcon() }}</span>

      <!-- Name -->
      <span class="node-name text-sm truncate" :title="item.name">{{ item.name }}</span>

      <!-- Actions (Rename/Delete) -->
      <div class="actions ml-auto flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <button 
          @click.stop="handleRename" 
          class="p-0.5 hover:bg-gray-200 rounded text-xs" 
          title="Rename"
        >
          ✏️
        </button>
        <button 
          @click.stop="handleDelete" 
          class="p-0.5 hover:bg-red-100 text-red-600 rounded text-xs" 
          title="Delete"
        >
          🗑️
        </button>
      </div>
    </div>

    <!-- Children (for directories) -->
    <div v-if="item.type === 'directory' && isExpanded && item.children" class="children">
      <FileTreeNode
        v-for="child in item.children"
        :key="child.path"
        :item="child"
        :depth="depth + 1"
        :expanded-dirs="expandedDirs"
        @toggle-dir="$emit('toggle-dir', $event)"
        @select-file="$emit('select-file', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useFileStore } from '../stores/file'
import { useSessionStore } from '../stores/session'

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  depth: {
    type: Number,
    default: 0
  },
  expandedDirs: {
    type: Set,
    required: true
  }
})

const emit = defineEmits(['toggle-dir', 'select-file'])

const fileStore = useFileStore()
const sessionStore = useSessionStore()

const isExpanded = computed(() => {
  return props.expandedDirs.has(props.item.path)
})

const isActive = computed(() => {
  return fileStore.activeFilePath === props.item.path
})

async function handleRename() {
  const newName = prompt('Enter new name:', props.item.name)
  if (newName && newName !== props.item.name) {
    try {
      // Calculate new path
      // Handle root files vs nested files
      const lastSlashIndex = props.item.path.lastIndexOf('/')
      const parentPath = lastSlashIndex === 0 ? '/' : props.item.path.substring(0, lastSlashIndex)
      
      // If parentPath is just '/', we need to be careful not to double slash if we just append
      // Actually, paths usually start with /. 
      // If path is /foo.txt, parent is /. newPath should be /bar.txt
      // If path is /dir/foo.txt, parent is /dir. newPath should be /dir/bar.txt
      
      let newPath
      if (parentPath === '/') {
        newPath = `/${newName}`
      } else {
        newPath = `${parentPath}/${newName}`
      }
      
      await fileStore.renameFile(sessionStore.currentSessionId, props.item.path, newPath)
    } catch (e) {
      alert('Failed to rename: ' + e.message)
    }
  }
}

async function handleDelete() {
  if (confirm(`Are you sure you want to delete ${props.item.name}?`)) {
    try {
      if (props.item.type === 'directory') {
        await fileStore.deleteDirectory(sessionStore.currentSessionId, props.item.path)
      } else {
        await fileStore.deleteFile(sessionStore.currentSessionId, props.item.path)
      }
    } catch (e) {
      alert('Failed to delete: ' + e.message)
    }
  }
}

// Get icon based on type and extension
function getIcon() {
  if (props.item.type === 'directory') {
    return isExpanded.value ? '📂' : '📁'
  }

  const fileName = props.item.name.toLowerCase()
  const parts = fileName.split('.')
  
  // Handle files without extension or special filenames
  if (parts.length === 1 || fileName.startsWith('.')) {
    const specialFiles = {
      'dockerfile': '🐳',
      'makefile': '⚙️',
      '.gitignore': '🚫',
      '.dockerignore': '🚫',
      '.env': '🔐',
      '.editorconfig': '⚙️'
    }
    return specialFiles[fileName] || '📄'
  }
  
  const ext = parts.pop()
  const iconMap = {
    'js': '📜',
    'jsx': '⚛️',
    'ts': '💙',
    'tsx': '💙',
    'vue': '💚',
    'html': '🌐',
    'css': '🎨',
    'scss': '🎨',
    'less': '🎨',
    'json': '📋',
    'md': '📝',
    'py': '🐍',
    'go': '🐹',
    'rs': '🦀',
    'java': '☕',
    'c': '📘',
    'cpp': '📘',
    'h': '📘',
    'sh': '💻',
    'bash': '💻',
    'yaml': '📄',
    'yml': '📄',
    'xml': '📄',
    'sql': '🗄️',
    'dockerfile': '🐳',
    'gitignore': '🚫',
    'env': '🔐',
    'lock': '🔒',
    'log': '📋',
    'txt': '📄',
    'png': '🖼️',
    'jpg': '🖼️',
    'jpeg': '🖼️',
    'gif': '🖼️',
    'svg': '🎨',
    'pdf': '📕',
    'zip': '📦',
    'tar': '📦',
    'gz': '📦'
  }
  return iconMap[ext] || '📄'
}

// Format file size
function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// Handle click on node
function handleClick() {
  if (props.item.type === 'directory') {
    emit('toggle-dir', props.item.path)
  } else {
    emit('select-file', props.item.path)
  }
}
</script>

<style scoped>
.tree-node {
  user-select: none;
}

.node-item:hover {
  background: rgba(255, 255, 255, 0.8);
}

.node-name {
  max-width: 150px;
}

.expand-icon {
  color: #6b7280;
}
</style>
