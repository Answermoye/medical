<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapsed ? 'var(--sidebar-collapsed)' : 'var(--sidebar-width)'" class="layout-aside">
      <div class="aside-header">
        <div class="logo-wrapper" @click="router.push('/')">
          <svg class="logo-icon" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="16" cy="16" r="14" stroke="url(#logoGradient)" stroke-width="2"/>
            <path d="M16 8v16M10 14l6-6 6 6" stroke="url(#logoGradient)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="16" cy="22" r="2" fill="url(#logoGradient)"/>
            <defs>
              <linearGradient id="logoGradient" x1="0" y1="0" x2="32" y2="32">
                <stop stop-color="#0EA5E9"/>
                <stop offset="1" stop-color="#6366F1"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <transition name="fade">
          <div v-if="!isCollapsed" class="brand-text">
            <span class="brand-name text-display">MedicalGuide</span>
            <span class="brand-tagline">AI 导诊系统</span>
          </div>
        </transition>
        <button class="collapse-btn" @click="isCollapsed = !isCollapsed" :title="isCollapsed ? '展开侧边栏' : '收起侧边栏'">
          <svg v-if="!isCollapsed" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 17l-5-5 5-5M18 17l-5-5 5-5"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M13 7l5 5-5 5M6 7l5 5-5 5"/>
          </svg>
        </button>
      </div>

      <nav class="aside-nav">
        <router-link
          to="/"
          :class="['nav-item', { active: route.path === '/' }]"
        >
          <div class="nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <transition name="fade">
            <span v-if="!isCollapsed" class="nav-label">智能对话</span>
          </transition>
          <transition name="fade">
            <span v-if="!isCollapsed && route.path === '/'" class="nav-indicator"></span>
          </transition>
        </router-link>

        <router-link
          v-if="userStore.isDoctor || userStore.isAdmin"
          to="/review"
          :class="['nav-item', { active: route.path === '/review' }]"
        >
          <div class="nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 12l2 2 4-4"/>
              <circle cx="12" cy="12" r="10"/>
            </svg>
          </div>
          <transition name="fade">
            <span v-if="!isCollapsed" class="nav-label">医生审核</span>
          </transition>
          <transition name="fade">
            <span v-if="!isCollapsed && route.path === '/review'" class="nav-indicator"></span>
          </transition>
        </router-link>

        <router-link
          v-if="userStore.isAdmin"
          to="/knowledge-base"
          :class="['nav-item', { active: route.path === '/knowledge-base' }]"
        >
          <div class="nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
          </div>
          <transition name="fade">
            <span v-if="!isCollapsed" class="nav-label">知识库管理</span>
          </transition>
          <transition name="fade">
            <span v-if="!isCollapsed && route.path === '/knowledge-base'" class="nav-indicator"></span>
          </transition>
        </router-link>
      </nav>

      <div class="aside-footer">
        <el-dropdown v-if="!isCollapsed" trigger="click" @command="handleCommand">
          <div class="user-info">
            <div class="user-avatar">
              <span class="avatar-text">{{ getInitial(userStore.userInfo?.username) }}</span>
            </div>
            <div class="user-detail">
              <span class="username">{{ userStore.userInfo?.username || '用户' }}</span>
              <span class="user-role">{{ getRoleLabel(userStore.userInfo?.role) }}</span>
            </div>
            <svg class="dropdown-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 9l6 6 6-6"/>
            </svg>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="menu-icon">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                  <polyline points="16 17 21 12 16 7"/>
                  <line x1="21" y1="12" x2="9" y2="12"/>
                </svg>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <button v-else class="user-avatar-collapsed" @click="handleLogout" title="退出登录">
          <span class="avatar-text">{{ getInitial(userStore.userInfo?.username) }}</span>
        </button>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-main class="layout-main">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isCollapsed = ref(false)

function getInitial(name?: string): string {
  if (!name) return 'U'
  return name.charAt(0).toUpperCase()
}

function getRoleLabel(role?: string): string {
  const labels: Record<string, string> = {
    patient: '患者',
    doctor: '医生',
    admin: '管理员',
  }
  return labels[role || ''] || '用户'
}

function handleCommand(command: string) {
  if (command === 'logout') {
    handleLogout()
  }
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    userStore.logout()
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  background: var(--color-bg);
}

/* 侧边栏 */
.layout-aside {
  background: var(--color-bg-elevated);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-normal);
  overflow: hidden;
  position: relative;
  z-index: 10;
  border-right: 1px solid var(--color-border);
}

