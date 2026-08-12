import request from './request'
import type { Report, ReviewTask } from '@/types'

export const reportApi = {
  uploadReport(file: File): Promise<Report> {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/report/upload', formData)
  },

  getReport(reportId: string): Promise<Report> {
    return request.get(`/report/${reportId}`)
  },

  getReportResult(reportId: string): Promise<any> {
    return request.get(`/report/${reportId}/result`)
  },

  getUserReports(userId: string): Promise<Report[]> {
    return request.get(`/report/user/${userId}`)
  },

  // 审核相关
  getPendingReviews(): Promise<ReviewTask[]> {
    return request.get('/review/pending')
  },

  getReviewDetail(reviewId: string): Promise<any> {
    return request.get(`/review/${reviewId}`)
  },

  approveReview(reviewId: string, comment?: string): Promise<any> {
    return request.post(`/review/${reviewId}/approve`, { comment })
  },

  modifyReview(reviewId: string, modifiedText: string, comment?: string): Promise<any> {
    return request.post(`/review/${reviewId}/modify`, { modified_text: modifiedText, comment })
  },

  rejectReview(reviewId: string, comment?: string): Promise<any> {
    return request.post(`/review/${reviewId}/reject`, { comment })
  },
}
