<template>
  <div id="app-root">
    <!-- Organic Background -->
    <div class="garden-canvas">
      <svg viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <radialGradient id="glow1" cx="15%" cy="20%" r="25%"><stop offset="0%" stop-color="#5a8f5c" stop-opacity="0.1"/><stop offset="100%" stop-color="#5a8f5c" stop-opacity="0"/></radialGradient>
          <radialGradient id="glow2" cx="85%" cy="75%" r="30%"><stop offset="0%" stop-color="#e8743f" stop-opacity="0.07"/><stop offset="100%" stop-color="#e8743f" stop-opacity="0"/></radialGradient>
          <radialGradient id="glow3" cx="50%" cy="10%" r="20%"><stop offset="0%" stop-color="#8bc34a" stop-opacity="0.06"/><stop offset="100%" stop-color="#8bc34a" stop-opacity="0"/></radialGradient>
        </defs>
        <rect fill="url(#glow1)" width="1440" height="900"/>
        <rect fill="url(#glow2)" width="1440" height="900"/>
        <rect fill="url(#glow3)" width="1440" height="900"/>
      </svg>
    </div>

    <!-- Floating Leaf Particles -->
    <div class="particle" style="left:8%;animation:particleFall 18s linear 0s infinite"><span style="width:14px;height:22px;background:linear-gradient(135deg,#5a8f5c,#8bc34a)"></span></div>
    <div class="particle" style="left:25%;animation:particleFall 22s linear 4s infinite"><span style="width:10px;height:16px;background:linear-gradient(135deg,#8bc34a,#aed581)"></span></div>
    <div class="particle" style="left:55%;animation:particleFall 20s linear 8s infinite"><span style="width:12px;height:20px;background:linear-gradient(135deg,#5a8f5c,#81c784)"></span></div>
    <div class="particle" style="left:78%;animation:particleFall 24s linear 2s infinite"><span style="width:16px;height:26px;background:linear-gradient(135deg,#7cb342,#c5e1a5)"></span></div>
    <div class="particle" style="left:92%;animation:particleFall 19s linear 12s infinite"><span style="width:11px;height:18px;background:linear-gradient(135deg,#5a8f5c,#a5d6a7)"></span></div>

    <!-- Floating Decorative Leaves -->
    <div class="leaf-float" style="top:18%;left:4%"><span style="width:20px;height:34px;animation-delay:0s"></span></div>
    <div class="leaf-float" style="top:35%;right:5%"><span style="width:16px;height:28px;animation-delay:5s"></span></div>
    <div class="leaf-float" style="top:60%;left:2%"><span style="width:18px;height:30px;animation-delay:10s"></span></div>
    <div class="leaf-float" style="top:80%;right:3%"><span style="width:14px;height:24px;animation-delay:15s"></span></div>

    <!-- Header -->
    <header>
      <div class="header-inner">
        <div class="brand" @click="resetView">
          <div class="brand-icon">荔</div>
          <div>
            <h1>荔知</h1>
            <p class="tagline">荔园花园 · 深大信息聚合</p>
          </div>
        </div>
        <div class="search-box">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input v-model="searchQuery" @keyup.enter="doSearch" placeholder="搜索讲座、活动、志愿..." />
          <button v-if="searchQuery" class="clear-btn" @click="clearSearch">&times;</button>
        </div>
      </div>
    </header>

    <!-- Category Tabs -->
    <nav>
      <div class="cat-inner">
        <button
          v-for="cat in allCategories"
          :key="cat.key"
          :class="['cat-btn', { active: currentCategory === cat.key }]"
          @click="switchCategory(cat.key)"
        >
          {{ cat.label }}
          <span class="cat-count" v-if="cat.count">{{ cat.count }}</span>
        </button>
      </div>
    </nav>

    <!-- Main Content -->
    <main>
      <!-- Article Detail -->
      <div v-if="selectedArticle" class="detail-view">
        <button class="back-btn" @click="selectedArticle = null">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
          返回列表
        </button>
        <article class="detail-card">
          <div class="detail-meta">
            <span class="detail-source">{{ selectedArticle.source_name }}</span>
            <span class="detail-date">{{ formatDate(selectedArticle.published_at) }}</span>
          </div>
          <h2 class="detail-title">{{ selectedArticle.title }}</h2>
          <p class="detail-desc" v-if="selectedArticle.summary">{{ selectedArticle.summary }}</p>
          <img v-if="selectedArticle.cover_url" :src="selectedArticle.cover_url" class="detail-cover" />
          <div class="detail-categories">
            <span v-for="c in selectedArticle.categories || []" :key="c" class="cat-tag">{{ categoryMap[c]?.label || c }}</span>
          </div>
          <div class="detail-content" v-if="detailHtml" v-html="detailHtml"></div>
          <div class="detail-actions">
            <a :href="selectedArticle.original_url" target="_blank" class="btn-original">查看原文 &rarr;</a>
          </div>
        </article>
      </div>

      <!-- Article List -->
      <div v-else>
        <div class="list-header">
          <h2 class="list-title">
            {{ currentCategoryLabel }}
            <span class="list-count" v-if="articles.length">{{ articles.length }} 条</span>
          </h2>
          <button class="sync-btn" @click="doSync" :disabled="syncing">
            {{ syncing ? '同步中...' : '刷新' }}
          </button>
        </div>

        <div class="article-grid" v-if="articles.length">
          <div
            v-for="(a, i) in articles"
            :key="a.id"
            class="article-card"
            :style="{ animationDelay: i * 70 + 'ms' }"
            @click="openArticle(a)"
          >
            <div class="card-inner">
              <div class="card-top">
                <span class="card-source">{{ a.source_name }}</span>
                <span class="card-date">{{ formatDate(a.published_at) }}</span>
              </div>
              <h3 class="card-title">{{ a.title }}</h3>
              <p class="card-desc" v-if="a.summary">{{ a.summary.slice(0, 100) }}{{ a.summary.length > 100 ? '...' : '' }}</p>
              <div class="card-bottom">
                <div class="card-tags">
                  <span v-for="c in a.categories || []" :key="c" class="tag" :class="'tag-' + c">
                    {{ categoryMap[c]?.label || c }}
                  </span>
                </div>
                <button
                  class="bookmark-btn"
                  :class="{ active: bookmarks.has(a.id) }"
                  @click.stop="toggleBookmark(a.id)"
                  title="收藏"
                >&#9733;</button>
              </div>
              <a class="card-link" :href="a.original_url" target="_blank" @click.stop>查看原文 &#8594;</a>
            </div>
            <div class="leaf-shadow"></div>
          </div>
        </div>

        <div class="empty-state" v-else-if="!loading">
          <div class="empty-icon">&#127811;</div>
          <p>暂无{{ currentCategoryLabel }}相关的信息</p>
          <p style="font-size:13px;margin-top:6px;color:var(--muted)">试试其他分类或搜索关键词</p>
        </div>

        <div class="loading-state" v-if="loading">
          <div class="spinner"></div>
          <p>正在加载...</p>
        </div>

        <div class="load-more" v-if="articles.length && articles.length % 20 === 0">
          <button @click="loadMore" :disabled="loadingMore">
            {{ loadingMore ? '加载中...' : '加载更多' }}
          </button>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <footer>荔知 · 荔园花园 · 深圳大学校园信息聚合平台</footer>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { getArticles, getArticle, getCategories, syncNow } from './api.js'

