<template>
  <div class="knowledge-base">
    <div class="kb-header glass-card">
      <div class="header-content">
        <div class="header-badge">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          </svg>
          <span>知识库管理</span>
        </div>
        <h1 class="header-title text-display">知识库</h1>
        <p class="header-desc">管理医学知识库和文档，为 AI 提供专业医疗知识支持</p>
      </div>
      <button class="create-btn" @click="showCreateDialog = true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        <span>创建知识库</span>
      </button>
    </div>

    <div class="kb-content">
      <div class="kb-grid" v-loading="loading">
        <div
          v-for="kb in knowledgeBases"
          :key="kb.id"
          class="kb-card gold-card"
        >
          <div class="card-header">
            <div :class="['card-icon', kb.type]">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              </svg>
            </div>
            <div :class="['status-badge', kb.status]">
              {{ kb.status === 'active' ? '活跃' : '未激活' }}
            </div>
          </div>

          <div class="card-body">
            <h3 class="card-title">{{ kb.name }}</h3>
            <p class="card-desc">{{ kb.description || '暂无描述' }}</p>

            <div class="card-meta">
              <div class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
                <span>{{ kb.document_count }} 个文档</span>
              </div>
              <div class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/>
                  <line x1="8" y1="2" x2="8" y2="6"/>
                  <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                <span>{{ formatDate(kb.created_at) }}</span>
              </div>
            </div>

            <div :class="['type-tag', kb.type]">
              {{ getTypeLabel(kb.type) }}
            </div>
          </div>

          <div class="card-actions">
            <button class="action-btn upload" @click="openUpload(kb)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <span>上传文档</span>
            </button>
            <button class="action-btn delete" @click="handleDelete(kb.id)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
              <span>删除</span>
            </button>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="knowledgeBases.length === 0 && !loading" class="empty-state">
          <div class="empty-icon-wrapper glass-card">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
          </div>
          <h3 class="empty-title">暂无知识库</h3>
          <p class="empty-desc">创建您的第一个知识库，开始管理医学文档</p>
          <button class="empty-btn" @click="showCreateDialog = true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            <span>创建知识库</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 创建知识库对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建知识库" width="500px" class="create-dialog">
      <el-form :model="createForm" label-width="80px" class="create-form">
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="createForm.type" placeholder="请选择类型" style="width: 100%">
            <el-option label="症状映射" value="symptom" />
            <el-option label="医学指南" value="guideline" />
            <el-option label="通用知识" value="general" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreateDialog = false" class="btn-cancel">取消</el-button>
          <el-button type="primary" @click="handleCreate" :loading="creating" class="btn-primary">
            <svg v-if="!creating" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            <span>{{ creating ? '创建中...' : '创建' }}</span>
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 上传文档对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传文档" width="500px" class="upload-dialog">
      <div class="upload-info glass-card">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
        </svg>
        <div>
          <span class="info-label">知识库</span>
          <span class="info-value">{{ currentKB?.name }}</span>
        </div>
      </div>

      <div class="upload-area glass-card" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleDrop">
        <input
          ref="fileInput"
          type="file"
          accept=".txt,.pdf,.md,.csv"
          style="display: none"
          @change="handleFileChange"
        />
        <div class="upload-content">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="upload-icon">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          <p class="upload-text">
            <span class="upload-link">点击上传</span>
            或拖拽文件到此处
          </p>
          <span class="upload-tip">支持 txt、pdf、md、csv 格式</span>
        </div>
      </div>

      <div v-if="uploadFile" class="selected-file glass-card">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <div class="file-info">
          <span class="file-name">{{ uploadFile.name }}</span>
          <span class="file-size">{{ formatFileSize(uploadFile.size) }}</span>
        </div>
        <button class="remove-file" @click="uploadFile = null">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showUploadDialog = false" class="btn-cancel">取消</el-button>
          <el-button type="primary" @click="handleUpload" :loading="uploading" class="btn-primary">
            <svg v-if="!uploading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            <span>{{ uploading ? '上传中...' : '上传' }}</span>
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { knowledgeBaseApi } from '@/api/knowledgeBase'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { KnowledgeBase } from '@/types'

const knowledgeBases = ref<KnowledgeBase[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showUploadDialog = ref(false)
const creating = ref(false)
const uploading = ref(false)
const currentKB = ref<KnowledgeBase | null>(null)
const uploadFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement>()

const createForm = ref({
  name: '',
  description: '',
  type: 'general',
})

onMounted(async () => {
  await fetchKnowledgeBases()
})

async function fetchKnowledgeBases() {
  loading.value = true
  try {
    knowledgeBases.value = await knowledgeBaseApi.list()
  } catch {
    knowledgeBases.value = []
  }
  loading.value = false
}

async function handleCreate() {
  if (!createForm.value.name) {
    ElMessage.warning('请输入名称')
    return
  }
  creating.value = true
  try {
    await knowledgeBaseApi.create(createForm.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    createForm.value = { name: '', description: '', type: 'general' }
    await fetchKnowledgeBases()
  } catch {
    ElMessage.error('创建失败')
  }
  creating.value = false
}

function openUpload(kb: KnowledgeBase) {
  currentKB.value = kb
  uploadFile.value = null
  showUploadDialog.value = true
}

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    uploadFile.value = file
  }
}

function handleDrop(event: DragEvent) {
  const file = event.dataTransfer?.files[0]
  if (file) {
    uploadFile.value = file
  }
}

