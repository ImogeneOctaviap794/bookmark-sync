<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <icon-bookmark style="font-size: 48px; color: rgb(var(--primary-6));" />
        <h1>书签同步管理后台</h1>
      </div>
      
      <a-form
        :model="form"
        @submit="handleSubmit"
        layout="vertical"
      >
        <a-form-item field="email" label="邮箱">
          <a-input
            v-model="form.email"
            placeholder="请输入管理员邮箱"
            size="large"
          >
            <template #prefix><icon-user /></template>
          </a-input>
        </a-form-item>
        
        <a-form-item field="password" label="密码">
          <a-input-password
            v-model="form.password"
            placeholder="请输入密码"
            size="large"
          >
            <template #prefix><icon-lock /></template>
          </a-input-password>
        </a-form-item>
        
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            long
            size="large"
            :loading="loading"
          >
            登录
          </a-button>
        </a-form-item>
      </a-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { useAuthStore } from '../stores/auth'
import { IconBookmark, IconUser, IconLock } from '@arco-design/web-vue/es/icon'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  email: '',
  password: ''
})

const loading = ref(false)

async function handleSubmit() {
  if (!form.email || !form.password) {
    Message.warning('请填写邮箱和密码')
    return
  }
  
  loading.value = true
  try {
    await authStore.login(form.email, form.password)
    Message.success('登录成功')
    router.push('/')
  } catch (error) {
    Message.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  margin: 16px 0 0;
  font-size: 24px;
  color: var(--color-text-1);
}
</style>
