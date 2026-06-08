import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 应用全局状态管理。
 *
 * 管理主题（亮色/暗色）、侧边栏折叠等 UI 状态。
 */
export const useAppStore = defineStore('app', () => {
  const isDark = ref(true)
  const sidebarCollapsed = ref(false)

  function toggleTheme(): void {
    isDark.value = !isDark.value
  }

  function toggleSidebar(): void {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return { isDark, sidebarCollapsed, toggleTheme, toggleSidebar }
})
