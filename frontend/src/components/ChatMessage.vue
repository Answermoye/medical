<template>
  <div :class="['chat-message', message.role]">
    <div :class="['avatar-wrapper', message.role]">
      <span v-if="message.role === 'user'" class="avatar-text">
        {{ getInitial(userInfo?.username) }}
      </span>
      <svg v-else class="ai-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
      </svg>
    </div>

    <div class="message-body">
      <div class="message-header">
        <span class="role-name">{{ message.role === 'user' ? '我' : '医疗助手' }}</span>
        <span class="time">{{ formatTime(message.created_at) }}</span>
      </div>

      <div :class="['message-content', message.role]">
        <!-- AI 消息左侧装饰线 -->
        <div v-if="message.role === 'assistant'" class="content-accent"></div>

        <!-- 图片消息 -->
        <div v-if="message.message_type === 'image' && message.metadata?.image_url" class="image-message">
          <el-image
            :src="message.metadata.image_url"
            :preview-src-list="[message.metadata.image_url]"
            style="max-width: 300px; border-radius: var(--radius-lg)"
          />
        </div>

        <!-- 文本消息（Markdown渲染） -->
        <div
          v-if="message.content"
          class="markdown-body"
          v-html="renderMarkdown(message.content)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useUserStore } from '@/stores/user'
import type { Message } from '@/types'

defineProps<{
  message: Message
}>()

const userStore = useUserStore()
const userInfo = computed(() => userStore.userInfo)

function getInitial(name?: string): string {
  if (!name) return 'U'
  return name.charAt(0).toUpperCase()
}

function renderMarkdown(text: string): string {
  const html = marked(text) as string
  return DOMPurify.sanitize(html)
}

function formatTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`

  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
  max-width: 85%;
  animation: messageIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-message.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.chat-message.assistant {
  margin-right: auto;
}

/* 头像 */
.avatar-wrapper {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-wrapper.user {
  background: var(--gradient-primary);
  box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
}

.avatar-wrapper.assistant {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
}

.avatar-text {
  font-family: var(--font-display);
  font-size: var(--text-sm);
  font-weight: var(--weight-bold);
  color: white;
}

.ai-icon {
  width: 20px;
  height: 20px;
  color: white;
}

/* 消息体 */
.message-body {
  max-width: 100%;
  min-width: 0;
}

.message-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.user .message-header {
  flex-direction: row-reverse;
}

.role-name {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
}

.time {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  opacity: 0.7;
}

/* 消息气泡 */
.message-content {
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-xl);
  word-break: break-word;
  position: relative;
  line-height: var(--leading-relaxed);
}

.message-content.user {
  background: var(--gradient-primary);
  color: white;
  box-shadow: 0 4px 20px rgba(14, 165, 233, 0.25);
  border-bottom-right-radius: var(--radius-sm);
}

.message-content.user :deep(.markdown-body) {
  color: white;
}

.message-content.user :deep(.markdown-body strong) {
  color: white;
}

.message-content.user :deep(.markdown-body a) {
  color: rgba(255, 255, 255, 0.9);
  border-bottom-color: rgba(255, 255, 255, 0.3);
}

.message-content.user :deep(.markdown-body a:hover) {
  border-bottom-color: white;
}

.message-content.user :deep(.markdown-body code) {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.message-content.user :deep(.markdown-body pre) {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.message-content.user :deep(.markdown-body pre code) {
  background: transparent;
}

.message-content.user :deep(.markdown-body blockquote) {
  border-left-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.9);
}

.message-content.user :deep(.markdown-body li::marker) {
  color: rgba(255, 255, 255, 0.7);
}

.message-content.assistant {
  background: var(--color-bg-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  color: var(--color-text);
  box-shadow: var(--shadow-md);
  border-bottom-left-radius: var(--radius-sm);
  border: 1px solid var(--color-border-light);
  padding-left: calc(var(--space-5) + 4px);
}

/* AI 消息左侧装饰线 */
.content-accent {
  position: absolute;
  left: 0;
  top: var(--space-3);
  bottom: var(--space-3);
  width: 4px;
  border-radius: 2px;
  background: var(--gradient-primary);
  box-shadow: 0 0 10px rgba(14, 165, 233, 0.3);
}

.image-message {
  margin-bottom: var(--space-3);
}

/* 响应式 */
@media (max-width: 768px) {
  .chat-message {
    max-width: 95%;
  }

  .message-content {
    padding: var(--space-3) var(--space-4);
  }

  .avatar-wrapper {
    width: 36px;
    height: 36px;
  }

  .avatar-text {
    font-size: var(--text-xs);
  }

  .ai-icon {
    width: 18px;
    height: 18px;
  }
}

/* 减少动画模式 */
@media (prefers-reduced-motion: reduce) {
  .chat-message {
    animation: none;
  }
}
</style>
