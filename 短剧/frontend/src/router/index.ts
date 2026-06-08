import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/script-generator',
    redirect: '/projects',
  },
  {
    path: '/characters',
    name: 'CharacterManager',
    component: () => import('../views/CharacterManager.vue'),
    meta: { title: '角色库' },
  },
  {
    path: '/storyboards',
    name: 'StoryboardManager',
    component: () => import('../views/StoryboardManager.vue'),
    meta: { title: '分镜设计' },
  },
  {
    path: '/composition',
    name: 'Composition',
    component: () => import('../views/CompositionView.vue'),
    meta: { title: '合成中心' },
  },
  {
    path: '/system-settings',
    name: 'SystemSettings',
    component: () => import('../views/SystemSettings.vue'),
    meta: { title: '系统设置' },
  },
  {
    path: '/system-settings/:provider',
    name: 'ProviderConfig',
    component: () => import('../views/ProviderConfig.vue'),
    meta: { title: '服务商配置' },
  },
  {
    path: '/projects',
    name: 'ProjectList',
    component: () => import('../views/ProjectList.vue'),
    meta: { title: '项目管理' },
  },
  {
    path: '/projects/:id',
    name: 'ProjectDetail',
    component: () => import('../views/ProjectWorkspace.vue'),
    meta: { title: '项目工作区' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  let title = (to.meta.title as string) || '短剧AI'
  if (to.name === 'ProviderConfig') {
    title = '服务商配置'
  }
  document.title = `${title} - 智能制片工厂`
})

export default router