const CATEGORY_CONFIG = [
  { key: '', label: '全部' },
  { key: 'activity', label: '活动' },
  { key: 'lecture', label: '讲座' },
  { key: 'volunteer', label: '志愿' },
  { key: 'exam', label: '考试' },
  { key: 'recruitment', label: '招聘' },
  { key: 'scholarship', label: '奖助' },
  { key: 'other', label: '其他' },
]

export default {
  name: 'App',
  setup() {
    const articles = ref([])
    const categories = ref([])
    const currentCategory = ref('')
    const searchQuery = ref('')
    const activeSearch = ref('')
    const selectedArticle = ref(null)
    const detailHtml = ref('')
    const loading = ref(false)
    const syncing = ref(false)
    const loadingMore = ref(false)
    const offset = ref(0)
    const bookmarks = ref(new Set())

    const categoryMap = computed(() => {
      const map = {}
      CATEGORY_CONFIG.forEach(c => { map[c.key || 'other'] = c })
      return map
    })

    const allCategories = computed(() => {
      const countMap = {}
      categories.value.forEach(c => { countMap[c.category] = c.count })
      return CATEGORY_CONFIG.map(c => ({
        ...c,
        count: c.key ? (countMap[c.key] || 0) : null,
      }))
    })

    const currentCategoryLabel = computed(() => {
      if (activeSearch.value) return `"${activeSearch.value}" 的搜索结果`
      const found = CATEGORY_CONFIG.find(c => c.key === currentCategory.value)
      return found ? found.label + '信息' : '全部信息'
    })

    async function loadArticles(append = false) {
      loading.value = true
      try {
        const params = { offset: append ? offset.value : 0, limit: 20 }
        if (currentCategory.value) params.category = currentCategory.value
        if (activeSearch.value) params.search = activeSearch.value
        const data = await getArticles(params)
        if (append) {
          articles.value = [...articles.value, ...data.items]
        } else {
          articles.value = data.items
          offset.value = 0
        }
        offset.value = articles.value.length
      } finally {
        loading.value = false
        loadingMore.value = false
      }
    }

    function loadMore() {
      loadingMore.value = true
      loadArticles(true)
    }

    async function loadCategories() {
      const stats = await getCategories()
      categories.value = stats.categories
    }

    function switchCategory(key) {
      currentCategory.value = key
      activeSearch.value = ''
      searchQuery.value = ''
      selectedArticle.value = null
      loadArticles()
    }

    function doSearch() {
      if (!searchQuery.value.trim()) return
      activeSearch.value = searchQuery.value.trim()
      currentCategory.value = ''
      selectedArticle.value = null
      loadArticles()
    }

    function clearSearch() {
      searchQuery.value = ''
      activeSearch.value = ''
      loadArticles()
    }

    async function openArticle(a) {
      selectedArticle.value = a
      detailHtml.value = ''
      try {
        const full = await getArticle(a.id)
        selectedArticle.value = full
        detailHtml.value = full.content_html || ''
      } catch {}
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    async function doSync() {
      syncing.value = true
      try { await syncNow() } finally { syncing.value = false }
      loadArticles()
      loadCategories()
    }

    function resetView() {
      selectedArticle.value = null
      currentCategory.value = ''
      activeSearch.value = ''
      searchQuery.value = ''
      loadArticles()
    }

    function toggleBookmark(id) {
      if (bookmarks.value.has(id)) {
        bookmarks.value.delete(id)
      } else {
        bookmarks.value.add(id)
      }
    }

    function formatDate(dt) {
      if (!dt) return ''
      const d = new Date(dt)
      const now = new Date()
      const diff = now - d
      if (diff < 86400000) return '今天'
      if (diff < 172800000) return '昨天'
      if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
      return (d.getMonth() + 1) + '月' + d.getDate() + '日'
    }

    onMounted(() => {
      loadArticles()
      loadCategories()
    })

    return {
      articles, categories, currentCategory, searchQuery, activeSearch,
      selectedArticle, detailHtml, loading, syncing, loadingMore,
      allCategories, categoryMap, currentCategoryLabel, bookmarks,
      switchCategory, doSearch, clearSearch, openArticle, doSync,
      resetView, loadMore, toggleBookmark, formatDate,
    }
  },
}
</script>

<style>
:root {
  --bg: #f0f7ed;
  --fg: #2d3a29;
  --primary: #5a8f5c;
  --primary-dark: #3d7a3f;
  --accent: #e8743f;
  --card: #ffffff;
  --muted: #6b7a66;
  --border: #c8dcc3;
  --tag-activity: #d4edda; --tag-activity-fg: #2d6a3e;
  --tag-lecture: #d6eaf8; --tag-lecture-fg: #1a5276;
  --tag-volunteer: #fdebd0; --tag-volunteer-fg: #b9770e;
  --tag-exam: #fadbd8; --tag-exam-fg: #922b21;
  --tag-recruitment: #d1f2eb; --tag-recruitment-fg: #0e6655;
  --tag-scholarship: #e8daef; --tag-scholarship-fg: #6c3483;
  --tag-other: #eaecee; --tag-other-fg: #5d6d7e;
  --title-font: 'ZCOOL XiaoWei', serif;
  --body-font: 'LXGW WenKai TC', -apple-system, 'PingFang SC', sans-serif;
  --tag-font: 'Nunito', sans-serif;
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html { font-size: 16px; }

body {
  background: var(--bg);
  color: var(--fg);
  font-family: var(--body-font);
  line-height: 1.6;
  min-height: 100vh;
  overflow-x: hidden;
  position: relative;
}

/* Body glow effects */
body::before {
  content: '';
  position: fixed;
  top: -120px; left: -80px;
  width: 400px; height: 400px;
  background: radial-gradient(ellipse, rgba(90,143,92,0.18) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
}

body::after {
  content: '';
  position: fixed;
  bottom: -140px; right: -100px;
  width: 450px; height: 450px;
  background: radial-gradient(ellipse, rgba(232,116,63,0.12) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
}

#app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
}

/* === Garden Canvas === */
.garden-canvas {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none;
  z-index: 0;
}

.garden-canvas svg { width: 100%; height: 100%; }

/* === Floating Leaves === */
.leaf-float {
  position: fixed;
  pointer-events: none;
  z-index: 0;
  opacity: 0.18;
}

.leaf-float span {
  display: block;
  border-radius: 50% 0 50% 50%;
  background: linear-gradient(135deg, var(--primary), #8bc34a);
  animation: leafDrift 20s ease-in-out infinite;
}

@keyframes leafDrift {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  25% { transform: translateY(-18px) rotate(8deg); }
  50% { transform: translateY(6px) rotate(-5deg); }
  75% { transform: translateY(-10px) rotate(3deg); }
}

.particle {
  position: fixed;
  pointer-events: none;
  z-index: 0;
  opacity: 0;
}

.particle span {
  display: block;
  border-radius: 50% 0 50% 50%;
  animation: particleFall linear infinite;
}

@keyframes particleFall {
  0% { transform: translateY(-20px) rotate(0deg); opacity: 0; }
  10% { opacity: 0.15; }
  90% { opacity: 0.15; }
  100% { transform: translateY(calc(100vh + 20px)) rotate(360deg); opacity: 0; }
}

/* === Header === */
header {
  background: linear-gradient(160deg, #3d7a3f 0%, #5a8f5c 35%, #72a874 65%, #8bb890 100%);
  color: #fff;
  position: relative;
  z-index: 100;
  padding-bottom: 32px;
  box-shadow: 0 6px 30px rgba(45,58,41,0.18);
}

header::after {
  content: '';
  position: absolute;
  bottom: -2px; left: 0; right: 0;
  height: 40px;
  background: var(--bg);
  border-radius: 50% 50% 0 0 / 100% 100% 0 0;
}

.header-inner {
  max-width: 960px;
  margin: 0 auto;
  padding: 22px 24px 0;
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  flex-shrink: 0;
}

.brand-icon {
  width: 56px; height: 56px;
  background: linear-gradient(135deg, var(--accent), #f09060);
  color: #fff;
  font-family: var(--title-font);
  font-size: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  box-shadow: 0 4px 16px rgba(232,116,63,0.35);
  position: relative;
  overflow: hidden;
}

.brand-icon::before {
  content: '';
  position: absolute;
  top: -8px; left: 40%;
  width: 22px; height: 14px;
  background: #4a7f4c;
  border-radius: 50% 50% 0 0;
  transform: rotate(-20deg);
}

.brand-icon::after {
  content: '';
  position: absolute;
  top: -5px; left: 55%;
  width: 16px; height: 10px;
  background: #5a8f5c;
  border-radius: 50% 50% 0 0;
  transform: rotate(15deg);
}

.brand h1 {
  font-family: var(--title-font);
  font-size: 26px;
  letter-spacing: 4px;
  text-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.brand .tagline {
  font-size: 12px;
  opacity: 0.8;
  letter-spacing: 1.5px;
  margin-top: 2px;
}

.search-box {
  flex: 1;
  max-width: 400px;
  display: flex;
  align-items: center;
  background: rgba(255,255,255,0.2);
  border-radius: 100px;
  padding: 10px 20px;
  gap: 10px;
  transition: all 0.35s;
  backdrop-filter: blur(6px);
  border: 1px solid rgba(255,255,255,0.15);
}

.search-box:focus-within {
  background: rgba(255,255,255,0.32);
  box-shadow: 0 0 0 4px rgba(255,255,255,0.1), 0 0 20px rgba(232,116,63,0.15);
}

.search-box svg { flex-shrink: 0; opacity: 0.8; }

.search-box input {
  flex: 1;
  background: none;
  border: none;
  color: #fff;
  font-size: 14px;
  font-family: var(--body-font);
  outline: none;
}

.search-box input::placeholder { color: rgba(255,255,255,0.55); }

.clear-btn {
  background: none;
  border: none;
  color: rgba(255,255,255,0.6);
  font-size: 20px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}

.clear-btn:hover { color: #fff; }

/* === Category Nav === */
nav {
  background: var(--card);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 90;
  box-shadow: 0 2px 12px rgba(45,58,41,0.06);
}

.cat-inner {
  max-width: 960px;
  margin: 0 auto;
  padding: 12px 24px;
  display: flex;
  gap: 8px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.cat-inner::-webkit-scrollbar { display: none; }

.cat-btn {
  display: inline-flex;
  align-items: center;
  padding: 7px 20px;
  border: 1.5px solid var(--border);
  border-radius: 100px;
  background: transparent;
  color: var(--muted);
  font-family: var(--tag-font);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.3s;
}

.cat-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: rgba(90,143,92,0.06);
  transform: translateY(-1px);
}

.cat-btn.active {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
  box-shadow: 0 3px 10px rgba(90,143,92,0.25);
}

.cat-count {
  background: rgba(90,143,92,0.15);
  color: var(--primary);
  font-size: 11px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 100px;
  margin-left: 4px;
}

.cat-btn.active .cat-count {
  background: rgba(255,255,255,0.25);
  color: #fff;
}

/* === Main Content === */
main {
  max-width: 960px;
  margin: 0 auto;
  padding: 28px 24px 40px;
  position: relative;
  z-index: 1;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.list-title {
  font-family: var(--title-font);
  font-size: 24px;
  color: var(--primary);
  position: relative;
}

.list-title::after {
  content: '';
  display: block;
  width: 40px; height: 3px;
  background: linear-gradient(90deg, var(--accent), transparent);
  border-radius: 2px;
  margin-top: 6px;
}

.list-count {
  font-size: 14px;
  color: var(--muted);
  font-family: var(--tag-font);
  margin-left: 10px;
}

.sync-btn {
  padding: 7px 20px;
  border: 1.5px solid var(--border);
  border-radius: 100px;
  background: transparent;
  font-family: var(--tag-font);
  font-size: 13px;
  font-weight: 700;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.3s;
}

.sync-btn:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--primary);
}

.sync-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* === Article Grid === */
.article-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 24px;
  align-items: start;
}

.article-card {
  background: var(--card);
  border-radius: 20px;
  box-shadow: 0 2px 14px rgba(45,58,41,0.06);
  cursor: pointer;
  transition: transform 0.35s ease, box-shadow 0.35s ease;
  position: relative;
  animation: growIn 0.5s ease both;
  overflow: visible;
}

.article-card:nth-child(even) { margin-top: 18px; }

.article-card::before {
  content: '';
  position: absolute;
  top: -6px; right: -4px;
  width: 36px; height: 20px;
  background: linear-gradient(135deg, rgba(90,143,92,0.3), rgba(139,195,74,0.1));
  border-radius: 0 50% 0 50%;
  transform: rotate(30deg);
  z-index: 2;
  transition: transform 0.3s, opacity 0.3s;
}

.article-card:nth-child(even)::before {
  top: auto; right: auto;
  bottom: -6px; left: -4px;
  transform: rotate(-150deg);
}

.article-card::after {
  content: '';
  position: absolute;
  top: -3px; right: 24px;
  width: 18px; height: 12px;
  background: linear-gradient(135deg, rgba(139,195,74,0.2), transparent);
  border-radius: 50% 50% 0 50%;
  transform: rotate(45deg);
  z-index: 2;
  transition: transform 0.3s;
}

.article-card:hover {
  transform: scale(1.02) translateY(-4px);
  box-shadow: 0 12px 36px rgba(45,58,41,0.13), 0 4px 12px rgba(90,143,92,0.08);
}

.article-card:hover::before { transform: rotate(40deg) scale(1.15); opacity: 0.9; }
.article-card:hover::after { transform: rotate(55deg) scale(1.1); }

.leaf-shadow {
  position: absolute;
  bottom: -12px; left: 12%; right: 12%;
  height: 24px;
  background: radial-gradient(ellipse, rgba(90,143,92,0.14) 0%, transparent 80%);
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.35s;
  pointer-events: none;
}

.article-card:hover .leaf-shadow { opacity: 1; }

@keyframes growIn {
  from { opacity: 0; transform: scale(0.94) translateY(16px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.card-inner {
  padding: 22px 22px 18px;
  position: relative;
  z-index: 3;
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.card-source {
  font-size: 12px;
  color: var(--accent);
  font-weight: 700;
  font-family: var(--tag-font);
  letter-spacing: 0.5px;
}

.card-date {
  font-size: 12px;
  color: var(--muted);
  font-family: var(--tag-font);
}

.card-title {
  font-family: var(--title-font);
  font-size: 17px;
  line-height: 1.55;
  color: var(--fg);
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: color 0.2s;
}

.article-card:hover .card-title { color: var(--primary); }

.card-desc {
  font-size: 13px;
  color: var(--muted);
  line-height: 1.65;
  margin-bottom: 14px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-tags { display: flex; gap: 6px; flex-wrap: wrap; }

.tag {
  font-family: var(--tag-font);
  font-size: 11px;
  font-weight: 700;
  padding: 3px 12px;
  border-radius: 100px;
  transition: transform 0.2s;
}

.tag:hover { transform: scale(1.06); }
.tag-activity { background: var(--tag-activity); color: var(--tag-activity-fg); }
.tag-lecture { background: var(--tag-lecture); color: var(--tag-lecture-fg); }
.tag-volunteer { background: var(--tag-volunteer); color: var(--tag-volunteer-fg); }
.tag-exam { background: var(--tag-exam); color: var(--tag-exam-fg); }
.tag-recruitment { background: var(--tag-recruitment); color: var(--tag-recruitment-fg); }
.tag-scholarship { background: var(--tag-scholarship); color: var(--tag-scholarship-fg); }
.tag-other { background: var(--tag-other); color: var(--tag-other-fg); }

.bookmark-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--border);
  font-size: 20px;
  transition: all 0.3s;
  padding: 4px;
  line-height: 1;
}

.bookmark-btn:hover, .bookmark-btn.active {
  color: var(--accent);
  transform: scale(1.2);
}

.bookmark-btn.active { text-shadow: 0 0 8px rgba(232,116,63,0.3); }

.card-link {
  display: inline-block;
  margin-top: 14px;
  font-size: 13px;
  color: var(--primary);
  text-decoration: none;
  font-family: var(--tag-font);
  font-weight: 700;
  transition: all 0.25s;
  position: relative;
  padding-bottom: 1px;
}

.card-link::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0;
  width: 0; height: 1.5px;
  background: var(--accent);
  transition: width 0.3s;
  border-radius: 1px;
}

.card-link:hover { color: var(--accent); }
.card-link:hover::after { width: 100%; }

/* === Detail View === */
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1.5px solid var(--border);
  border-radius: 100px;
  background: transparent;
  font-family: var(--tag-font);
  font-size: 14px;
  font-weight: 700;
  color: var(--muted);
  cursor: pointer;
  margin-bottom: 20px;
  transition: all 0.2s;
}

.back-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.detail-card {
  background: var(--card);
  border-radius: 20px;
  padding: 32px;
  box-shadow: 0 2px 14px rgba(45,58,41,0.06);
}

.detail-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
  font-size: 13px;
}

.detail-source { color: var(--accent); font-weight: 700; font-family: var(--tag-font); }
.detail-date { color: var(--muted); font-family: var(--tag-font); }

.detail-title {
  font-family: var(--title-font);
  font-size: 28px;
  font-weight: 900;
  line-height: 1.4;
  color: var(--primary);
  margin-bottom: 12px;
}

.detail-desc {
  font-size: 16px;
  color: var(--muted);
  line-height: 1.6;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.detail-cover {
  width: 100%;
  border-radius: 12px;
  margin-bottom: 20px;
}

.detail-categories { display: flex; gap: 8px; margin-bottom: 20px; }

.cat-tag {
  font-family: var(--tag-font);
  font-size: 13px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 100px;
  background: rgba(90,143,92,0.12);
  color: var(--primary);
}

.detail-content {
  line-height: 1.8;
  font-size: 16px;
  color: var(--fg);
}

.detail-content img {
  max-width: 100%;
  border-radius: 8px;
  margin: 12px 0;
}

.detail-content p { margin-bottom: 12px; }

.detail-actions {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}

.btn-original {
  display: inline-flex;
  align-items: center;
  padding: 10px 24px;
  background: var(--primary);
  color: #fff;
  border-radius: 100px;
  text-decoration: none;
  font-family: var(--tag-font);
  font-size: 14px;
  font-weight: 700;
  transition: background 0.2s;
}

.btn-original:hover { background: var(--primary-dark); }

/* === States === */
.empty-state, .loading-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--muted);
}

.empty-icon { font-size: 48px; margin-bottom: 12px; opacity: 0.7; }

.spinner {
  width: 32px; height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  margin: 0 auto 12px;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.load-more {
  text-align: center;
  margin-top: 32px;
}

.load-more button {
  padding: 10px 32px;
  border: 1.5px solid var(--border);
  border-radius: 100px;
  background: transparent;
  font-family: var(--tag-font);
  font-size: 14px;
  font-weight: 700;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.2s;
}

.load-more button:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--primary);
}

.load-more button:disabled { opacity: 0.5; cursor: not-allowed; }

/* === Footer === */
footer {
  text-align: center;
  padding: 32px 24px;
  color: var(--muted);
  font-size: 12px;
  border-top: 1px solid var(--border);
  margin-top: 48px;
  position: relative;
  z-index: 1;
}

footer::before {
  content: '';
  display: block;
  width: 60px; height: 3px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  border-radius: 2px;
  margin: 0 auto 16px;
}

/* === Responsive === */
@media (max-width: 960px) {
  .article-grid { grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
}

@media (max-width: 640px) {
  .header-inner {
    flex-direction: column;
    gap: 14px;
    padding: 16px 16px 0;
    text-align: center;
  }
  .brand { justify-content: center; }
  .search-box { max-width: 100%; }
  nav { top: 0; }
  .cat-inner { padding: 8px 12px; }
  main { padding: 20px 16px; }
  .article-grid { grid-template-columns: 1fr; }
  .article-card:nth-child(even) { margin-top: 0; }
  .list-title { font-size: 20px; }
  .brand h1 { font-size: 22px; }
  .detail-card { padding: 20px; }
  .detail-title { font-size: 22px; }
}
</style>
