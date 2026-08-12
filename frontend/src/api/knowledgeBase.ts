import request from './request'
import type { KnowledgeBase } from '@/types'

export const knowledgeBaseApi = {
  create(data: { name: string; description?: string; type: string }): Promise<KnowledgeBase> {
    return request.post('/knowledge-base/', data)
  },

  list(): Promise<KnowledgeBase[]> {
    return request.get('/knowledge-base/')
  },

  get(kbId: string): Promise<KnowledgeBase> {
    return request.get(`/knowledge-base/${kbId}`)
  },

  uploadDocument(kbId: string, file: File): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    return request.post(`/knowledge-base/${kbId}/documents`, formData)
  },

  listDocuments(kbId: string): Promise<any[]> {
    return request.get(`/knowledge-base/${kbId}/documents`)
  },

  deleteDocument(kbId: string, docId: string): Promise<any> {
    return request.delete(`/knowledge-base/${kbId}/documents/${docId}`)
  },

  delete(kbId: string): Promise<any> {
    return request.delete(`/knowledge-base/${kbId}`)
  },
}
