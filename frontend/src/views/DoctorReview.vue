<template>
  <div class="doctor-review">
    <div class="review-header glass-card">
      <div class="header-content">
        <div class="header-badge">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 12l2 2 4-4"/>
            <circle cx="12" cy="12" r="10"/>
          </svg>
          <span>医生工作台</span>
        </div>
        <h1 class="header-title text-display">审核工作台</h1>
        <p class="header-desc">审核 AI 生成的报告解读，确保医疗建议的准确性</p>
      </div>
      <div class="header-stats">
        <div class="stat-card glass-card">
          <span class="stat-number gradient-text-blue">{{ pendingCount }}</span>
          <span class="stat-label">待审核</span>
        </div>
        <div class="stat-card glass-card">
          <span class="stat-number gradient-text">{{ approvedCount }}</span>
          <span class="stat-label">已批准</span>
        </div>
      </div>
    </div>

    <div class="review-content">
      <div class="review-table-wrapper glass-card">
        <div class="table-header">
          <h2 class="table-title text-display">审核列表</h2>
          <div class="table-filters">
            <button
              v-for="filter in filters"
              :key="filter.value"
              :class="['filter-btn', { active: currentFilter === filter.value }]"
              @click="currentFilter = filter.value"
            >
              {{ filter.label }}
            </button>
          </div>
        </div>

        <div class="review-list" v-loading="loading">
          <div
            v-for="review in filteredReviews"
            :key="review.id"
            class="review-item"
            @click="openReview(review)"
          >
            <div class="review-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
            </div>
            <div class="review-info">
              <span class="review-id">报告 #{{ review.report_id.slice(0, 8) }}</span>
              <span class="review-time">{{ formatTime(review.created_at) }}</span>
            </div>
            <div :class="['review-status', review.status]">
              {{ getStatusLabel(review.status) }}
            </div>
            <svg class="review-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18l6-6-6-6"/>
            </svg>
          </div>

          <div v-if="filteredReviews.length === 0" class="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
              <path d="M9 12l2 2 4-4"/>
              <circle cx="12" cy="12" r="10"/>
            </svg>
            <p class="empty-text">暂无审核任务</p>
            <p class="empty-hint">{{ currentFilter === 'pending' ? '所有报告已审核完毕' : '该状态下暂无报告' }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 审核对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="报告审核"
      width="800px"
      :close-on-click-modal="false"
      class="review-dialog"
    >
      <div v-if="currentReview" class="review-dialog-content">
        <!-- AI解读 -->
        <div class="dialog-section">
          <div class="section-header">
            <div class="section-icon ai">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
            </div>
            <div>
              <h3 class="section-title">AI 解读草案</h3>
              <p class="section-desc">由 AI 生成的初步解读</p>
            </div>
          </div>
          <div class="ai-interpretation markdown-body" v-html="renderMarkdown(currentReview.ai_interpretation || '')" />
        </div>

        <!-- 医生操作 -->
        <div v-if="currentReview.status === 'pending'" class="dialog-section">
          <div class="section-header">
            <div class="section-icon doctor">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </div>
            <div>
              <h3 class="section-title">审核意见</h3>
              <p class="section-desc">请填写您的审核意见</p>
            </div>
          </div>
          <el-input
            v-model="doctorComment"
            type="textarea"
            :rows="3"
            placeholder="请输入审核意见（可选）"
            class="review-textarea"
          />

          <el-input
            v-if="actionType === 'modify'"
            v-model="modifiedText"
            type="textarea"
            :rows="5"
            placeholder="请输入修改后的解读内容"
            class="review-textarea"
          />
        </div>

        <!-- 已有审核结果 -->
        <div v-else class="dialog-section">
          <div class="section-header">
            <div class="section-icon completed">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
            </div>
            <div>
              <h3 class="section-title">审核结果</h3>
              <p class="section-desc">已完成的审核</p>
            </div>
          </div>
          <div class="review-result">
            <div :class="['result-status', currentReview.status]">
              {{ getStatusLabel(currentReview.status) }}
            </div>
            <p v-if="currentReview.doctor_comment" class="result-comment">
              <strong>批注：</strong>{{ currentReview.doctor_comment }}
            </p>
          </div>
        </div>
      </div>

      <template #footer v-if="currentReview?.status === 'pending'">
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false" class="btn-cancel">取消</el-button>
          <el-button type="warning" @click="actionType = 'modify'" class="btn-modify">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            修改后放行
          </el-button>
          <el-button type="danger" @click="handleReject" class="btn-reject">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            驳回
          </el-button>
          <el-button type="success" @click="handleApprove" class="btn-approve">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            批准
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { reportApi } from '@/api/report'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { ElMessage } from 'element-plus'
import type { ReviewTask } from '@/types'

const reviews = ref<ReviewTask[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const currentReview = ref<ReviewTask | null>(null)
const doctorComment = ref('')
const modifiedText = ref('')
const actionType = ref<'approve' | 'modify' | 'reject'>('approve')
const currentFilter = ref('pending')

const filters = [
  { value: 'pending', label: '待审核' },
  { value: 'approved', label: '已批准' },
  { value: 'modified', label: '已修改' },
  { value: 'rejected', label: '已驳回' },
  { value: 'all', label: '全部' },
]

const filteredReviews = computed(() => {
  if (currentFilter.value === 'all') return reviews.value
  return reviews.value.filter(r => r.status === currentFilter.value)
})

const pendingCount = computed(() => reviews.value.filter(r => r.status === 'pending').length)
const approvedCount = computed(() => reviews.value.filter(r => r.status === 'approved').length)

onMounted(async () => {
  await fetchReviews()
})

async function fetchReviews() {
  loading.value = true
  try {
    reviews.value = await reportApi.getPendingReviews()
  } catch {
    reviews.value = []
  }
  loading.value = false
}

function openReview(review: ReviewTask) {
  currentReview.value = review
  doctorComment.value = review.doctor_comment || ''
  modifiedText.value = review.ai_interpretation || ''
  actionType.value = 'approve'
  dialogVisible.value = true
}

async function handleApprove() {
  if (!currentReview.value) return
  try {
    await reportApi.approveReview(currentReview.value.id, doctorComment.value)
    ElMessage.success('审核通过')
    dialogVisible.value = false
    await fetchReviews()
  } catch {
    ElMessage.error('操作失败')
  }
}

async function handleReject() {
  if (!currentReview.value) return
  try {
    await reportApi.rejectReview(currentReview.value.id, doctorComment.value)
    ElMessage.success('已驳回')
    dialogVisible.value = false
    await fetchReviews()
  } catch {
    ElMessage.error('操作失败')
  }
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: '待审核',
    approved: '已批准',
    modified: '已修改',
    rejected: '已驳回',
  }
  return labels[status] || status
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

function renderMarkdown(text: string): string {
  const html = marked(text) as string
  return DOMPurify.sanitize(html)
}
</script>

<style scoped>
.doctor-review {
  padding: var(--space-6);
  max-width: 1200px;
  margin: 0 auto;
}

/* 页面头部 */
.review-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-8);
  padding: var(--space-8);
  background: var(--gradient-glow);
}

