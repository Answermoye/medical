<template>
  <div class="report-result">
    <el-card v-if="report" class="report-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <div class="header-icon">
              <el-icon :size="24"><Document /></el-icon>
            </div>
            <div>
              <h2>报告解读结果</h2>
              <p class="header-subtitle">基于 AI 智能分析</p>
            </div>
          </div>
          <span :class="['risk-tag', report.risk_level]">
            {{ getRiskLabel(report.risk_level) }}
          </span>
        </div>
      </template>

      <!-- 异常指标 -->
      <div v-if="report.abnormal_items?.length" class="section">
        <div class="section-header">
          <el-icon><Warning /></el-icon>
          <h3>异常指标</h3>
        </div>
        <el-table :data="report.abnormal_items" stripe class="result-table">
          <el-table-column prop="item_name" label="项目名称" width="150" />
          <el-table-column label="结果值" width="120">
            <template #default="{ row }">
              <span :class="['value', row.abnormal_type]">
                {{ row.value }} {{ row.unit }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="异常类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.abnormal_type === 'high' ? 'danger' : 'warning'" size="small" effect="dark">
                {{ row.abnormal_type === 'high' ? '↑ 偏高' : '↓ 偏低' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="reference_range" label="参考范围" width="120" />
          <el-table-column prop="meaning" label="临床意义" />
        </el-table>
      </div>

      <!-- 解读内容 -->
      <div class="section">
        <div class="section-header">
          <el-icon><InfoFilled /></el-icon>
          <h3>详细解读</h3>
        </div>
        <div class="interpretation-box">
          <div class="markdown-body" v-html="renderMarkdown(report.interpretation || '')" />
        </div>
      </div>

      <!-- 免责声明 -->
      <el-alert
        title="免责声明"
        description="以上解读仅供参考，不构成医疗诊断建议。如有疑问，请咨询专业医生。"
        type="warning"
        :closable="false"
        show-icon
        class="disclaimer"
      />
    </el-card>

    <el-empty v-else description="暂无报告数据" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { reportApi } from '@/api/report'
import { marked } from 'marked'
import { Document, Warning, InfoFilled } from '@element-plus/icons-vue'
import type { Report } from '@/types'

const route = useRoute()
const report = ref<Report | null>(null)

onMounted(async () => {
  const reportId = route.params.id as string
  if (reportId) {
    try {
      report.value = await reportApi.getReport(reportId)
    } catch {
      // 处理错误
    }
  }
})

function getRiskLabel(level?: string): string {
  const labels: Record<string, string> = {
    normal: '🟢 正常',
    attention: '🟡 需关注',
    see_doctor: '🔴 建议就医',
  }
  return labels[level || ''] || '未知'
}

function renderMarkdown(text: string): string {
  return marked(text) as string
}
</script>

<style scoped>
.report-result {
  max-width: 900px;
  margin: 24px auto;
  padding: 0 20px;
}

.report-card {
  border-radius: var(--radius-lg);
  border: none;
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

:deep(.el-card__header) {
  background: var(--gradient-primary);
  padding: 24px 28px;
  border: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: white;
}

.header-subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 4px;
}

.section {
  margin-bottom: 28px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--border-light);
}

.section-header .el-icon {
  color: var(--primary-color);
  font-size: 20px;
}

.section-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.result-table {
  border-radius: var(--radius-md);
  overflow: hidden;
}

.value.high {
  color: var(--danger-color);
  font-weight: 700;
}

.value.low {
  color: var(--warning-color);
  font-weight: 700;
}

.interpretation-box {
  background: var(--bg-color);
  padding: 20px 24px;
  border-radius: var(--radius-md);
  border-left: 4px solid var(--primary-color);
}

.disclaimer {
  border-radius: var(--radius-md);
  margin-top: 8px;
}
</style>
