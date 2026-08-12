import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { User, LoginRequest, RegisterRequest } from '@/types'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<User | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isDoctor = computed(() => userInfo.value?.role === 'doctor')
  const isAdmin = computed(() => userInfo.value?.role === 'admin')

  async function login(data: LoginRequest) {
    try {
      const res = await authApi.login(data)
      token.value = res.access_token
      localStorage.setItem('token', res.access_token)
      await getUserInfo()
      ElMessage.success('登录成功')
      return true
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '登录失败')
      return false
    }
  }

  async function register(data: RegisterRequest) {
    try {
      await authApi.register(data)
      ElMessage.success('注册成功，请登录')
      return true
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '注册失败')
      return false
    }
  }

  async function getUserInfo() {
    try {
      const res = await authApi.getCurrentUser()
      userInfo.value = res
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  // 初始化时获取用户信息
  if (token.value) {
    getUserInfo()
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isDoctor,
    isAdmin,
    login,
    register,
    getUserInfo,
    logout,
  }
})
