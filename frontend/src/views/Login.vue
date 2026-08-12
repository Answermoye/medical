<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="grid-pattern"></div>
    </div>

    <!-- 左侧品牌区 -->
    <div class="login-hero">
      <div class="hero-content">
        <div class="brand-mark">
          <div class="brand-icon">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="24" cy="24" r="22" stroke="url(#brandGradient)" stroke-width="2"/>
              <path d="M24 12v24M16 20l8-8 8 8" stroke="url(#brandGradient)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
              <circle cx="24" cy="32" r="3" fill="url(#brandGradient)"/>
              <defs>
                <linearGradient id="brandGradient" x1="0" y1="0" x2="48" y2="48">
                  <stop stop-color="#0EA5E9"/>
                  <stop offset="1" stop-color="#6366F1"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <span class="brand-name">MedicalGuide</span>
        </div>

        <h1 class="hero-title text-display">
          <span class="title-line">智能医疗</span>
          <span class="title-line accent gradient-text">触手可及</span>
        </h1>

        <p class="hero-description">
          基于 AI 多智能体架构，为您提供专业的医疗导诊、报告解读和健康咨询服务。
        </p>

        <div class="hero-features">
          <div class="feature-item glass-card">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 12l2 2 4-4"/>
                <circle cx="12" cy="12" r="10"/>
              </svg>
            </div>
            <div class="feature-text">
              <span class="feature-label">智能导诊</span>
              <span class="feature-desc">精准症状分析</span>
            </div>
          </div>

          <div class="feature-item glass-card">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
            </div>
            <div class="feature-text">
              <span class="feature-label">报告解读</span>
              <span class="feature-desc">化验单一键分析</span>
            </div>
          </div>

          <div class="feature-item glass-card">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
            </div>
            <div class="feature-text">
              <span class="feature-label">健康咨询</span>
              <span class="feature-desc">24小时在线问诊</span>
            </div>
          </div>
        </div>

        <div class="hero-stats">
          <div class="stat-item">
            <span class="stat-number gradient-text-blue">98%</span>
            <span class="stat-label">诊断准确率</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number gradient-text-blue">50K+</span>
            <span class="stat-label">服务用户</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number gradient-text-blue">24/7</span>
            <span class="stat-label">在线服务</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧登录表单 -->
    <div class="login-form-section">
      <div class="form-wrapper glass-card">
        <div class="form-header">
          <h2 class="form-title text-display">欢迎回来</h2>
          <p class="form-subtitle">登录您的账户以继续</p>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          size="large"
          class="login-form"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              class="custom-input"
            >
              <template #prefix>
                <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              show-password
              class="custom-input"
              @keyup.enter="handleLogin"
            >
              <template #prefix>
                <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
              </template>
            </el-input>
          </el-form-item>

          <div class="form-options">
            <el-checkbox v-model="rememberMe" class="remember-checkbox">
              记住我
            </el-checkbox>
            <a href="#" class="forgot-link">忘记密码？</a>
          </div>

          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              class="login-btn"
              @click="handleLogin"
            >
              <span v-if="!loading">登 录</span>
              <span v-else>登录中...</span>
            </el-button>
          </el-form-item>
        </el-form>

        <div class="form-footer">
          <span class="footer-text">还没有账号？</span>
          <router-link to="/register" class="register-link">
            立即注册
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </router-link>
        </div>

        <div class="form-divider">
          <span class="divider-text">或</span>
        </div>

        <div class="social-login">
          <button class="social-btn glass-card" title="微信登录">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18z"/>
              <path d="M23.96 14.785c0-3.24-3.239-5.868-7.015-5.868-3.927 0-7.016 2.628-7.016 5.868 0 3.24 3.089 5.868 7.016 5.868.772 0 1.544-.103 2.24-.33a.673.673 0 0 1 .557.076l1.483.87a.258.258 0 0 0 .13.04c.126 0 .227-.103.227-.228 0-.056-.023-.11-.037-.165l-.304-1.152a.46.46 0 0 1 .166-.518c1.423-1.05 2.553-2.772 2.553-4.461zm-9.463-1.18c-.506 0-.916-.416-.916-.928 0-.512.41-.928.916-.928.506 0 .916.416.916.928 0 .512-.41.928-.916.928zm4.896 0c-.506 0-.916-.416-.916-.928 0-.512.41-.928.916-.928.506 0 .916.416.916.928 0 .512-.41.928-.916.928z"/>
            </svg>
          </button>
          <button class="social-btn glass-card" title="支付宝登录">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M21.422 15.358c-1.406-.586-3.036-1.278-4.866-2.076.662-1.312 1.174-2.818 1.522-4.484h-4.02v-1.34h5.088V6.134h-5.088V4h-2.132s.036-.202.036-.408c0-.986-.406-1.612-1.298-1.612-.892 0-1.298.626-1.298 1.612 0 .206.036.408.036.408H9.262v1.324H4.174v1.324h5.088v1.34H4.922v1.324h8.716c-.278 1.146-.692 2.214-1.216 3.152-2.244-.968-4.686-1.916-6.722-2.512C3.236 12.108 2 14.068 2 16.308c0 3.174 3.708 5.692 9.5 5.692 5.244 0 9.024-2.206 9.922-5.096.378-.032.756-.076 1.128-.132a12.76 12.76 0 0 0 1.102-1.414h-2.23zm-12.92 2.638c-2.708-.564-4.136-1.674-4.136-3.024 0-1.574 1.772-2.978 4.136-3.024v6.048zm7.456-7.88c.536-.96.936-2.054 1.2-3.238 1.544.668 2.92 1.348 4.176 2.002-1.074 1.998-2.874 3.398-5.376 1.236z"/>
            </svg>
          </button>
          <button class="social-btn glass-card" title="手机号登录">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
              <line x1="12" y1="18" x2="12.01" y2="18"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref<FormInstance>()