.header-content {
  position: relative;
  z-index: 1;
}

.header-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface);
  border: 1px solid var(--color-border-glow);
  border-radius: var(--radius-full);
  margin-bottom: var(--space-4);
}

.header-badge svg {
  width: 16px;
  height: 16px;
  color: var(--color-primary);
}

.header-badge span {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-primary-light);
}

.header-title {
  font-size: var(--text-3xl);
  font-weight: var(--weight-bold);
  color: var(--color-text);
  margin-bottom: var(--space-2);
}

.header-desc {
  font-size: var(--text-base);
  color: var(--color-text-muted);
  max-width: 400px;
}

.header-stats {
  display: flex;
  gap: var(--space-4);
  position: relative;
  z-index: 1;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-4) var(--space-6);
  min-width: 100px;
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

/* 内容区 */
.review-content {
  margin-top: var(--space-6);
}

.review-table-wrapper {
  padding: 0;
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--color-border);
}

.table-title {
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
}

.table-filters {
  display: flex;
  gap: var(--space-2);
}

.filter-btn {
  padding: var(--space-2) var(--space-4);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-btn:hover {
  background: var(--color-surface);
  border-color: var(--color-border-light);
  color: var(--color-text);
}

.filter-btn.active {
  background: var(--gradient-primary);
  border-color: transparent;
  color: white;
  box-shadow: 0 2px 10px rgba(14, 165, 233, 0.3);
}

/* 审核列表 */
.review-list {
  min-height: 400px;
}

.review-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.review-item:hover {
  background: var(--color-surface);
}

.review-item:last-child {
  border-bottom: none;
}

.review-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.review-icon svg {
  width: 22px;
  height: 22px;
}

.review-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.review-id {
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  color: var(--color-text);
}

.review-time {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-top: 2px;
}

.review-status {
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.review-status.pending {
  background: var(--color-warning-light);
  color: var(--color-warning);
  box-shadow: 0 0 10px rgba(251, 191, 36, 0.1);
}

.review-status.approved {
  background: var(--color-success-light);
  color: var(--color-success);
  box-shadow: 0 0 10px rgba(52, 211, 153, 0.1);
}

.review-status.modified {
  background: var(--color-info-light);
  color: var(--color-info);
  box-shadow: 0 0 10px rgba(96, 165, 250, 0.1);
}

.review-status.rejected {
  background: var(--color-danger-light);
  color: var(--color-danger);
  box-shadow: 0 0 10px rgba(248, 113, 113, 0.1);
}

.review-arrow {
  width: 20px;
  height: 20px;
  color: var(--color-text-muted);
  transition: all var(--transition-fast);
}

.review-item:hover .review-arrow {
  color: var(--color-primary);
  transform: translateX(4px);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-4);
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  color: var(--color-text-muted);
  margin-bottom: var(--space-5);
  opacity: 0.5;
}

.empty-text {
  font-size: var(--text-lg);
  font-weight: var(--weight-medium);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.empty-hint {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

/* 对话框样式 */
.review-dialog-content {
  max-height: 60vh;
  overflow-y: auto;
}

.dialog-section {
  margin-bottom: var(--space-6);
}

.dialog-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.section-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  flex-shrink: 0;
}

.section-icon svg {
  width: 20px;
  height: 20px;
}

.section-icon.ai {
  background: var(--color-surface);
  color: var(--color-primary);
}

.section-icon.doctor {
  background: var(--color-info-light);
  color: var(--color-info);
}

.section-icon.completed {
  background: var(--color-success-light);
  color: var(--color-success);
}

.section-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  margin: 0;
}

.section-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin: 2px 0 0;
}

