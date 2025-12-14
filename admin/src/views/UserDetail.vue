<template>
  <div class="user-detail">
    <div class="page-header">
      <a-space>
        <a-button @click="$router.back()">
          <template #icon><icon-left /></template>
          返回
        </a-button>
        <h2>用户详情</h2>
      </a-space>
    </div>
    
    <a-spin :loading="loading" style="width: 100%;">
      <a-row :gutter="24">
        <a-col :span="8">
          <a-card title="基本信息">
            <a-descriptions :column="1" bordered>
              <a-descriptions-item label="ID">
                {{ user.id }}
              </a-descriptions-item>
              <a-descriptions-item label="邮箱">
                {{ user.email }}
              </a-descriptions-item>
              <a-descriptions-item label="状态">
                <a-tag :color="user.status === 'active' ? 'green' : 'red'">
                  {{ user.status === 'active' ? '正常' : '禁用' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="管理员">
                {{ user.is_admin ? '是' : '否' }}
              </a-descriptions-item>
              <a-descriptions-item label="书签数">
                {{ user.bookmark_count }}
              </a-descriptions-item>
              <a-descriptions-item label="同步次数">
                {{ user.sync_count }}
              </a-descriptions-item>
              <a-descriptions-item label="最后同步">
                {{ user.last_sync_at ? formatDate(user.last_sync_at) : '从未同步' }}
              </a-descriptions-item>
              <a-descriptions-item label="注册时间">
                {{ formatDate(user.created_at) }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>
        
        <a-col :span="16">
          <a-card title="书签列表" style="margin-bottom: 24px;">
            <a-table
              :columns="bookmarkColumns"
              :data="user.bookmarks"
              :pagination="{ pageSize: 10 }"
              size="small"
            >
              <template #url="{ record }">
                <a :href="record.url" target="_blank" class="url-link">
                  {{ truncate(record.url, 50) }}
                </a>
              </template>
            </a-table>
          </a-card>
          
          <a-card title="同步记录">
            <a-table
              :columns="syncColumns"
              :data="user.recent_syncs"
              :pagination="false"
              size="small"
            >
              <template #action="{ record }">
                <a-tag>{{ record.action }}</a-tag>
              </template>
              <template #created_at="{ record }">
                {{ formatDate(record.created_at) }}
              </template>
            </a-table>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import api from '../api'
import { IconLeft } from '@arco-design/web-vue/es/icon'

const route = useRoute()
const loading = ref(false)

const user = ref({
  id: 0,
  email: '',
  status: '',
  is_admin: false,
  bookmark_count: 0,
  sync_count: 0,
  last_sync_at: null,
  created_at: '',
  bookmarks: [],
  recent_syncs: []
})

const bookmarkColumns = [
  { title: '标题', dataIndex: 'title', ellipsis: true },
  { title: 'URL', slotName: 'url' },
  { title: '文件夹', dataIndex: 'folderPath', ellipsis: true }
]

const syncColumns = [
  { title: '操作', slotName: 'action', width: 80 },
  { title: '添加', dataIndex: 'added', width: 60 },
  { title: '更新', dataIndex: 'updated', width: 60 },
  { title: '删除', dataIndex: 'deleted', width: 60 },
  { title: '时间', slotName: 'created_at' }
]

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

function truncate(str, len) {
  if (!str) return ''
  return str.length > len ? str.slice(0, len) + '...' : str
}

async function fetchUser() {
  loading.value = true
  try {
    const response = await api.get(`/admin/user/${route.params.id}`)
    user.value = response.data
  } catch (error) {
    Message.error('获取用户详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchUser()
})
</script>

<style scoped>
.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
}

.url-link {
  color: rgb(var(--primary-6));
  text-decoration: none;
}

.url-link:hover {
  text-decoration: underline;
}
</style>
