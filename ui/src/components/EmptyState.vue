<template>
  <div class="h-full flex items-center justify-center bg-gray-50">
    <div class="text-center">
      <div class="mb-6">
        <svg class="w-24 h-24 mx-auto text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </div>
      
      <h2 class="text-2xl font-semibold text-gray-700 mb-3">
        Welcome to OpenCode UI
      </h2>
      
      <p class="text-gray-500 mb-6 max-w-md mx-auto">
        Select a session from the sidebar or create a new one to start chatting with the AI assistant.
      </p>
      
      <div class="flex flex-col gap-4 max-w-md mx-auto">
        <div class="card p-4 text-left">
          <div class="flex items-start gap-3">
            <svg class="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
            <div>
              <h3 class="font-medium text-gray-900 mb-1">Smart Conversations</h3>
              <p class="text-sm text-gray-600">Chat with an AI assistant powered by OpenCode</p>
            </div>
          </div>
        </div>
        
        <div class="card p-4 text-left">
          <div class="flex items-start gap-3">
            <svg class="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
            </svg>
            <div>
              <h3 class="font-medium text-gray-900 mb-1">Session Management</h3>
              <p class="text-sm text-gray-600">Organize your conversations in separate sessions</p>
            </div>
          </div>
        </div>
        
        <div class="card p-4 text-left">
          <div class="flex items-start gap-3">
            <svg class="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            <div>
              <h3 class="font-medium text-gray-900 mb-1">Persistent Chat History</h3>
              <p class="text-sm text-gray-600">Your conversations are automatically saved locally</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Empty state component
</script>
