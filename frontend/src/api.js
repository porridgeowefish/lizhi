import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const getArticles = (params) =>
  api.get('/articles', { params }).then((r) => r.data)

export const getArticle = (id) =>
  api.get(`/articles/${id}`).then((r) => r.data)

export const getCategories = () =>
  api.get('/articles/categories').then((r) => r.data)

export const getFeeds = () =>
  api.get('/sources').then((r) => r.data)

export const syncNow = () => api.post('/sync').then(r => r.data)
