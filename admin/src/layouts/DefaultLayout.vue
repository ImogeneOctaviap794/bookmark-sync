<template>
  <a-layout class="layout">
    <a-layout-sider
      collapsible
      :collapsed="collapsed"
      @collapse="collapsed = $event"
      :width="220"
      class="sider"
    >
      <div class="logo">
        <icon-bookmark style="font-size: 24px;" />
        <span v-if="!collapsed">书签同步管理</span>
      </div>
      <a-menu
        :selected-keys="[currentRoute]"
        @menu-item-click="handleMenuClick"
        :default-open-keys="['menu']"
      >
        <a-menu-item key="Dashboard">
          <template #icon><icon-dashboard /></template>
          仪表盘
        </a-menu-item>
        <a-menu-item key="Users">
          <template #icon><icon-user-group /></template>
          用户管理
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    
    <a-layout>
      <a-layout-header class="header">
        <div class="header-right">
          <span class="admin-email">{{ authStore.email }}</span>
          <a-button type="text" @click="handleLogout">
            <template #icon><icon-export /></template>
            退出
          </a-button>
        </div>
      </a-layout-header>
      
      <a-layout-content class="content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import {
  IconDashboard,
  IconUserGroup,
  IconExport,
  IconBookmark
} from '@arco-design/web-vue/es/icon'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const collapsed = ref(false)

const currentRoute = computed(() => route.name)

function handleMenuClick(key) {
  router.push({ name: key })
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout {
  min-height: 100vh;
}

.sider {
  background: #fff;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: rgb(var(--primary-6));
  border-bottom: 1px solid var(--color-border);
}

.header {
  background: #fff;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  border-bottom: 1px solid var(--color-border);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.admin-email {
  color: var(--color-text-2);
}

.content {
  margin: 24px;
  padding: 24px;
  background: #fff;
  border-radius: 4px;
  min-height: calc(100vh - 64px - 48px);
}
</style>
