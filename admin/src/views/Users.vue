<template>
  <div class="users">
    <div class="page-header">
      <h2>用户管理</h2>
      <a-button @click="fetchUsers">
        <template #icon><icon-refresh /></template>
        刷新
      </a-button>
    </div>
    
    <a-table
      :columns="columns"
      :data="users"
      :loading="loading"
      :pagination="{ pageSize: 20 }"
      row-key="id"
    >
      <template #status="{ record }">
        <a-tag :color="record.status === 'active' ? 'green' : 'red'">
          {{ record.status === 'active' ? '正常' : '禁用' }}
        </a-tag>
      </template>
      
      <template #is_admin="{ record }">
        <a-tag v-if="record.is_admin" color="blue">管理员</a-tag>
        <span v-else>-</span>
      </template>
      
      <template #last_sync_at="{ record }">
        {{ record.last_sync_at ? formatDate(record.last_sync_at) : '从未同步' }}
      </template>
      
      <template #created_at="{ record }">
        {{ formatDate(record.created_at) }}
      </template>
      
      <template #actions="{ record }">
        <a-space>
          <a-button
            type="text"
            size="small"
            @click="$router.push(`/user/${record.id}`)"
          >
            详情
          </a-button>
          <a-button
            type="text"
            size="small"
            :status="record.status === 'active' ? 'danger' : 'success'"
            @click="toggleStatus(record)"
          >
            {{ record.status === 'active' ? '禁用' : '启用' }}
          </a-button>
          <a-popconfirm
            content="确定删除此用户？数据将无法恢复！"
            @ok="deleteUser(record.id)"
          >
            <a-button type="text" size="small" status="danger">
              删除
            </a-button>
          </a-popconfirm>
        </a-space>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import api from '../api'
import { IconRefresh } from '@arco-design/web-vue/es/icon'

const loading = ref(false)
const users = ref([])

const columns = [
  { title: 'ID', dataIndex: 'id', width: 80 },
  { title: '邮箱', dataIndex: 'email' },
  { title: '状态', slotName: 'status', width: 100 },
  { title: '管理员', slotName: 'is_admin', width: 100 },
  { title: '书签数', dataIndex: 'bookmark_count', width: 100 },
  { title: '最后同步', slotName: 'last_sync_at', width: 160 },
  { title: '注册时间', slotName: 'created_at', width: 160 },
  { title: '操作', slotName: 'actions', width: 180 }
]

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

async function fetchUsers() {
  loading.value = true
  try {
    const response = await api.get('/admin/users')
    users.value = response.data
  } catch (error) {
    Message.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

async function toggleStatus(user) {
  const newStatus = user.status === 'active' ? 'disabled' : 'active'
  try {
    await api.put(`/admin/user/${user.id}`, { status: newStatus })
    Message.success('操作成功')
    fetchUsers()
  } catch (error) {
    Message.error('操作失败')
  }
}

async function deleteUser(userId) {
  try {
    await api.delete(`/admin/user/${userId}`)
    Message.success('删除成功')
    fetchUsers()
  } catch (error) {
    Message.error(error.response?.data?.detail || '删除失败')
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
}
</style>
