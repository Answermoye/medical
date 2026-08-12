<template>
  <el-container class="chat-container">
    <!-- 左侧会话列表 -->
    <el-aside width="300px" class="chat-sidebar">
      <div class="sidebar-header">
        <button class="new-session-btn" @click="handleNewSession">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          <span>新建会话</span>
        </button>
      </div>

      <div class="session-list">
        <div
          v-for="session in chatStore.sessions"
          :key="session.id"
          :class="['session-item glass-card', { active: session.id === chatStore.currentSessionId }]"
          @click="chatStore.switchSession(session.id)"
        >
          <div :class="['session-icon', session.mode]">
            <svg v-if="session.mode === 'general'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <svg v-if="session.mode === 'triage'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
            <svg v-if="session.mode === 'report'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
          </div>
          <div class="session-info">
            <span class="session-title">{{ session.title || getModeLabel(session.mode) }}</span>
            <span class="session-time">{{ formatSessionTime(session.created_at) }}</span>
          </div>
        </div>

        <div v-if="chatStore.sessions.length === 0" class="empty-sessions">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <p class="empty-text">暂无会话</p>
          <p class="empty-hint">点击上方按钮开始对话</p>
        </div>
      </div>
    </el-aside>

    <!-- 右侧对话区 -->
    <el-main class="chat-main">
      <!-- 顶部模式切换 -->
      <div class="mode-switcher glass-card">
        <div class="mode-tabs">
          <button
            v-for="mode in modes"
            :key="mode.value"
            :class="['mode-tab', { active: currentMode === mode.value }]"
            @click="currentMode = mode.value as ChatMode"
          >
            <svg v-if="mode.value === 'triage'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
            <svg v-if="mode.value === 'report'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <svg v-if="mode.value === 'general'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <span>{{ mode.label }}</span>
          </button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div ref="messageListRef" class="message-list">
        <!-- 欢迎页 -->
        <div v-if="chatStore.messages.length === 0" class="welcome-screen">
          <div class="welcome-content">
            <div class="welcome-badge glass-card">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
              <span>AI 医疗导诊</span>
            </div>

            <h1 class="welcome-title text-display">
              <span class="title-line">您好，我是</span>
              <span class="title-line accent gradient-text">医疗导诊助手</span>
            </h1>

            <p class="welcome-desc">
              基于 AI 多智能体架构，为您提供专业的医疗服务。我可以帮助您：
            </p>

            <div class="feature-cards">
              <div class="feature-card glass-card" @click="currentMode = 'triage'">
                <div class="card-icon triage">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                  </svg>
                </div>
                <div class="card-content">
                  <h3>智能导诊</h3>
                  <p>描述您的症状，为您推荐就诊科室</p>
                </div>
                <svg class="card-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </div>

              <div class="feature-card glass-card" @click="currentMode = 'report'">
                <div class="card-icon report">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                </div>
                <div class="card-content">
                  <h3>报告解读</h3>
                  <p>上传化验单，帮您解读检验结果</p>
                </div>
                <svg class="card-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </div>

              <div class="feature-card glass-card" @click="currentMode = 'general'">
                <div class="card-icon general">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                    <line x1="12" y1="17" x2="12.01" y2="17"/>
                  </svg>
                </div>
                <div class="card-content">
                  <h3>健康咨询</h3>
                  <p>解答健康相关问题和医学常识</p>
                </div>
                <svg class="card-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </div>
            </div>

            <div class="welcome-footer">
              <p class="footer-text">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="16" x2="12" y2="12"/>
                  <line x1="12" y1="8" x2="12.01" y2="8"/>
                </svg>
                本系统提供的建议仅供参考，如有严重症状请及时就医
              </p>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <ChatMessage
          v-for="msg in chatStore.messages"
          :key="msg.id"
          :message="msg"
        />
      </div>

      <!-- 输入区 -->
      <div class="input-area glass-card">
        <div class="input-container">
          <div class="input-wrapper">
            <button
              v-if="currentMode === 'report'"
              class="upload-btn"
              @click="triggerFileUpload"
              title="上传图片"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
              </svg>
            </button>

            <textarea
              v-model="inputText"
              :placeholder="getPlaceholder()"
              class="message-input"
              rows="1"
              @keydown.enter.exact.prevent="handleSend"
              @input="autoResize"
              ref="inputRef"
            />

            <button
              class="send-btn"
              :class="{ active: inputText.trim() || selectedImage }"
              :disabled="!inputText.trim() && !selectedImage"
              @click="handleSend"
            >
              <svg v-if="!chatStore.isLoading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
              <div v-else class="loading-spinner"></div>
            </button>
          </div>

          <!-- 图片预览 -->
          <div v-if="selectedImage" class="selected-image">
            <img :src="imagePreview" alt="预览" />
            <button class="remove-btn" @click="clearSelectedImage">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <input
            ref="fileInputRef"
            type="file"
            accept="image/*"
            style="display: none"
            @change="handleFileSelect"
          />
        </div>
      </div>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatMessage from '@/components/ChatMessage.vue'
