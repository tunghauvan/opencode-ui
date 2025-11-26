<template>
  <div class="tree-node">
    <!-- Node Item -->
    <div
      class="node-item flex items-center gap-1 px-2 py-1 rounded-lg cursor-pointer hover:bg-white/60 transition-all"
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

      <!-- File size (for files) -->
      <span v-if="item.type === 'file' && item.size" class="text-xs text-gray-400 ml-auto">
        {{ formatSize(item.size) }}
      </span>
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

const isExpanded = computed(() => {
  return props.expandedDirs.has(props.item.path)
})

const isActive = computed(() => {
  return fileStore.activeFilePath === props.item.path
})

// Get icon based on type and extension
function getIcon() {
  if (props.item.type === 'directory') {
    return isExpanded.value ? '📂' : '📁'
  }

  const ext = props.item.name.split('.').pop().toLowerCase()
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
