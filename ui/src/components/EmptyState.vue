<template>
  <div class="h-full flex items-center justify-center bg-gradient-to-br from-gray-50/50 via-blue-50/30 to-purple-50/30 animate-fade-in">
    <div class="text-center max-w-3xl px-6">
      <div class="mb-8">
        <div class="w-28 h-28 mx-auto mb-6 rounded-3xl bg-gradient-to-br from-primary-500 via-purple-600 to-pink-500 flex items-center justify-center shadow-2xl shadow-primary-500/40 animate-pulse-slow">
          <svg class="w-14 h-14 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
      </div>
      
      <h2 class="text-4xl font-bold text-gradient mb-4">
        Welcome to OpenCode UI
      </h2>
      
      <p class="text-gray-600 text-lg mb-8 max-w-xl mx-auto">
        Select a session from the sidebar or create a new one to start chatting with your AI-powered coding assistant.
      </p>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div class="card p-6 text-left hover:scale-105 transition-transform animate-slide-up">
          <div class="flex flex-col items-center text-center gap-3">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-lg">
              <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
              </svg>
            </div>
            <div>
              <h3 class="font-bold text-gray-900 mb-2">Smart Conversations</h3>
              <p class="text-sm text-gray-600">Chat with AI powered by OpenCode technology</p>
            </div>
          </div>
        </div>
        
        <div class="card p-6 text-left hover:scale-105 transition-transform animate-slide-up" style="animation-delay: 0.1s">
          <div class="flex flex-col items-center text-center gap-3">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center shadow-lg">
              <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
              </svg>
            </div>
            <div>
              <h3 class="font-bold text-gray-900 mb-2">Session Management</h3>
              <p class="text-sm text-gray-600">Organize conversations in separate sessions</p>
            </div>
          </div>
        </div>
        
        <div class="card p-6 text-left hover:scale-105 transition-transform animate-slide-up" style="animation-delay: 0.2s">
          <div class="flex flex-col items-center text-center gap-3">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center shadow-lg">
              <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
            </div>
            <div>
              <h3 class="font-bold text-gray-900 mb-2">Persistent History</h3>
              <p class="text-sm text-gray-600">Conversations saved automatically and locally</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-primary-100 to-purple-100 text-sm text-gray-700">
        <svg class="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="font-medium">Click the <strong class="text-gradient">"New Chat"</strong> button to get started</span>
      </div>
    </div>
  </div>
</template>

<script setup>
// Empty state component with modern design
</script>