async function handleUpload() {
  if (!uploadFile.value || !currentKB.value) return
  uploading.value = true
  try {
    await knowledgeBaseApi.uploadDocument(currentKB.value.id, uploadFile.value)
    ElMessage.success('上传成功')
    showUploadDialog.value = false
    await fetchKnowledgeBases()
  } catch {
    ElMessage.error('上传失败')
  }
  uploading.value = false
}

async function handleDelete(kbId: string) {
  await ElMessageBox.confirm('确定要删除此知识库吗？', '提示', { type: 'warning' })
  try {
    await knowledgeBaseApi.delete(kbId)
    ElMessage.success('删除成功')
    await fetchKnowledgeBases()
  } catch {
    ElMessage.error('删除失败')
  }
}

function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    symptom: '症状映射',
    guideline: '医学指南',
    general: '通用知识',
  }
  return labels[type] || type
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.knowledge-base {
  padding: var(--space-6);
  max-width: 1200px;
  margin: 0 auto;
}

/* 页面头部 */
.kb-header {
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
  border: 1px solid var(--color-border-accent);
  border-radius: var(--radius-full);
  margin-bottom: var(--space-4);
}

.header-badge svg {
  width: 16px;
  height: 16px;
  color: var(--color-accent);
}

.header-badge span {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-accent-light);
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

.create-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  background: var(--gradient-accent);
  border: none;
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--color-text-inverse);
  cursor: pointer;
  transition: all var(--transition-normal);
  box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
  position: relative;
  z-index: 1;
}

.create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4);
}

.create-btn svg {
  width: 18px;
  height: 18px;
}

/* 知识库网格 */
.kb-content {
  margin-top: var(--space-6);
}

.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-6);
}

/* 知识库卡片 */
.kb-card {
  padding: 0;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--space-5) var(--space-5) 0;
}

.card-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  color: white;
}

.card-icon svg {
  width: 24px;
  height: 24px;
}

.card-icon.symptom {
  background: var(--gradient-primary);
}

.card-icon.guideline {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
}

.card-icon.general {
  background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
}

.status-badge {
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.status-badge.active {
  background: var(--color-success-light);
  color: var(--color-success);
  box-shadow: 0 0 10px rgba(52, 211, 153, 0.1);
}

.status-badge.inactive {
  background: var(--color-surface);
  color: var(--color-text-muted);
}

.card-body {
  padding: var(--space-4) var(--space-5);
}

.card-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  margin-bottom: var(--space-2);
}

.card-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: var(--leading-relaxed);
  margin-bottom: var(--space-4);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  display: flex;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.meta-item svg {
  width: 16px;
  height: 16px;
  color: var(--color-text-muted);
}

.type-tag {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
}

.type-tag.symptom {
  background: rgba(14, 165, 233, 0.1);
  color: var(--color-primary-light);
}

.type-tag.guideline {
  background: rgba(99, 102, 241, 0.1);
  color: #8B5CF6;
}

.type-tag.general {
  background: rgba(16, 185, 129, 0.1);
  color: var(--color-success);
}

.card-actions {
  display: flex;
  border-top: 1px solid var(--color-border);
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-4);
  background: transparent;
  border: none;
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn svg {
  width: 16px;
  height: 16px;
}

.action-btn.upload {
  color: var(--color-primary-light);
  border-right: 1px solid var(--color-border);
}

.action-btn.upload:hover {
  background: rgba(14, 165, 233, 0.05);
}

.action-btn.delete {
  color: var(--color-danger);
}

.action-btn.delete:hover {
  background: rgba(248, 113, 113, 0.05);
}

/* 空状态 */
.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-4);
  text-align: center;
}

.empty-icon-wrapper {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-6);
}

.empty-icon {
  width: 40px;
  height: 40px;
  color: var(--color-text-muted);
}

.empty-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  margin-bottom: var(--space-2);
}

.empty-desc {
  font-size: var(--text-base);
  color: var(--color-text-muted);
  margin-bottom: var(--space-6);
}

.empty-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  background: var(--gradient-primary);
  border: none;
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: white;
  cursor: pointer;
  transition: all var(--transition-normal);
  box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
}

.empty-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4);
}

.empty-btn svg {
  width: 18px;
  height: 18px;
}

/* 上传对话框 */
.upload-info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  margin-bottom: var(--space-5);
}

.upload-info svg {
  width: 24px;
  height: 24px;
  color: var(--color-accent);
}

.info-label {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-bottom: 2px;
}

.info-value {
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  color: var(--color-text);
}

.upload-area {
  border: 2px dashed var(--color-border-light);
  padding: var(--space-10) var(--space-6);
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.upload-area:hover {
  border-color: var(--color-primary);
  background: rgba(14, 165, 233, 0.02);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.upload-icon {
  width: 48px;
  height: 48px;
  color: var(--color-text-muted);
  margin-bottom: var(--space-4);
}

.upload-text {
  font-size: var(--text-base);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.upload-link {
  color: var(--color-primary-light);
  font-weight: var(--weight-semibold);
}

.upload-tip {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.selected-file {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  margin-top: var(--space-4);
}

.selected-file svg {
  width: 24px;
  height: 24px;
  color: var(--color-primary);
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.remove-file {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-full);
  cursor: pointer;
  color: var(--color-text-muted);
  transition: all var(--transition-fast);
}

.remove-file:hover {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.remove-file svg {
  width: 16px;
  height: 16px;
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
  .knowledge-base {
    padding: var(--space-4);
  }

  .kb-header {
    flex-direction: column;
    gap: var(--space-6);
    padding: var(--space-6);
  }

  .create-btn {
    width: 100%;
    justify-content: center;
  }

  .kb-grid {
    grid-template-columns: 1fr;
  }

  .card-meta {
    flex-direction: column;
    gap: var(--space-2);
  }
}
</style>