import type { ChatMode } from '@/types'

const chatStore = useChatStore()
const inputText = ref('')
const currentMode = ref<ChatMode>('triage')
const selectedImage = ref<File | undefined>(undefined)
const imagePreview = ref('')
const messageListRef = ref<HTMLElement>()
const inputRef = ref<HTMLTextAreaElement>()
const fileInputRef = ref<HTMLInputElement>()

const modes = [
  { value: 'triage', label: '导诊' },
  { value: 'report', label: '报告解读' },
  { value: 'general', label: '通用问答' },
]

onMounted(() => {
  chatStore.fetchSessions()
})

watch(() => chatStore.messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
}, { deep: true })

function scrollToBottom() {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

function formatSessionTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`

  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
  })
}

function getModeLabel(mode: ChatMode): string {
  const labels: Record<ChatMode, string> = {
    triage: '智能导诊',
    report: '报告解读',
    general: '健康咨询',
  }
  return labels[mode]
}

function getPlaceholder(): string {
  const placeholders: Record<ChatMode, string> = {
    triage: '请描述您的症状，如：我最近总是头疼...',
    report: '请描述您的问题，或上传化验单图片...',
    general: '请输入您的健康问题...',
  }
  return placeholders[currentMode.value]
}

function autoResize() {
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
    inputRef.value.style.height = Math.min(inputRef.value.scrollHeight, 120) + 'px'
  }
}

function triggerFileUpload() {
  fileInputRef.value?.click()
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    selectedImage.value = file
    imagePreview.value = URL.createObjectURL(file)
  }
}

function clearSelectedImage() {
  selectedImage.value = undefined
  imagePreview.value = ''
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

async function handleNewSession() {
  await chatStore.createSession(currentMode.value)
}

async function handleSend() {
  if (!inputText.value.trim() && !selectedImage.value) return

  let sessionId = chatStore.currentSessionId

  if (!sessionId) {
    const session = await chatStore.createSession(currentMode.value)
    if (!session) return
    sessionId = session.id
  }

  const content = inputText.value.trim()

  chatStore.addMessage({
    id: Date.now().toString(),
    session_id: sessionId,
    role: 'user',
    content,
    message_type: selectedImage.value ? 'image' : 'text',
    created_at: new Date().toISOString(),
  })

  inputText.value = ''
  const image = selectedImage.value
  clearSelectedImage()

  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }

  chatStore.isLoading = true

  chatStore.streamMessage(
    sessionId,
    content,
    (data: string) => {
      try {
        const event = JSON.parse(data)
        if (event.type === 'text') {
          chatStore.appendToLastAssistantMessage(event.content)
        } else if (event.type === 'followup') {
          chatStore.appendToLastAssistantMessage('\n\n' + event.questions?.join('\n'))
        }
      } catch {
        chatStore.appendToLastAssistantMessage(data)
      }
    },
    (_error: Error) => {
      chatStore.isLoading = false
    },
    image
  )

  setTimeout(() => {
    chatStore.isLoading = false
  }, 3000)
}
</script>

<style scoped>
.chat-container {
  height: 100vh;
}

/* 会话侧边栏 */
.chat-sidebar {
  background: var(--color-bg-elevated);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: var(--space-5) var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.new-session-btn {
  width: 100%;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: white;
  transition: all var(--transition-normal);
  box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
}

.new-session-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4);
}

.new-session-btn svg {
  width: 18px;
  height: 18px;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-3);
}

.session-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  margin-bottom: var(--space-1);
  cursor: pointer;
}

.session-item.active {
  border-color: var(--color-border-glow);
  box-shadow: var(--shadow-glow);
}

.session-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: white;
}

.session-icon svg {
  width: 20px;
  height: 20px;
}

.session-icon.triage {
  background: var(--gradient-primary);
}

.session-icon.report {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
}

.session-icon.general {
  background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
}

.session-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.session-title {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-time {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
}

.empty-sessions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-10) var(--space-4);
  text-align: center;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: var(--color-text-muted);
  margin-bottom: var(--space-4);
  opacity: 0.5;
}

.empty-text {
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.empty-hint {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

/* 主对话区 */
.chat-main {
  display: flex;
  flex-direction: column;
  padding: 0;
  background: var(--color-bg);
}

/* 模式切换 */
.mode-switcher {
  margin: var(--space-4) var(--space-6);
  padding: var(--space-2);
}

.mode-tabs {
  display: inline-flex;
  background: var(--color-surface);
  border-radius: var(--radius-full);
  padding: 4px;
  gap: 4px;
}

.mode-tab {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border: none;
  background: transparent;
  border-radius: var(--radius-full);
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.mode-tab:hover {
  color: var(--color-text);
}

.mode-tab.active {
  background: var(--gradient-primary);
  color: white;
  box-shadow: 0 2px 10px rgba(14, 165, 233, 0.3);
}

.mode-tab svg {
  width: 16px;
  height: 16px;
}

/* 消息列表 */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6) var(--space-8);
}

/* 欢迎页 */
.welcome-screen {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  padding: var(--space-10);
}

.welcome-content {
  max-width: 640px;
  text-align: center;
}

.welcome-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  margin-bottom: var(--space-8);
}

.welcome-badge svg {
  width: 16px;
  height: 16px;
  color: var(--color-primary);
}

.welcome-badge span {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-primary-light);
}

.welcome-title {
  font-size: var(--text-5xl);
  font-weight: var(--weight-bold);
  line-height: var(--leading-tight);
  color: var(--color-text);
  margin-bottom: var(--space-5);
}

.title-line {
  display: block;
}

.title-line.accent {
  font-style: italic;
}

.welcome-desc {
  font-size: var(--text-lg);
  line-height: var(--leading-relaxed);
  color: var(--color-text-muted);
  margin-bottom: var(--space-10);
}

.feature-cards {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-bottom: var(--space-10);
}

.feature-card {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-5);
  cursor: pointer;
  text-align: left;
}

.feature-card:hover {
  border-color: var(--color-border-glow);
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: white;
}

.card-icon svg {
  width: 24px;
  height: 24px;
}

.card-icon.triage {
  background: var(--gradient-primary);
}

.card-icon.report {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
}

.card-icon.general {
  background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
}

.card-content {
  flex: 1;
}

.card-content h3 {
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  margin-bottom: var(--space-1);
}

.card-content p {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: var(--leading-normal);
}

.card-arrow {
  width: 20px;
  height: 20px;
  color: var(--color-text-muted);
  transition: all var(--transition-fast);
}

.feature-card:hover .card-arrow {
  color: var(--color-primary);
  transform: translateX(4px);
}

.welcome-footer {
  margin-top: var(--space-8);
}

.footer-text {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.footer-text svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

/* 输入区 */
.input-area {
  margin: var(--space-4) var(--space-6);
  padding: var(--space-3);
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-2) var(--space-2) var(--space-2) var(--space-4);
  border: 1px solid var(--color-border);
  transition: all var(--transition-fast);
}

.input-wrapper:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15);
}

.upload-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  color: var(--color-text-muted);
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.upload-btn:hover {
  background: var(--color-surface-raised);
  color: var(--color-primary);
}

.upload-btn svg {
  width: 20px;
  height: 20px;
}

.message-input {
  flex: 1;
  min-height: 24px;
  max-height: 120px;
  padding: var(--space-2) 0;
  border: none;
  background: transparent;
  font-family: var(--font-body);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  color: var(--color-text);
  resize: none;
  outline: none;
}

.message-input::placeholder {
  color: var(--color-text-muted);
}

.send-btn {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  color: var(--color-text-muted);
  transition: all var(--transition-normal);
  flex-shrink: 0;
}

.send-btn.active {
  background: var(--gradient-primary);
  color: white;
  box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
}

.send-btn.active:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4);
}

.send-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.send-btn svg {
  width: 20px;
  height: 20px;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.selected-image {
  position: relative;
  display: inline-block;
  margin-top: var(--space-3);
}

.selected-image img {
  max-width: 100px;
  max-height: 100px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.remove-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-danger);
  border: 2px solid var(--color-bg-elevated);
  border-radius: 50%;
  cursor: pointer;
  color: white;
  transition: all var(--transition-fast);
}

.remove-btn:hover {
  transform: scale(1.1);
}

.remove-btn svg {
  width: 12px;
  height: 12px;
}

/* 响应式 */
@media (max-width: 768px) {
  .chat-sidebar {
    display: none;
  }

  .message-list {
    padding: var(--space-4);
  }

  .welcome-title {
    font-size: var(--text-4xl);
  }

  .feature-cards {
    gap: var(--space-3);
  }

  .feature-card {
    padding: var(--space-4);
  }

  .mode-switcher,
  .input-area {
    margin: var(--space-3);
  }
}
</style>
