/**
 * Service layer wrapping every API call.
 *
 * Components import these functions instead of calling axios directly.
 */
import api from '../api'

// ---------------------------------------------------------------------------
// Articles
// ---------------------------------------------------------------------------
export const articleService = {
  list: async (params = {}) => {
    const res = await api.get('/articles', { params })
    return res.data
  },
  search: async (params = {}) => {
    const res = await api.get('/articles/search', { params })
    return res.data
  },
  myArticles: async () => {
    const res = await api.get('/articles/my-articles')
    return res.data
  },
  pendingApprovals: async () => {
    const res = await api.get('/articles/pending-approvals')
    return res.data
  },
  get: async (id) => {
    const res = await api.get(`/articles/${id}`)
    return res.data
  },
  create: async (data) => {
    const res = await api.post('/articles', data)
    return res.data
  },
  update: async (id, data) => {
    const res = await api.put(`/articles/${id}`, data)
    return res.data
  },
  remove: async (id) => {
    const res = await api.delete(`/articles/${id}`)
    return res.data
  },
  submit: async (id) => {
    const res = await api.post(`/articles/${id}/submit`)
    return res.data
  },
  review: async (id, status, comments = null) => {
    const res = await api.post(`/articles/${id}/review`, { status, approval_comments: comments })
    return res.data
  },
  archive: async (id) => {
    const res = await api.post(`/articles/${id}/archive`)
    return res.data
  },

  // Comments
  listComments: async (id) => (await api.get(`/articles/${id}/comments`)).data,
  addComment: async (id, text) => (await api.post(`/articles/${id}/comments`, { comment_text: text })).data,
  deleteComment: async (commentId) => (await api.delete(`/articles/comments/${commentId}`)).data,

  // Ratings
  rate: async (id, value) => (await api.post(`/articles/${id}/rate`, { rating_value: value })).data,

  // Bookmarks
  bookmark: async (id) => (await api.post(`/articles/${id}/bookmark`)).data,
  unbookmark: async (id) => (await api.delete(`/articles/${id}/bookmark`)).data,
  myBookmarks: async () => (await api.get('/articles/bookmarks/mine')).data,

  // Attachments
  uploadAttachment: async (id, file) => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await api.post(`/articles/${id}/attachments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  },
  deleteAttachment: async (attachmentId) =>
    (await api.delete(`/articles/attachments/${attachmentId}`)).data,
  downloadAttachmentUrl: (attachmentId) =>
    `${api.defaults.baseURL}/articles/attachments/${attachmentId}/download`,
}

// ---------------------------------------------------------------------------
// Categories
// ---------------------------------------------------------------------------
export const categoryService = {
  list: async () => (await api.get('/categories')).data,
  create: async (data) => (await api.post('/categories', data)).data,
  update: async (id, data) => (await api.put(`/categories/${id}`, data)).data,
  remove: async (id) => (await api.delete(`/categories/${id}`)).data,
}

// ---------------------------------------------------------------------------
// Tags
// ---------------------------------------------------------------------------
export const tagService = {
  list: async () => (await api.get('/tags')).data,
}

// ---------------------------------------------------------------------------
// Users (admin)
// ---------------------------------------------------------------------------
export const userService = {
  list: async () => (await api.get('/users')).data,
  update: async (id, data) => (await api.put(`/users/${id}`, data)).data,
  remove: async (id) => (await api.delete(`/users/${id}`)).data,
  roles: async () => (await api.get('/users/roles/all')).data,
}

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------
export const analyticsService = {
  dashboard: async () => (await api.get('/analytics/dashboard')).data,
  full: async () => (await api.get('/analytics')).data,
}

// Shared constants
export const ARTICLE_STATUSES = ['Draft', 'Pending Approval', 'Approved', 'Rejected', 'Archived']
export const ROLES = ['Admin', 'Author', 'Reviewer', 'Employee']