/* 侧边栏装饰 */
.layout-aside::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 1px;
  height: 100%;
  background: linear-gradient(
    180deg,
    transparent 0%,
    rgba(14, 165, 233, 0.3) 30%,
    rgba(99, 102, 241, 0.1) 70%,
    transparent 100%
  );
}

/* 侧边栏头部 */
.aside-header {
  display: flex;
  align-items: center;
  padding: var(--space-5) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  gap: var(--space-3);
  min-height: 72px;
  position: relative;
  z-index: 1;
}

.logo-wrapper {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid var(--color-border-light);
}

.logo-wrapper:hover {
  border-color: var(--color-border-glow);
  box-shadow: var(--shadow-glow);
}

.logo-icon {
  width: 24px;
  height: 24px;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-name {
  font-size: var(--text-lg);
  font-weight: var(--weight-bold);
  color: var(--color-text);
  letter-spacing: var(--tracking-tight);
  white-space: nowrap;
}

.brand-tagline {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
}

.collapse-btn {
  margin-left: auto;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: var(--color-surface);
  color: var(--color-text);
}

.collapse-btn svg {
  width: 18px;
  height: 18px;
}

/* 导航菜单 */
.aside-nav {
  flex: 1;
  padding: var(--space-4) var(--space-3);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  position: relative;
  z-index: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  color: var(--color-text-muted);
  text-decoration: none;
  transition: all var(--transition-normal);
  position: relative;
  min-height: 48px;
}

.nav-item:hover {
  background: var(--color-surface);
  color: var(--color-text);
}

.nav-item.active {
  background: var(--gradient-primary);
  color: white;
  box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
}

.nav-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-icon svg {
  width: 20px;
  height: 20px;
}

.nav-label {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  white-space: nowrap;
}

.nav-indicator {
  position: absolute;
  right: var(--space-3);
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: white;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
}

/* 侧边栏底部 */
.aside-footer {
  padding: var(--space-4);
  border-top: 1px solid var(--color-border);
  position: relative;
  z-index: 1;
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  cursor: pointer;
  padding: var(--space-3);
  border-radius: var(--radius-lg);
  transition: background var(--transition-fast);
}

.user-info:hover {
  background: var(--color-surface);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-text {
  font-family: var(--font-display);
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  color: white;
}

.user-detail {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.username {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
}

.dropdown-icon {
  width: 16px;
  height: 16px;
  color: var(--color-text-muted);
  transition: transform var(--transition-fast);
}

.menu-icon {
  width: 16px;
  height: 16px;
  margin-right: var(--space-2);
}

.user-avatar-collapsed {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border: none;
  margin: 0 auto;
  transition: all var(--transition-fast);
}

.user-avatar-collapsed:hover {
  transform: scale(1.05);
  box-shadow: var(--shadow-glow);
}

/* 主内容区 */
.layout-main {
  padding: 0;
  background: var(--color-bg);
  overflow: hidden;
  position: relative;
}

/* 页面过渡动画 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: all var(--transition-normal);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 响应式 */
@media (max-width: 768px) {
  .layout-aside {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 1000;
    transform: translateX(-100%);
    transition: transform var(--transition-normal);
  }

  .layout-aside.is-open {
    transform: translateX(0);
  }
}
</style>