.ai-interpretation {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border-left: 4px solid var(--color-primary);
}

.review-textarea {
  margin-top: var(--space-3);
}

/* 审核结果 */
.review-result {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
}

.result-status {
  display: inline-block;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  margin-bottom: var(--space-3);
}

.result-status.pending {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.result-status.approved {
  background: var(--color-success-light);
  color: var(--color-success);
}

.result-status.modified {
  background: var(--color-info-light);
  color: var(--color-info);
}

.result-status.rejected {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.result-comment {
  font-size: var(--text-base);
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin: 0;
}

.result-comment strong {
  color: var(--color-text);
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  gap: var(--space-3);
  justify-content: flex-end;
}

.dialog-footer .el-button {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.dialog-footer svg {
  width: 16px;
  height: 16px;
}

.btn-cancel {
  background: var(--color-surface) !important;
  border-color: var(--color-border) !important;
  color: var(--color-text-secondary) !important;
}

.btn-cancel:hover {
  background: var(--color-surface-raised) !important;
  border-color: var(--color-border-light) !important;
}

/* 响应式 */
@media (max-width: 768px) {
  .doctor-review {
    padding: var(--space-4);
  }

  .review-header {
    flex-direction: column;
    gap: var(--space-6);
    padding: var(--space-6);
  }

  .header-stats {
    width: 100%;
  }

  .stat-card {
    flex: 1;
  }

  .table-header {
    flex-direction: column;
    gap: var(--space-4);
    align-items: flex-start;
  }

  .table-filters {
    flex-wrap: wrap;
  }

  .review-item {
    padding: var(--space-4);
  }

  .dialog-footer {
    flex-wrap: wrap;
  }

  .dialog-footer .el-button {
    flex: 1;
    min-width: 120px;
  }
}
</style>
