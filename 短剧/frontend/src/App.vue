<template>
  <n-config-provider :theme="isDark ? darkTheme : undefined">
    <n-global-style />
    <n-message-provider>
      <n-notification-provider>
        <AppLayout />
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { darkTheme, NConfigProvider, NGlobalStyle, NMessageProvider, NNotificationProvider } from 'naive-ui'
import { useAppStore } from './stores/app'
import AppLayout from './components/AppLayout.vue'

const store = useAppStore()
const isDark = computed(() => store.isDark)
</script>
