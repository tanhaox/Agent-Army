<template>
  <n-layout has-sider style="min-height: 100vh">
    <!-- 侧边栏 -->
    <n-layout-sider
      bordered
      :collapsed="sidebarCollapsed"
      collapse-mode="width"
      :collapsed-width="64"
      :width="240"
      show-trigger
      @collapse="toggleSidebar"
      @expand="toggleSidebar"
      :native-scrollbar="false"
    >
      <div class="sidebar-header">
        <span v-if="!sidebarCollapsed" class="sidebar-title">短剧AI</span>
        <span v-else class="sidebar-title-icon">剧</span>
      </div>
      <n-menu
        :collapsed="sidebarCollapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        :value="selectedMenu"
        @update:value="handleMenuClick"
      />
    </n-layout-sider>

    <!-- 右侧主体 -->
    <n-layout>
      <!-- 顶部导航栏 -->
      <n-layout-header bordered style="padding: 12px 24px; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <n-h3 style="margin: 0;">智能制片工厂</n-h3>
          <n-tag type="info" size="small">v0.1.0</n-tag>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
          <n-text depth="3" style="font-size: 13px;">
            {{ isDark ? '暗色模式' : '亮色模式' }}
          </n-text>
          <n-button quaternary circle @click="toggleTheme">
            <template #icon>
              <n-icon size="18">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path v-if="isDark" d="M12 3a9 9 0 1 0 9 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 0 1-4.4 2.26 5.403 5.403 0 0 1-3.14-9.8c-.44-.06-.9-.1-1.36-.1z" />
                  <path v-else d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58a.996.996 0 0 0-1.41 0 .996.996 0 0 0 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41L5.99 4.58zm12.37 12.37a.996.996 0 0 0-1.41 0 .996.996 0 0 0 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0a.996.996 0 0 0 0-1.41l-1.06-1.06zm1.06-10.96a.996.996 0 0 0 0-1.41.996.996 0 0 0-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06zM7.05 18.36a.996.996 0 0 0 0-1.41.996.996 0 0 0-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06z" />
                </svg>
              </n-icon>
            </template>
          </n-button>
        </div>
      </n-layout-header>

      <!-- 主内容区 -->
      <n-layout-content content-style="padding: 24px;">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NLayout,
  NLayoutSider,
  NLayoutHeader,
  NLayoutContent,
  NH3,
  NText,
  NTag,
  NButton,
  NIcon,
  NMenu,
  useMessage,
  type MenuOption,
} from 'naive-ui'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const router = useRouter()
const route = useRoute()
const isDark = computed(() => store.isDark)
const sidebarCollapsed = computed(() => store.sidebarCollapsed)
const toggleTheme = () => store.toggleTheme()
const toggleSidebar = () => store.toggleSidebar()
const message = useMessage()

/** 根据当前路由决定侧边栏选中项。 */
const selectedMenu = computed(() => {
  const pathMap: Record<string, string> = {
    '/': 'home',
    '/projects': 'projects',
    '/characters': 'characters',
    '/storyboards': 'storyboard',
    '/composition': 'composition',
    '/system-settings': 'system-settings',
  }
  // /projects/:id 也匹配 projects
  if (route.path.startsWith('/projects')) return 'projects'
  // /system-settings 和 /system-settings/:provider 都匹配
  if (route.path.startsWith('/system-settings')) return 'system-settings'
  return pathMap[route.path] || 'home'
})

/** 侧边栏菜单配置。 */
const menuOptions: MenuOption[] = [
  {
    label: '首页',
    key: 'home',
    icon: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor', width: '1em', height: '1em' }, [
      h('path', { d: 'M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z' }),
    ]),
  },
  {
    label: '项目管理',
    key: 'projects',
    icon: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor', width: '1em', height: '1em' }, [
      h('path', { d: 'M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V8h16v10z' }),
    ]),
  },
  {
    label: '剧本创作',
    key: 'scripts',
    icon: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor', width: '1em', height: '1em' }, [
      h('path', { d: 'M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z' }),
    ]),
  },
  {
    label: '角色库',
    key: 'characters',
    icon: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor', width: '1em', height: '1em' }, [
      h('path', { d: 'M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z' }),
    ]),
  },
  {
    label: '分镜设计',
    key: 'storyboard',
    icon: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor', width: '1em', height: '1em' }, [
      h('path', { d: 'M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 12.5v-9l6 4.5-6 4.5z' }),
    ]),
  },
  {
    label: '系统设置',
    key: 'system-settings',
    icon: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor', width: '1em', height: '1em' }, [
      h('path', { d: 'M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.49.49 0 0 0-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 0 0-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.07.62-.07.94s.02.64.07.94l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6A3.6 3.6 0 1 1 12 8.4a3.6 3.6 0 0 1 0 7.2z' }),
    ]),
  },
  {
    label: '合成中心',
    key: 'composition',
    icon: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor', width: '1em', height: '1em' }, [
      h('path', { d: 'M3 5v14h18V5H3zm8 12H5v-2h6v2zm0-4H5v-2h6v2zm0-4H5V7h6v2zm8 8h-6v-6h6v6z' }),
    ]),
  },
  {
    label: '发布中心',
    key: 'publish',
    icon: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor', width: '1em', height: '1em' }, [
      h('path', { d: 'M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z' }),
    ]),
  },
]

/** 处理侧边栏菜单点击。 */
function handleMenuClick(key: string): void {
  if (key === 'home') {
    router.push('/')
  } else if (key === 'projects') {
    router.push('/projects')
  } else if (key === 'scripts') {
    router.push('/projects')
  } else if (key === 'characters') {
    router.push('/characters')
  } else if (key === 'storyboard') {
    router.push('/storyboards')
  } else if (key === 'composition') {
    router.push('/composition')
  } else if (key === 'system-settings') {
    router.push('/system-settings')
  } else {
    const label = menuOptions.find((m) => m.key === key)?.label || '功能'
    message.info(`${label} 开发中...`)
  }
}
</script>

<style scoped>
.sidebar-header {
  padding: 16px;
  text-align: center;
  border-bottom: 1px solid var(--n-border-color);
}

.sidebar-title {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sidebar-title-icon {
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>
