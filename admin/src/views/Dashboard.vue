<template>
  <div class="dashboard">
    <h2>仪表盘</h2>
    
    <a-spin :loading="loading" style="width: 100%;">
      <a-row :gutter="24">
        <a-col :span="6">
          <a-card class="stat-card">
            <a-statistic
              title="总用户数"
              :value="stats.total_users"
            >
              <template #prefix>
                <icon-user-group style="color: rgb(var(--primary-6));" />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        
        <a-col :span="6">
          <a-card class="stat-card">
            <a-statistic
              title="活跃用户"
              :value="stats.active_users"
            >
              <template #prefix>
                <icon-check-circle style="color: rgb(var(--success-6));" />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        
        <a-col :span="6">
          <a-card class="stat-card">
            <a-statistic
              title="总书签数"
              :value="stats.total_bookmarks"
            >
              <template #prefix>
                <icon-bookmark style="color: rgb(var(--warning-6));" />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        
        <a-col :span="6">
          <a-card class="stat-card">
            <a-statistic
              title="今日同步"
              :value="stats.today_syncs"
            >
              <template #prefix>
                <icon-sync style="color: rgb(var(--arcoblue-6));" />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
      </a-row>
      
      <a-row :gutter="24" style="margin-top: 24px;">
        <a-col :span="12">
          <a-card title="系统状态">
            <a-descriptions :column="1" bordered>
              <a-descriptions-item label="禁用用户">
                {{ stats.disabled_users }}
              </a-descriptions-item>
              <a-descriptions-item label="总同步次数">
                {{ stats.total_syncs }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>
        
        <a-col :span="12">
          <a-card title="快捷操作">
            <a-space>
              <a-button type="primary" @click="$router.push('/users')">
                <template #icon><icon-user-group /></template>
                管理用户
              </a-button>
              <a-button @click="fetchStats">
                <template #icon><icon-refresh /></template>
                刷新数据
              </a-button>
            </a-space>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import api from '../api'
import {
  IconUserGroup,
  IconCheckCircle,
  IconBookmark,
  IconSync,
  IconRefresh
} from '@arco-design/web-vue/es/icon'

const loading = ref(false)
const stats = ref({
  total_users: 0,
  active_users: 0,
  disabled_users: 0,
  total_bookmarks: 0,
  total_syncs: 0,
  today_syncs: 0
})

async function fetchStats() {
  loading.value = true
  try {
    const response = await api.get('/admin/stats')
    stats.value = response.data
  } catch (error) {
    Message.error('获取统计数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.dashboard h2 {
  margin: 0 0 24px;
}

.stat-card {
  text-align: center;
}
</style>
