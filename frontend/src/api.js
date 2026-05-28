import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 15000 })

export const getPosts = (params) =>
  api.get('/posts', { params }).then((r) => r.data)

export const getPost = (id) =>
  api.get(`/posts/${id}`).then((r) => r.data)

export const getPostCategories = () =>
  api.get('/posts/categories').then((r) => r.data)

export const getHealth = () =>
  api.get('/health').then((r) => r.data)

export const getJobSummary = () =>
  api.get('/jobs/summary').then((r) => r.data)

export const getIngestionHealth = () =>
  api.get('/jobs/ingestion-health').then((r) => r.data)

export const getSources = () =>
  api.get('/sources').then((r) => r.data)

export const syncNow = () => api.post('/sync').then((r) => r.data)

export const getSupport = (clientId) =>
  api.get('/support', { params: { client_id: clientId } }).then((r) => r.data)

export const addSupport = (clientId) =>
  api.post('/support', { client_id: clientId }).then((r) => r.data)
