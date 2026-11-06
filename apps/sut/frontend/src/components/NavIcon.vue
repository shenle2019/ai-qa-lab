<script setup>
defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 16 },
})

// 统一一套 24×24 / stroke 2 的线性图标，避免用 Unicode 字符当图标
// （字重、基线、大小不一致，是界面显得简陋的主要来源）。
const PATHS = {
  projects: 'M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z',
  'ai-config':
    'M12 3l2.1 4.6 4.9.6-3.6 3.4.9 4.9L12 14.9 7.7 16.5l.9-4.9L5 8.2l4.9-.6z',
  logs: 'M12 21a9 9 0 100-18 9 9 0 000 18zM12 7v5l3 3',
  users: 'M12 12a4 4 0 100-8 4 4 0 000 8zM4 21c0-4 3.6-6 8-6s8 2 8 6',
  overview: 'M12 21a9 9 0 100-18 9 9 0 000 18zM12 15a3 3 0 100-6 3 3 0 000 6z',
  requirements: 'M4 6h16M4 12h16M4 18h10',
  functional: 'M4 4h16v16H4zM8 12l2.5 2.5L16 9',
  kb: 'M4 5a2 2 0 012-2h11v16H6a2 2 0 00-2 2zM4 5v14',
  environments:
    'M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.7 1.7 0 00.3 1.9l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-2.9 1.2V21a2 2 0 11-4 0v-.1A1.7 1.7 0 006.9 19l-.1.1a2 2 0 11-2.8-2.8l.1-.1A1.7 1.7 0 003 15a2 2 0 010-4 1.7 1.7 0 001.2-1.7l-.1-.1a2 2 0 112.8-2.8l.1.1A1.7 1.7 0 009 5.6V5a2 2 0 014 0v.6A1.7 1.7 0 0018.9 7l.1-.1a2 2 0 112.8 2.8l-.1.1A1.7 1.7 0 0021 12a2 2 0 010 3z',
  api: 'M8 9l-4 3 4 3M16 9l4 3-4 3M13 5l-2 14',
  ui: 'M3 5h18v11H3zM8 20h8',
  modules: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
  members: 'M9 11a3.5 3.5 0 100-7 3.5 3.5 0 000 7zM2 20c0-3.3 3.1-5 7-5s7 1.7 7 5M17 4.5a3.5 3.5 0 010 7M18 20c0-2.2-.7-3.8-2-5',
  tools: 'M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM16 14v6M14 17h4',
  key: 'M15 3a6 6 0 00-5.2 9L3 19v2h3v-2h2v-2h2l1.8-1.8A6 6 0 0015 3zM17.5 6.5h.01',
  search: 'M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.3-4.3',
  plus: 'M12 5v14M5 12h14',
  refresh: 'M21 12a9 9 0 11-3-6.7M21 4v5h-5',
  chevron: 'M9 6l6 6-6 6',
}
</script>

<template>
  <svg
    class="nav-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="PATHS[name] || PATHS.projects" />
  </svg>
</template>
