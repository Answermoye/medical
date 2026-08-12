/**
 * 前端类型定义
 */

/** 用户信息 */
export interface User {
  id: string
  username: string
  role: 'patient' | 'doctor' | 'admin'
  email?: string
  phone?: string
  is_active: boolean
}

/** 登录请求 */
export interface LoginRequest {
  username: string
  password: string
}

/** 注册请求 */
export interface RegisterRequest {
  username: string
  password: string
  confirm_password: string
  role?: 'patient' | 'doctor'
}

/** 认证响应 */
export interface AuthResponse {
  access_token: string
  token_type: string
}

/** 会话信息 */
export interface Session {
  id: string
  user_id: string
  mode: 'triage' | 'report' | 'general'
  title?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

/** 消息 */
export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  message_type: 'text' | 'image' | 'file'
  metadata?: Record<string, any>
  created_at: string
}

/** 报告信息 */
export interface Report {
  id: string
  user_id: string
  title?: string
  image_path?: string
  abnormal_items?: AbnormalItem[]
  risk_level?: 'normal' | 'attention' | 'see_doctor'
  interpretation?: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
}

/** 异常指标 */
export interface AbnormalItem {
  item_name: string
  value: number
  unit: string
  reference_range: string
  abnormal_type: 'high' | 'low'
  meaning?: string
}

/** 审核任务 */
export interface ReviewTask {
  id: string
  report_id: string
  doctor_id?: string
  status: 'pending' | 'approved' | 'modified' | 'rejected'
  ai_interpretation?: string
  doctor_comment?: string
  doctor_modified_text?: string
  created_at: string
}

/** 知识库 */
export interface KnowledgeBase {
  id: string
  name: string
  description?: string
  type: 'symptom' | 'guideline' | 'general'
  document_count: number
  status: 'active' | 'inactive' | 'building'
  created_at: string
}

/** 科室推荐 */
export interface DepartmentRecommendation {
  department: string
  confidence?: number
  reason?: string
  description?: string
}

/** SSE事件数据 */
export interface SSEEvent {
  type: 'text' | 'followup' | 'done' | 'error'
  content?: string
  questions?: string[]
  data?: Record<string, any>
}

/** 对话模式 */
export type ChatMode = 'triage' | 'report' | 'general'
