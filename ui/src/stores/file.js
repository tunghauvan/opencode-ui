import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { backendApi } from '../services/api'

export const useFileStore = defineStore('file', () => {
  // File tree state
  const fileTree = ref([])
  const expandedDirs = ref(new Set())
  const currentPath = ref('/')
  
  // Editor state
  const openFiles = ref([]) // Array of { path, content, language, modified }
  const activeFilePath = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const saving = ref(false)
  
  // Editor panel visibility
  const isEditorVisible = ref(false)

  // Get the currently active file
  const activeFile = computed(() => {
    return openFiles.value.find(f => f.path === activeFilePath.value) || null
  })

  // Check if any file has unsaved changes
  const hasUnsavedChanges = computed(() => {
    return openFiles.value.some(f => f.modified)
  })

  // Detect language from file extension
  function detectLanguage(path) {
    const fileName = path.split('/').pop().toLowerCase()
    const parts = fileName.split('.')
    
    // Handle files without extension or with special names
    if (parts.length === 1 || fileName.startsWith('.')) {
      // Check for special filenames without extensions
      const specialFiles = {
        'dockerfile': 'dockerfile',
        'makefile': 'makefile',
        '.gitignore': 'plaintext',
        '.env': 'plaintext',
        '.dockerignore': 'plaintext',
        '.editorconfig': 'plaintext'
      }
      return specialFiles[fileName] || 'plaintext'
    }
    
    const ext = parts.pop()
    const languageMap = {
      'js': 'javascript',
      'jsx': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'vue': 'html',
      'html': 'html',
      'css': 'css',
      'scss': 'scss',
      'less': 'less',
      'json': 'json',
      'md': 'markdown',
      'py': 'python',
      'rb': 'ruby',
      'go': 'go',
      'rs': 'rust',
      'java': 'java',
      'c': 'c',
      'cpp': 'cpp',
      'h': 'c',
      'hpp': 'cpp',
      'sh': 'shell',
      'bash': 'shell',
      'yaml': 'yaml',
      'yml': 'yaml',
      'xml': 'xml',
      'sql': 'sql',
      'dockerfile': 'dockerfile',
      'gitignore': 'plaintext',
      'env': 'plaintext'
    }
    return languageMap[ext] || 'plaintext'
  }

  // Load file tree for a directory
  async function loadFileTree(sessionId, path = '/') {
    loading.value = true
    error.value = null
    try {
      const data = await backendApi.listFiles(sessionId, path)
      
      if (path === '/') {
        fileTree.value = data.entries || []
      } else {
        // Update nested entries in the tree
        updateTreeEntries(fileTree.value, path, data.entries || [])
      }
      
      currentPath.value = path
      return data.entries || []
    } catch (e) {
      error.value = 'Failed to load file tree'
      console.error(e)
      return []
    } finally {
      loading.value = false
    }
  }

  // Helper to update nested tree entries
  function updateTreeEntries(tree, targetPath, entries) {
    for (const item of tree) {
      if (item.path === targetPath && item.type === 'directory') {
        item.children = entries
        return true
      }
      if (item.children && updateTreeEntries(item.children, targetPath, entries)) {
        return true
      }
    }
    return false
  }

  // Toggle directory expansion
  async function toggleDirectory(sessionId, path) {
    if (expandedDirs.value.has(path)) {
      expandedDirs.value.delete(path)
    } else {
      expandedDirs.value.add(path)
      // Load children if not already loaded
      const item = findTreeItem(fileTree.value, path)
      if (item && !item.children) {
        await loadFileTree(sessionId, path)
      }
    }
  }

  // Find item in tree by path
  function findTreeItem(tree, targetPath) {
    for (const item of tree) {
      if (item.path === targetPath) {
        return item
      }
      if (item.children) {
        const found = findTreeItem(item.children, targetPath)
        if (found) return found
      }
    }
    return null
  }

  // Open a file in the editor
  async function openFile(sessionId, path) {
    // Check if file is already open
    const existingFile = openFiles.value.find(f => f.path === path)
    if (existingFile) {
      activeFilePath.value = path
      isEditorVisible.value = true
      return existingFile
    }

    loading.value = true
    error.value = null
    try {
      const data = await backendApi.readFile(sessionId, path)
      
      const file = {
        path: path,
        content: data.content || '',
        originalContent: data.content || '',
        language: detectLanguage(path),
        modified: false,
        encoding: data.encoding || 'utf-8'
      }
      
      openFiles.value.push(file)
      activeFilePath.value = path
      isEditorVisible.value = true
      
      return file
    } catch (e) {
      error.value = 'Failed to open file'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  // Update file content (mark as modified)
  function updateFileContent(path, content) {
    const file = openFiles.value.find(f => f.path === path)
    if (file) {
      file.content = content
      file.modified = content !== file.originalContent
    }
  }

  // Save a file
  async function saveFile(sessionId, path) {
    const file = openFiles.value.find(f => f.path === path)
    if (!file) {
      throw new Error('File not found')
    }

    saving.value = true
    error.value = null
    try {
      await backendApi.writeFile(sessionId, path, file.content)
      
      file.originalContent = file.content
      file.modified = false
      
      return true
    } catch (e) {
      error.value = 'Failed to save file'
      console.error(e)
      throw e
    } finally {
      saving.value = false
    }
  }

  // Create a new file
  async function createFile(sessionId, path, content = '') {
    loading.value = true
    error.value = null
    try {
      await backendApi.writeFile(sessionId, path, content)
      // Refresh parent directory
      const parentPath = path.substring(0, path.lastIndexOf('/')) || '/'
      await loadFileTree(sessionId, parentPath)
      return true
    } catch (e) {
      error.value = 'Failed to create file'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  // Create a new directory
  async function createDirectory(sessionId, path) {
    loading.value = true
    error.value = null
    try {
      await backendApi.createDirectory(sessionId, path)
      // Refresh parent directory
      const parentPath = path.substring(0, path.lastIndexOf('/')) || '/'
      await loadFileTree(sessionId, parentPath)
      return true
    } catch (e) {
      error.value = 'Failed to create directory'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  // Rename a file or directory
  async function renameFile(sessionId, oldPath, newPath) {
    loading.value = true
    error.value = null
    try {
      await backendApi.renameFile(sessionId, oldPath, newPath)
      
      // Update open files if needed
      const openFileIndex = openFiles.value.findIndex(f => f.path === oldPath)
      if (openFileIndex !== -1) {
        const file = openFiles.value[openFileIndex]
        file.path = newPath
        file.language = detectLanguage(newPath)
        
        if (activeFilePath.value === oldPath) {
          activeFilePath.value = newPath
        }
      }
      
      // Refresh parent directory of old path and new path
      const oldParent = oldPath.substring(0, oldPath.lastIndexOf('/')) || '/'
      const newParent = newPath.substring(0, newPath.lastIndexOf('/')) || '/'
      
      await loadFileTree(sessionId, oldParent)
      if (oldParent !== newParent) {
        await loadFileTree(sessionId, newParent)
      }
      
      return true
    } catch (e) {
      error.value = 'Failed to rename'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  // Delete a file
  async function deleteFile(sessionId, path) {
    loading.value = true
    error.value = null
    try {
      await backendApi.deleteFile(sessionId, path)
      
      // Close if open
      closeFile(path)
      
      // Refresh parent directory
      const parentPath = path.substring(0, path.lastIndexOf('/')) || '/'
      await loadFileTree(sessionId, parentPath)
      
      return true
    } catch (e) {
      error.value = 'Failed to delete file'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  // Delete a directory
  async function deleteDirectory(sessionId, path) {
    loading.value = true
    error.value = null
    try {
      await backendApi.deleteDirectory(sessionId, path, true) // Recursive delete
      
      // Close any open files inside this directory
      const filesToClose = openFiles.value.filter(f => f.path.startsWith(path + '/'))
      filesToClose.forEach(f => closeFile(f.path))
      
      // Refresh parent directory
      const parentPath = path.substring(0, path.lastIndexOf('/')) || '/'
      await loadFileTree(sessionId, parentPath)
      
      return true
    } catch (e) {
      error.value = 'Failed to delete directory'
      console.error(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  // Close a file
  function closeFile(path) {
    const index = openFiles.value.findIndex(f => f.path === path)
    if (index !== -1) {
      openFiles.value.splice(index, 1)
      
      // If this was the active file, switch to another one
      if (activeFilePath.value === path) {
        if (openFiles.value.length > 0) {
          // Switch to the next available file, or the previous one if at the end
          const newIndex = index < openFiles.value.length ? index : Math.max(0, index - 1)
          activeFilePath.value = openFiles.value[newIndex].path
        } else {
          activeFilePath.value = null
        }
      }
    }
  }

  // Toggle editor visibility
  function toggleEditor() {
    isEditorVisible.value = !isEditorVisible.value
  }

  // Show editor
  function showEditor() {
    isEditorVisible.value = true
  }

  // Hide editor
  function hideEditor() {
    isEditorVisible.value = false
  }

  // Reset store state
  function reset() {
    fileTree.value = []
    expandedDirs.value = new Set()
    currentPath.value = '/'
    openFiles.value = []
    activeFilePath.value = null
    loading.value = false
    error.value = null
    saving.value = false
  }

  return {
    // State
    fileTree,
    expandedDirs,
    currentPath,
    openFiles,
    activeFilePath,
    activeFile,
    loading,
    error,
    saving,
    isEditorVisible,
    hasUnsavedChanges,
    
    // Actions
    loadFileTree,
    toggleDirectory,
    openFile,
    updateFileContent,
    saveFile,
    createFile,
    createDirectory,
    renameFile,
    deleteFile,
    deleteDirectory,
    closeFile,
    toggleEditor,
    showEditor,
    hideEditor,
    reset
  }
})