const loading = ref(false)
const rememberMe = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' },
  ],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  const success = await userStore.login(form)
  loading.value = false

  if (success) {
    router.push('/')
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg);
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.3;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: var(--gradient-primary);
  top: -200px;
  right: -100px;
  animation: float 10s ease-in-out infinite;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
  bottom: -100px;
  left: -50px;
  animation: float 8s ease-in-out infinite reverse;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #D4AF37 0%, #F0D060 100%);
  top: 50%;
  left: 40%;
  animation: float 12s ease-in-out infinite;
  opacity: 0.15;
}

.grid-pattern {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
  background-size: 60px 60px;
}

/* 左侧英雄区 */
.login-hero {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-12);
  position: relative;
  z-index: 1;
}

.hero-content {
  max-width: 520px;
}

/* 品牌标识 */
.brand-mark {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-12);
}

.brand-icon {
  width: 48px;
  height: 48px;
}

.brand-icon svg {
  width: 100%;
  height: 100%;
}

.brand-name {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  letter-spacing: var(--tracking-wide);
}

/* 标题 */
.hero-title {
  font-size: var(--text-6xl);
  font-weight: var(--weight-bold);
  line-height: var(--leading-tight);
  color: var(--color-text);
  margin-bottom: var(--space-6);
}

.title-line {
  display: block;
}

.title-line.accent {
  font-style: italic;
}

/* 描述 */
.hero-description {
  font-size: var(--text-lg);
  line-height: var(--leading-relaxed);
  color: var(--color-text-muted);
  margin-bottom: var(--space-10);
}

/* 特性列表 */
.hero-features {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-bottom: var(--space-10);
}

.feature-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  cursor: default;
}

.feature-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-primary);
  border-radius: var(--radius-lg);
  color: white;
  flex-shrink: 0;
}

.feature-icon svg {
  width: 22px;
  height: 22px;
}

.feature-text {
  display: flex;
  flex-direction: column;
}

.feature-label {
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  font-size: var(--text-base);
}

.feature-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-top: 2px;
}

/* 统计数据 */
.hero-stats {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-5) var(--space-6);
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-number {
  font-family: var(--font-display);
  font-size: var(--text-3xl);
  font-weight: var(--weight-bold);
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-top: var(--space-1);
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: var(--color-border);
}

/* 右侧表单区 */
.login-form-section {
  width: 520px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-12);
  position: relative;
  z-index: 1;
}

.form-wrapper {
  width: 100%;
  max-width: 420px;
  padding: var(--space-10);
}

/* 表单头部 */
.form-header {
  margin-bottom: var(--space-8);
}

.form-title {
  font-size: var(--text-3xl);
  font-weight: var(--weight-bold);
  color: var(--color-text);
  margin-bottom: var(--space-2);
}

.form-subtitle {
  font-size: var(--text-base);
  color: var(--color-text-muted);
}

/* 表单样式 */
.login-form {
  margin-bottom: var(--space-6);
}

.login-form :deep(.el-form-item__label) {
  font-family: var(--font-body);
  font-weight: var(--weight-medium);
  color: var(--color-text-secondary);
  padding-bottom: var(--space-2);
}

.input-icon {
  width: 18px;
  height: 18px;
  color: var(--color-text-muted);
  margin-right: var(--space-2);
}

/* 表单选项 */
.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-6);
}

.remember-checkbox :deep(.el-checkbox__label) {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.remember-checkbox :deep(.el-checkbox__inner) {
  background: transparent;
  border-color: var(--color-border-light);
}

.remember-checkbox :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background: var(--gradient-primary);
  border-color: transparent;
}

.forgot-link {
  font-size: var(--text-sm);
  color: var(--color-primary-light);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.forgot-link:hover {
  color: var(--color-primary);
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  height: 52px;
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tracking-wide);
  border-radius: var(--radius-lg);
}

/* 表单底部 */
.form-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  margin-bottom: var(--space-8);
}

.footer-text {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.register-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--color-primary-light);
  text-decoration: none;
  transition: all var(--transition-fast);
}

.register-link svg {
  width: 16px;
  height: 16px;
  transition: transform var(--transition-fast);
}

.register-link:hover {
  color: var(--color-primary);
}

.register-link:hover svg {
  transform: translateX(4px);
}

/* 分隔线 */
.form-divider {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}

.form-divider::before,
.form-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--color-border);
}

.divider-text {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

/* 社交登录 */
.social-login {
  display: flex;
  justify-content: center;
  gap: var(--space-4);
}

.social-btn {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--color-text-secondary);
  padding: 0;
}

.social-btn svg {
  width: 24px;
  height: 24px;
}

.social-btn:hover {
  color: var(--color-primary-light);
  border-color: var(--color-border-glow);
  box-shadow: var(--shadow-glow);
}

/* 响应式 */
@media (max-width: 1024px) {
  .login-hero {
    display: none;
  }

  .login-form-section {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .login-form-section {
    padding: var(--space-6);
  }

  .form-wrapper {
    max-width: 100%;
    padding: var(--space-6);
  }

  .hero-title {
    font-size: var(--text-4xl);
  }
}
</style>
