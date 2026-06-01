<template>
  <AdminStatus v-if="isAdminStatus" />
  <template v-else>
  <div class="garden-canvas">
    <svg viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="glow1" cx="15%" cy="20%" r="25%"><stop offset="0%" stop-color="#5a8f5c" stop-opacity="0.1"/><stop offset="100%" stop-color="#5a8f5c" stop-opacity="0"/></radialGradient>
        <radialGradient id="glow2" cx="85%" cy="75%" r="30%"><stop offset="0%" stop-color="#e8743f" stop-opacity="0.07"/><stop offset="100%" stop-color="#e8743f" stop-opacity="0"/></radialGradient>
      </defs>
      <rect fill="url(#glow1)" width="1440" height="900"/>
      <rect fill="url(#glow2)" width="1440" height="900"/>
    </svg>
  </div>

  <div class="leaf-float" style="top:18%;left:4%"><span style="width:20px;height:34px;animation-delay:0s"></span></div>
  <div class="leaf-float" style="top:35%;right:5%"><span style="width:16px;height:28px;animation-delay:5s"></span></div>
  <div class="leaf-float" style="top:60%;left:2%"><span style="width:18px;height:30px;animation-delay:10s"></span></div>

  <!-- First-time Guide Overlay -->
  <div class="guide-overlay" v-if="showGuide">
    <div class="guide-backdrop" @click="dismissGuide"></div>
    <div class="guide-dialog" :class="'step-' + guideStep">
      <button class="guide-close" @click="dismissGuide">&times;</button>
      <div class="guide-arrow" v-if="guideStep === 0">↓</div>
      <h3>{{ t.guideTitle }}</h3>
      <p>{{ guideSteps[guideStep] }}</p>
      <div class="guide-dots">
        <span v-for="i in guideSteps.length" :key="i" :class="{ active: i - 1 === guideStep }"></span>
      </div>
      <div class="guide-actions">
        <button class="guide-skip" @click="dismissGuide">{{ t.guideSkip }}</button>
        <button class="guide-next" @click="nextGuideStep">
          {{ guideStep < guideSteps.length - 1 ? t.guideNext : t.guideDone }}
        </button>
      </div>
    </div>
  </div>

  <div class="app-shell" :class="{ dark: darkMode }">
    <header class="hero">
      <div class="hero-inner">
        <div class="brand">
          <div class="brand-icon">
            <svg viewBox="0 0 100 100" width="38" height="38">
              <defs>
                <radialGradient id="lcGrad" cx="36%" cy="28%" r="70%">
                  <stop offset="0%" stop-color="#ff817d"/>
                  <stop offset="58%" stop-color="#d9443f"/>
                  <stop offset="100%" stop-color="#951f2b"/>
                </radialGradient>
              </defs>
              <path d="M73 41c6 5 6 14 2 20 0 8-5 14-13 16-4 7-13 8-20 5-7 3-15-1-19-8-7-3-11-10-9-18-4-7-2-15 5-20 2-8 9-13 17-12 6-5 14-5 20 0 8 0 15 5 17 13Z" fill="url(#lcGrad)"/>
              <ellipse cx="35" cy="38" rx="7" ry="10" fill="#fff" opacity="0.16" transform="rotate(24 35 38)"/>
              <path d="M50 25c-1-9 0-16 2-23" stroke="#2f7d4e" stroke-width="4" fill="none" stroke-linecap="round"/>
              <path d="M50 13c-8-7-17-8-25-4 6 6 15 8 25 4Z" fill="#4a9a61"/>
              <path d="M52 14c7-8 16-11 24-8-5 6-14 9-24 8Z" fill="#2f7d4e"/>
            </svg>
          </div>
          <div>
            <h1>{{ t.appName }}</h1>
            <p class="tagline">{{ t.tagline }}</p>
          </div>
        </div>
        <div class="hero-actions">
          <button class="icon-btn" @click="toggleDark" :title="t.darkMode">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path v-if="darkMode" d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z"/><circle v-else cx="12" cy="12" r="5"/><line v-if="!darkMode" x1="12" y1="1" x2="12" y2="3"/><line v-if="!darkMode" x1="12" y1="21" x2="12" y2="23"/><line v-if="!darkMode" x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line v-if="!darkMode" x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line v-if="!darkMode" x1="1" y1="12" x2="3" y2="12"/><line v-if="!darkMode" x1="21" y1="12" x2="23" y2="12"/><line v-if="!darkMode" x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line v-if="!darkMode" x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
          </button>
          <button class="icon-btn lang-btn" @click="toggleLang" :title="t.switchLang">
            {{ lang === 'zh' ? 'EN' : '中' }}
          </button>
          <a class="icon-btn" href="https://github.com/porridgeowefish/lizhi" target="_blank" rel="noreferrer" title="GitHub">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
          </a>
          <button class="sync-button" :disabled="syncing" @click="runSync">
            {{ syncing ? t.syncing : t.syncNow }}
          </button>
          <div class="job-chip" v-if="lastSyncJob">
            {{ t.discarded }} {{ lastSyncJob.posts_discarded }}
          </div>
        </div>
      </div>
    </header>

    <main class="page">
      <section class="toolbar card">
        <div class="filter-panel">
          <div class="search-row">
            <input v-model="draftSearch" @keyup.enter="applyFilters" :placeholder="t.searchPlaceholder" />
            <button class="search-action" @click="applyFilters">搜索</button>
            <section class="support-widget" aria-label="荔枝支持">
              <div class="support-copy">
                <strong>{{ t.supportTitle }}</strong>
                <span>{{ t.supportHint }}</span>
              </div>
              <div class="support-action">
                <button
                  class="support-lychee-button"
                  :class="{ liked: supportLiked, popping: supportPulse }"
                  :disabled="supportLiked || supportBusy"
                  :aria-pressed="supportLiked"
                  :title="supportLiked ? t.supported : t.supportHint"
                  @click="supportProject"
                >
                  <svg viewBox="0 0 100 100" width="42" height="42" aria-hidden="true">
                    <defs>
                      <radialGradient id="supportLcGrad" cx="34%" cy="28%" r="72%">
                        <stop offset="0%" :stop-color="supportLiked ? '#ff8a85' : '#f7c7c4'"/>
                        <stop offset="58%" :stop-color="supportLiked ? '#dc4642' : '#d99a96'"/>
                        <stop offset="100%" :stop-color="supportLiked ? '#982433' : '#b87d7a'"/>
                      </radialGradient>
                    </defs>
                    <path d="M73 41c6 5 6 14 2 20 0 8-5 14-13 16-4 7-13 8-20 5-7 3-15-1-19-8-7-3-11-10-9-18-4-7-2-15 5-20 2-8 9-13 17-12 6-5 14-5 20 0 8 0 15 5 17 13Z" fill="url(#supportLcGrad)"/>
                    <ellipse cx="35" cy="38" rx="7" ry="10" fill="#fff" opacity="0.18" transform="rotate(24 35 38)"/>
                    <path d="M50 25c-1-9 0-16 2-23" stroke="#2f7d4e" stroke-width="4" fill="none" stroke-linecap="round"/>
                    <path d="M50 13c-8-7-17-8-25-4 6 6 15 8 25 4Z" fill="#4a9a61"/>
                    <path d="M52 14c7-8 16-11 24-8-5 6-14 9-24 8Z" fill="#2f7d4e"/>
                  </svg>
                </button>
                <div class="support-basket" aria-live="polite">
                  <svg viewBox="0 0 92 68" width="72" height="54" aria-hidden="true">
                    <defs>
                      <radialGradient id="basketLycheeGrad" cx="36%" cy="28%" r="72%">
                        <stop offset="0%" stop-color="#ff8a85"/>
                        <stop offset="62%" stop-color="#dc4642"/>
                        <stop offset="100%" stop-color="#982433"/>
                      </radialGradient>
                    </defs>
                    <g class="basket-lychees">
                      <circle cx="31" cy="25" r="10" fill="url(#basketLycheeGrad)"/>
                      <circle cx="46" cy="21" r="11" fill="url(#basketLycheeGrad)"/>
                      <circle cx="61" cy="26" r="10" fill="url(#basketLycheeGrad)"/>
                      <circle cx="39" cy="34" r="10" fill="url(#basketLycheeGrad)"/>
                      <circle cx="54" cy="35" r="9" fill="url(#basketLycheeGrad)"/>
                      <path d="M43 14c-2-5 1-9 5-11" stroke="#2f7d4e" stroke-width="3" fill="none" stroke-linecap="round"/>
                      <path d="M48 7c5-4 11-4 16-1-4 4-9 5-16 1Z" fill="#4a9a61"/>
                    </g>
                    <path d="M18 29h56l-7 31H25L18 29Z" fill="#c88a4b"/>
                    <path d="M23 30c6 9 40 9 46 0" fill="none" stroke="#8b5a2b" stroke-width="4" stroke-linecap="round"/>
                    <path d="M30 29c4-17 28-17 32 0" fill="none" stroke="#8b5a2b" stroke-width="5" stroke-linecap="round"/>
                    <path d="M28 39h36M27 49h38" stroke="#a36c34" stroke-width="2.5" stroke-linecap="round"/>
                  </svg>
                  <span class="support-count">{{ supportCount }}</span>
                  <span v-if="supportFloatKey" :key="supportFloatKey" class="support-plus-one">+1</span>
                </div>
              </div>
            </section>
          </div>
          <div class="chip-row">
            <button class="filter-chip" :class="{ active: filters.category === '' }" @click="setCategory('')">{{ t.allCategories }}</button>
            <button
              v-for="item in categoryOptions"
              :key="item.value"
              class="filter-chip"
              :class="{ active: filters.category === item.value }"
              @click="setCategory(item.value)"
            >
              {{ item.label }}
            </button>
          </div>
          <div class="chip-row compact">
            <button class="filter-chip" :class="{ active: filters.time_range === '' }" @click="setTimeRange('')">{{ t.allTime }}</button>
            <button class="filter-chip" :class="{ active: filters.time_range === 'this_week' }" @click="setTimeRange('this_week')">{{ t.thisWeek }}</button>
            <button class="filter-chip" :class="{ active: filters.time_range === 'this_weekend' }" @click="setTimeRange('this_weekend')">{{ t.thisWeekend }}</button>
            <button class="filter-chip" :class="{ active: filters.time_range === 'next_week' }" @click="setTimeRange('next_week')">{{ t.nextWeek }}</button>
            <span class="chip-divider"></span>
            <button class="filter-chip" :class="{ active: filters.sort === 'deadline' }" @click="setSort('deadline')">{{ t.sortByDeadline }}</button>
            <button class="filter-chip" :class="{ active: filters.sort === 'published' }" @click="setSort('published')">{{ t.sortByPublished }}</button>
          </div>
          <div class="active-filter-row" v-if="activeFilterChips.length">
            <button v-for="chip in activeFilterChips" :key="chip.key" class="active-filter-chip" @click="removeFilterChip(chip.key)">
              {{ chip.label }} <span>×</span>
            </button>
            <button class="clear-filter-chip" @click="clearAllFilters">清空筛选</button>
          </div>
        </div>
      </section>

      <section class="content-grid">
        <div class="list-column">
          <div class="list-head">
            <h2>{{ t.opportunityList }} <small v-if="total">{{ total }} {{ t.items }}</small></h2>
            <button class="ghost" v-if="activeSearch" @click="clearSearch">{{ t.clearSearch }}</button>
          </div>

          <div v-if="errorMessage" class="card state error">{{ errorMessage }}</div>
          <div v-else-if="loading" class="card state loading-state">
            <div class="lychee-loader">
              <svg viewBox="0 0 100 100" width="54" height="54" class="lychee-spin-loader">
                <defs>
                  <radialGradient id="loaderLcGrad" cx="36%" cy="28%" r="70%">
                    <stop offset="0%" stop-color="#ff817d"/>
                    <stop offset="58%" stop-color="#d9443f"/>
                    <stop offset="100%" stop-color="#951f2b"/>
                  </radialGradient>
                </defs>
                <g class="lychee-spinner">
                  <path d="M73 41c6 5 6 14 2 20 0 8-5 14-13 16-4 7-13 8-20 5-7 3-15-1-19-8-7-3-11-10-9-18-4-7-2-15 5-20 2-8 9-13 17-12 6-5 14-5 20 0 8 0 15 5 17 13Z" fill="url(#loaderLcGrad)"/>
                  <ellipse cx="35" cy="38" rx="7" ry="10" fill="#fff" opacity="0.16" transform="rotate(24 35 38)"/>
                  <path d="M50 25c-1-9 0-16 2-23" stroke="#2f7d4e" stroke-width="4" fill="none" stroke-linecap="round"/>
                  <path d="M50 13c-8-7-17-8-25-4 6 6 15 8 25 4Z" fill="#4a9a61"/>
                  <path d="M52 14c7-8 16-11 24-8-5 6-14 9-24 8Z" fill="#2f7d4e"/>
                </g>
              </svg>
              <span class="loading-text">{{ t.loading }}</span>
            </div>
          </div>
          <div v-else-if="posts.length === 0" class="card state">
            {{ t.noResults }}
          </div>

          <article
            v-for="post in posts"
            :key="post.id"
            class="card post-card"
            :class="{ selected: expandedId === post.id }"
            @click="toggleExpand(post)"
          >
            <div class="post-topline">
              <span class="pill tag-sm" :class="'tag-' + displayCategory(post)">{{ categoryLabel(displayCategory(post)) }}</span>
              <span class="post-date">{{ formatDate(post.published_at) }}</span>
            </div>
            <h3>{{ post.llm_title || post.title }}</h3>
            <p class="summary">{{ post.llm_summary || post.summary }}</p>
            <div class="post-bottom" v-if="post.key_time_at || post.source_name">
              <span class="deadline-tag" v-if="post.key_time_at" :class="'deadline-' + keyTimeTone(post)">
                {{ keyTimeLabel(post) }} - {{ keyTimeName(post) }} {{ formatDate(post.key_time_at) }}
              </span>
              <span class="source-tag">{{ post.source_name }}</span>
            </div>
            <div class="post-expand" v-if="expandedId === post.id">
              <dl class="expand-grid" v-if="hasAnyTime(post)">
                <div v-if="post.event_start_at"><dt>{{ t.startTime }}</dt><dd>{{ formatDate(post.event_start_at) }}</dd></div>
                <div v-if="post.event_end_at"><dt>{{ t.endTime }}</dt><dd>{{ formatDate(post.event_end_at) }}</dd></div>
                <div v-if="post.deadline_at"><dt>{{ t.deadlineTime }}</dt><dd>{{ formatDate(post.deadline_at) }}</dd></div>
              </dl>
              <a class="open-link" :href="post.original_url" target="_blank" rel="noreferrer">{{ t.viewOriginal }}</a>
            </div>
          </article>

          <div class="load-more-wrap" v-if="posts.length && posts.length < total">
            <button class="ghost" :disabled="loadingMore" @click="loadMore">
              {{ loadingMore ? t.loading : t.loadMore }}
            </button>
          </div>
        </div>
      </section>
    </main>

    <footer class="app-footer">
      <section class="sync-summary" v-if="lastSyncJob">
        <div class="sync-summary-title">同步结果</div>
        <div class="sync-metric"><strong>{{ syncMetrics.fetched }}</strong><span>抓取</span></div>
        <div class="sync-metric"><strong>{{ syncMetrics.valid }}</strong><span>有效</span></div>
        <div class="sync-metric"><strong>{{ syncMetrics.deduped }}</strong><span>去重</span></div>
        <div class="sync-metric filtered"><strong>{{ syncMetrics.filtered }}</strong><span>过滤宣传稿</span></div>
      </section>
      <div class="footer-brand">{{ t.appName }} · {{ t.tagline }}</div>
      <div class="footer-team">{{ t.devTeam }}</div>
    </footer>
  </div>
  </template>
</template>

<script>
import { computed, onMounted, ref } from 'vue'
import { addSupport, getPostCategories, getPosts, getSupport, syncNow } from './api.js'
import AdminStatus from './components/AdminStatus.vue'

const I18N = {
  zh: {
    appName: '荔知', tagline: '荔园花园 · 深大信息聚合', syncNow: '立即同步', syncing: '同步中...',
    discarded: '丢弃', searchPlaceholder: '搜索讲座、活动、志愿...',
    allCategories: '全部', sortByDeadline: '按截止时间', sortByPublished: '按发布时间',
    allTime: '全部', thisWeek: '这周', thisWeekend: '这周末', nextWeek: '下周',
    opportunityList: '机会列表', clearSearch: '清除搜索',
    items: '条',
    loading: '正在加载...', noResults: '当前筛选条件下没有机会内容。你可以切换分类，或搜索更宽泛的关键词。',
    deadline: '截止', loadMore: '加载更多', startTime: '开始时间', endTime: '结束时间',
    deadlineTime: '截止时间', notRecognized: '未识别', viewOriginal: '查看原文',
    selectHint: '从左侧选择一条机会内容，这里会显示详情。',
    darkMode: '切换夜间模式', switchLang: 'Switch to English',
    devTeam: '开发团队：哈基米',
    supportTitle: '给荔知加颗荔枝',
    supportHint: '喜欢点一下支持！',
    supported: '已经支持过啦',
    guideTitle: '使用指南', guideSkip: '跳过', guideNext: '下一步', guideDone: '开始使用',
    campus_activity: '校园活动', lecture: '讲座论坛', volunteer: '志愿公益',
    competition: '学科竞赛', recruitment: '就业招聘', graduate_study: '升学留学',
    exam_certification: '考试考证', other: '其他',
  },
  en: {
    appName: 'Lizhi', tagline: 'SZU Campus Info Hub', syncNow: 'Sync Now', syncing: 'Syncing...',
    discarded: 'Discarded', searchPlaceholder: 'Search lectures, events...',
    allCategories: 'All', sortByDeadline: 'By Deadline', sortByPublished: 'By Published',
    allTime: 'All', thisWeek: 'This Week', thisWeekend: 'This Weekend', nextWeek: 'Next Week',
    opportunityList: 'Opportunities', clearSearch: 'Clear',
    items: 'items',
    loading: 'Loading...', noResults: 'No results found. Try different filters or keywords.',
    deadline: 'Due', loadMore: 'Load More', startTime: 'Start', endTime: 'End',
    deadlineTime: 'Deadline', notRecognized: 'N/A', viewOriginal: 'View Original',
    selectHint: 'Select an item from the list to view details.',
    darkMode: 'Toggle Dark Mode', switchLang: '切换中文',
    devTeam: 'Dev Team: Hajimi',
    supportTitle: 'Add a lychee',
    supportHint: 'Tap once if you like it.',
    supported: 'Already supported',
    guideTitle: 'Quick Guide', guideSkip: 'Skip', guideNext: 'Next', guideDone: 'Get Started',
    campus_activity: 'Campus Activity', lecture: 'Lecture Forum', volunteer: 'Volunteer',
    competition: 'Competition', recruitment: 'Recruitment', graduate_study: 'Graduate Study',
    exam_certification: 'Certification Exam', other: 'Other',
  },
}

const CATEGORY_KEYS = ['campus_activity', 'competition', 'volunteer', 'exam_certification', 'recruitment', 'lecture', 'graduate_study', 'other']
const CATEGORY_KEY_SET = new Set(CATEGORY_KEYS)
const LEGACY_CATEGORY_MAP = {
  club_activity: 'campus_activity',
  exam: 'exam_certification',
  notice: 'other',
}
const SUPPORT_CLIENT_KEY = 'lizhi-support-client-id'
const SUPPORT_LIKED_KEY = 'lizhi-support-liked'

function getSupportClientId() {
  let clientId = localStorage.getItem(SUPPORT_CLIENT_KEY)
  if (!clientId) {
    clientId = globalThis.crypto?.randomUUID?.() || `lizhi-${Date.now()}-${Math.random().toString(16).slice(2)}`
    localStorage.setItem(SUPPORT_CLIENT_KEY, clientId)
  }
  return clientId
}

export default {
  name: 'App',
  components: { AdminStatus },
  setup() {
    const isAdminStatus = window.location.pathname.replace(/\/+$/, '') === '/admin/status'
    const posts = ref([])
    const total = ref(0)
    const stats = ref({ categories: [], content_type_stats: {}, participation_stats: {}, time_status_stats: {} })
    const expandedId = ref(null)
    const loading = ref(false)
    const loadingMore = ref(false)
    const syncing = ref(false)
    const errorMessage = ref('')
    const draftSearch = ref('')
    const activeSearch = ref('')
    const offset = ref(0)
    const lastSyncJob = ref(null)
    const filters = ref({ category: '', time_range: '', sort: 'deadline' })
    const supportCount = ref(0)
    const supportLiked = ref(localStorage.getItem(SUPPORT_LIKED_KEY) === '1')
    const supportBusy = ref(false)
    const supportPulse = ref(false)
    const supportFloatKey = ref(0)

    const lang = ref(localStorage.getItem('lizhi-lang') || 'zh')
    const darkMode = ref(localStorage.getItem('lizhi-dark') === 'true')

    const showGuide = ref(false)
    const guideStep = ref(0)

    const t = computed(() => I18N[lang.value])

    const guideStepsZh = [
      '在搜索框输入关键词，快速查找讲座、活动、竞赛等信息。',
      '使用分类筛选和「这周/这周末/下周」按钮，快速定位感兴趣的时间段。',
      '点击「按截止时间」查看最紧急的机会，或「按发布时间」看最新内容。',
      '点击任意一条机会，右侧会显示详情、时间信息和原文链接。',
    ]
    const guideStepsEn = [
      'Type keywords in the search box to find lectures, events, and more.',
      'Use category filter and time range buttons to narrow results.',
      'Sort by deadline for urgency, or by published date for recency.',
      'Click any item to view full details, time info, and source link.',
    ]
    const guideSteps = computed(() => lang.value === 'zh' ? guideStepsZh : guideStepsEn)

    const categoryOptions = computed(() =>
      CATEGORY_KEYS.map(key => ({ value: key, label: t.value[key] || key })),
    )
    const timeRangeOptions = computed(() => ({
      this_week: t.value.thisWeek,
      this_weekend: t.value.thisWeekend,
      next_week: t.value.nextWeek,
    }))
    const syncMetrics = computed(() => {
      if (!lastSyncJob.value) return { fetched: 0, valid: 0, deduped: 0, filtered: 0 }
      const fetched = Number(lastSyncJob.value.posts_fetched || 0)
      const inserted = Number(lastSyncJob.value.posts_inserted || 0)
      const updated = Number(lastSyncJob.value.posts_updated || 0)
      const filtered = Number(lastSyncJob.value.posts_discarded || lastSyncJob.value.discarded_count || 0)
      return {
        fetched,
        valid: inserted + updated,
        deduped: Math.max(fetched - inserted - updated - filtered, 0),
        filtered,
      }
    })
    const activeFilterChips = computed(() => {
      const chips = []
      if (activeSearch.value) chips.push({ key: 'search', label: activeSearch.value })
      if (filters.value.category) chips.push({ key: 'category', label: categoryLabel(filters.value.category) })
      if (filters.value.time_range) chips.push({ key: 'time_range', label: timeRangeOptions.value[filters.value.time_range] || filters.value.time_range })
      if (filters.value.sort && filters.value.sort !== 'deadline') chips.push({ key: 'sort', label: t.value.sortByPublished })
      return chips
    })

    function categoryLabel(key) { return t.value[key] || key || '' }
    function normalizeCategory(key) {
      if (CATEGORY_KEY_SET.has(key)) return key
      return LEGACY_CATEGORY_MAP[key] || ''
    }
    function displayCategory(post) {
      if (filters.value.category) return filters.value.category
      const primaryCategory = normalizeCategory(post?.primary_category)
      if (primaryCategory) return primaryCategory
      const categories = Array.isArray(post?.categories) ? post.categories : []
      return categories.map(normalizeCategory).find(Boolean) || 'other'
    }
    function setCategory(category) {
      filters.value.category = category
      expandedId.value = null
      loadPosts()
    }

    function setTimeRange(range) {
      filters.value.time_range = range
      expandedId.value = null
      loadPosts()
    }

    function toggleLang() {
      lang.value = lang.value === 'zh' ? 'en' : 'zh'
      localStorage.setItem('lizhi-lang', lang.value)
    }
    function toggleDark() {
      darkMode.value = !darkMode.value
      localStorage.setItem('lizhi-dark', String(darkMode.value))
    }
    function dismissGuide() {
      showGuide.value = false
      localStorage.setItem('lizhi-guide-done', '1')
    }
    function nextGuideStep() {
      if (guideStep.value < guideSteps.value.length - 1) { guideStep.value++ }
      else { dismissGuide() }
    }

    function buildParams(nextOffset = 0) {
      const params = { offset: nextOffset, limit: 20 }
      if (filters.value.category) params.category = filters.value.category
      if (filters.value.time_range) params.time_range = filters.value.time_range
      if (filters.value.sort) params.sort = filters.value.sort
      if (activeSearch.value) params.search = activeSearch.value
      return params
    }

    async function loadPosts({ append = false } = {}) {
      if (!append) { loading.value = true; errorMessage.value = '' }
      try {
        const payload = await getPosts(buildParams(append ? offset.value : 0))
        posts.value = append ? [...posts.value, ...payload.items] : payload.items
        total.value = payload.total
        offset.value = posts.value.length
      } catch (error) {
        errorMessage.value = error?.response?.data?.detail || 'Failed to load data.'
      } finally { loading.value = false; loadingMore.value = false }
    }

    async function loadStats() {
      try {
        stats.value = await getPostCategories()
      } catch (error) {
        stats.value = { categories: [], content_type_stats: {}, participation_stats: {}, time_status_stats: {} }
      }
    }
    function toggleExpand(post) { expandedId.value = expandedId.value === post.id ? null : post.id }
    function applyFilters() { activeSearch.value = draftSearch.value.trim(); expandedId.value = null; loadPosts() }
    function clearSearch() { draftSearch.value = ''; activeSearch.value = ''; loadPosts() }
    function setSort(mode) { filters.value.sort = mode; expandedId.value = null; loadPosts() }
    function removeFilterChip(key) {
      if (key === 'search') { draftSearch.value = ''; activeSearch.value = '' }
      if (key === 'category') filters.value.category = ''
      if (key === 'time_range') filters.value.time_range = ''
      if (key === 'sort') filters.value.sort = 'deadline'
      expandedId.value = null
      loadPosts()
    }
    function clearAllFilters() {
      draftSearch.value = ''
      activeSearch.value = ''
      filters.value = { category: '', time_range: '', sort: 'deadline' }
      expandedId.value = null
      loadPosts()
    }
    function loadMore() { loadingMore.value = true; loadPosts({ append: true }) }
    function hasAnyTime(post) { return post.event_start_at || post.event_end_at || post.deadline_at }
    async function runSync() {
      syncing.value = true
      try { lastSyncJob.value = await syncNow(); await Promise.all([loadPosts(), loadStats()]) }
      finally { syncing.value = false }
    }
    function formatDate(value) {
      if (!value) return ''
      const d = new Date(value)
      return Number.isNaN(d.getTime()) ? '' : `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
    }
    function daysUntil(value) {
      if (!value) return null
      const d = new Date(value)
      if (Number.isNaN(d.getTime())) return null
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      d.setHours(0, 0, 0, 0)
      return Math.ceil((d - today) / 86400000)
    }
    function deadlineTone(value) {
      const days = daysUntil(value)
      if (days === null) return 'muted'
      if (days <= 3) return 'urgent'
      if (days <= 7) return 'soon'
      return 'later'
    }
    function deadlineLabel(value) {
      const days = daysUntil(value)
      if (days === null) return t.value.deadline
      if (days < 0) return '已截止'
      if (days <= 3) return '3天内截止'
      if (days <= 7) return '7天内'
      return '7天外'
    }

    function keyTimeName(post) {
      if (post.key_time_type === 'event_start') return lang.value === 'zh' ? '活动' : 'Event'
      return t.value.deadline
    }
    function keyTimeTone(post) {
      const days = daysUntil(post.key_time_at)
      if (days === null) return 'muted'
      if (days < 0) return 'muted'
      if (days <= 3) return 'urgent'
      if (days <= 7) return 'soon'
      return 'later'
    }
    function keyTimeLabel(post) {
      const days = daysUntil(post.key_time_at)
      const isEvent = post.key_time_type === 'event_start'
      const action = isEvent
        ? (lang.value === 'zh' ? '活动' : 'event')
        : (lang.value === 'zh' ? '截止' : 'due')
      if (days === null) return keyTimeName(post)
      if (days < 0) return isEvent ? (lang.value === 'zh' ? '活动已过' : 'Event passed') : (lang.value === 'zh' ? '已截止' : 'Past due')
      if (days === 0) return isEvent ? (lang.value === 'zh' ? '今天活动' : 'Today') : (lang.value === 'zh' ? '今天截止' : 'Due today')
      return lang.value === 'zh' ? `距离${action} ${days} 天` : `${days} days to ${action}`
    }


    async function loadSupport() {
      try {
        const payload = await getSupport(getSupportClientId())
        supportCount.value = Number(payload.count || 0)
        supportLiked.value = Boolean(payload.liked) || localStorage.getItem(SUPPORT_LIKED_KEY) === '1'
      } catch (error) {
        supportLiked.value = localStorage.getItem(SUPPORT_LIKED_KEY) === '1'
      }
    }

    async function supportProject() {
      if (supportLiked.value || supportBusy.value) return
      supportBusy.value = true
      try {
        const payload = await addSupport(getSupportClientId())
        supportCount.value = Number(payload.count || supportCount.value)
        supportLiked.value = Boolean(payload.liked)
        if (payload.incremented) {
          supportFloatKey.value += 1
          supportPulse.value = true
          window.setTimeout(() => { supportPulse.value = false }, 520)
          window.setTimeout(() => { supportFloatKey.value = 0 }, 980)
        }
        if (supportLiked.value) localStorage.setItem(SUPPORT_LIKED_KEY, '1')
      } finally {
        supportBusy.value = false
      }
    }

    onMounted(async () => {
      if (isAdminStatus) return
      await Promise.allSettled([loadPosts(), loadStats(), loadSupport()])
      if (!localStorage.getItem('lizhi-guide-done')) { showGuide.value = true }
    })

    return {
      isAdminStatus,
      posts, total, stats, expandedId, loading, loadingMore, syncing, errorMessage,
      draftSearch, activeSearch, filters, lastSyncJob,
      supportCount, supportLiked, supportBusy, supportPulse, supportFloatKey,
      lang, darkMode, t, showGuide, guideStep, guideSteps,
      categoryOptions, activeFilterChips, syncMetrics, categoryLabel, displayCategory, deadlineTone, deadlineLabel, keyTimeTone, keyTimeLabel, keyTimeName,
      toggleLang, toggleDark, dismissGuide, nextGuideStep,
      applyFilters, clearSearch, clearAllFilters, removeFilterChip, setCategory, setSort, setTimeRange, toggleExpand, loadMore, runSync, supportProject, formatDate, hasAnyTime,
    }
  },
}
</script>

<style>
/* === Garden Design System === */
:root {
  --bg: #f0f7ed;
  --card: #ffffff;
  --line: #c8dcc3;
  --text: #2d3a29;
  --muted: #6b7a66;
  --primary: #5a8f5c;
  --accent: #e8743f;
  --soft: #e8f5e9;
  --title-font: 'ZCOOL XiaoWei', serif;
  --body-font: 'LXGW WenKai TC', -apple-system, 'PingFang SC', sans-serif;
  --tag-font: 'Nunito', sans-serif;
  --tag-campus_activity: #d4edda; --tag-campus_activity-fg: #2d6a3e;
  --tag-lecture: #d6eaf8; --tag-lecture-fg: #1a5276;
  --tag-volunteer: #fdebd0; --tag-volunteer-fg: #b9770e;
  --tag-recruitment: #d1f2eb; --tag-recruitment-fg: #0e6655;
  --tag-competition: #e8daef; --tag-competition-fg: #6c3483;
  --tag-graduate_study: #fff3cd; --tag-graduate_study-fg: #7a5b00;
  --tag-exam_certification: #fadbd8; --tag-exam_certification-fg: #922b21;
  --tag-other: #eaecee; --tag-other-fg: #5d6d7e;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: var(--body-font);
  background:
    radial-gradient(ellipse at 15% 20%, rgba(90,143,92,0.12) 0%, transparent 70%),
    radial-gradient(ellipse at 85% 75%, rgba(232,116,63,0.08) 0%, transparent 70%),
    radial-gradient(ellipse at 50% 10%, rgba(139,195,74,0.06) 0%, transparent 70%),
    var(--bg);
  color: var(--text);
  line-height: 1.6;
}

button, input, select { font: inherit; }

/* === Organic Background Canvas === */
.garden-canvas {
  position: fixed; top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none; z-index: 0;
}
.garden-canvas svg { width: 100%; height: 100%; }

/* === Floating Leaf Particles === */
.leaf-float {
  position: fixed; pointer-events: none; z-index: 0; opacity: 0.18;
}
.leaf-float span {
  display: block; border-radius: 50% 0 50% 50%;
  background: linear-gradient(135deg, var(--primary), #8bc34a);
  animation: leafDrift 20s ease-in-out infinite;
}
@keyframes leafDrift {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  25% { transform: translateY(-18px) rotate(8deg); }
  50% { transform: translateY(6px) rotate(-5deg); }
  75% { transform: translateY(-10px) rotate(3deg); }
}

/* === Layout Shell === */
.app-shell {
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

/* === Hero Header with Green Gradient === */
.hero {
  background: linear-gradient(160deg, #3d7a3f 0%, #5a8f5c 35%, #72a874 65%, #8bb890 100%);
  color: #fff;
  position: relative;
  z-index: 100;
  padding-bottom: 32px;
  box-shadow: 0 6px 30px rgba(45,58,41,0.18);
}
.hero::after {
  content: '';
  position: absolute; bottom: -2px; left: 0; right: 0;
  height: 40px;
  background: var(--bg);
  border-radius: 50% 50% 0 0 / 100% 100% 0 0;
}

.hero-inner, .page {
  max-width: 1280px;
  margin: 0 auto;
}

.hero-inner {
  padding: 22px 24px 0;
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

/* === Brand Icon === */
.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}
.brand-icon {
  width: 56px; height: 56px;
  background: transparent;
  display: flex; align-items: center; justify-content: center;
  border-radius: 0;
  box-shadow: none;
  position: relative;
  overflow: visible;
}
.brand-icon svg {
  width: 48px;
  height: 48px;
  filter: drop-shadow(0 4px 10px rgba(120, 24, 30, 0.24));
}
.brand h1 {
  font-family: var(--title-font);
  font-size: 26px;
  letter-spacing: 4px;
  text-shadow: 0 2px 8px rgba(0,0,0,0.15);
  margin: 0;
}
.brand .tagline {
  font-size: 12px;
  opacity: 0.8;
  letter-spacing: 1.5px;
  margin-top: 2px;
}

.hero-copy {
  display: none;
}

.hero-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

/* === Toolbar / Category Nav === */
.toolbar {
  background: var(--card);
  border: none;
  border-bottom: 1px solid var(--line);
  border-radius: 0;
  box-shadow: 0 2px 12px rgba(45,58,41,0.06);
  position: sticky;
  top: 0;
  z-index: 90;
  padding: 12px 0;
}

.filter-panel {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
  display: grid;
  gap: 10px;
}

.search-row {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.search-row input {
  flex: 1;
  min-width: 0;
  height: 42px;
  padding: 9px 16px 9px 42px;
  border: 1.5px solid var(--line);
  border-radius: 100px;
  color: var(--text);
  background: rgba(90,143,92,0.04) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='17' height='17' viewBox='0 0 24 24' fill='none' stroke='%236b7a66' stroke-width='2'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'/%3E%3C/svg%3E") 16px center no-repeat;
  outline: none;
}

.search-row input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(90,143,92,0.1);
}

.search-action {
  height: 42px;
  padding: 0 18px;
  border: none;
  border-radius: 100px;
  background: var(--primary);
  color: #fff;
  cursor: pointer;
  font-family: var(--tag-font);
  font-weight: 800;
}

.chip-row,
.active-filter-row {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.chip-row::-webkit-scrollbar,
.active-filter-row::-webkit-scrollbar {
  display: none;
}

.chip-row.compact {
  align-items: center;
}

.filter-chip,
.active-filter-chip,
.clear-filter-chip {
  flex: 0 0 auto;
  height: 32px;
  padding: 0 14px;
  border: 1.5px solid var(--line);
  border-radius: 100px;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  font-family: var(--tag-font);
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
}

.filter-chip.active,
.filter-chip:hover {
  border-color: var(--primary);
  background: rgba(90,143,92,0.12);
  color: var(--primary);
}

.active-filter-chip {
  border-color: rgba(232,116,63,0.22);
  background: rgba(232,116,63,0.1);
  color: var(--accent);
}

.active-filter-chip span {
  margin-left: 4px;
}

.clear-filter-chip {
  border-color: transparent;
  color: var(--muted);
}

.chip-divider {
  flex: 0 0 1px;
  height: 22px;
  background: var(--line);
  margin: 5px 2px;
}

.toolbar-grid {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  gap: 8px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
.toolbar-grid::-webkit-scrollbar { display: none; }

.toolbar-grid label {
  display: contents;
}
.toolbar-grid label span {
  display: none;
}
.toolbar-grid input,
.toolbar-grid select {
  display: inline-flex;
  align-items: center;
  padding: 7px 20px;
  border: 1.5px solid var(--line);
  border-radius: 100px;
  background: transparent;
  color: var(--muted);
  font-family: var(--tag-font);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.3s;
  min-width: auto;
  width: auto;
  flex-shrink: 0;
}
.toolbar-grid input {
  min-width: 180px;
  padding-left: 36px;
  background: rgba(90,143,92,0.04) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%236b7a66' stroke-width='2'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'/%3E%3C/svg%3E") 14px center no-repeat;
}
.toolbar-grid input::placeholder {
  color: var(--muted);
  font-weight: 400;
}
.toolbar-grid input:focus,
.toolbar-grid select:focus {
  border-color: var(--primary);
  color: var(--primary);
  background-color: rgba(90,143,92,0.06);
  outline: none;
}
.toolbar-grid select:focus {
  background: rgba(90,143,92,0.06);
}
.sort-toggle {
  display: flex;
  gap: 0;
  border: 1.5px solid var(--line);
  border-radius: 100px;
  overflow: hidden;
}
.sort-toggle button {
  padding: 7px 14px;
  font-size: 0.82rem;
  border: none;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}
.sort-toggle button.active {
  background: var(--primary);
  color: #fff;
}
.sort-toggle button:not(.active):hover {
  background: rgba(90,143,92,0.08);
}
.time-range-toggle {
  display: flex;
  gap: 0;
  border: 1.5px solid var(--line);
  border-radius: 100px;
  overflow: hidden;
}
.time-range-toggle button {
  padding: 7px 12px;
  font-size: 0.82rem;
  border: none;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  white-space: nowrap;
}
.time-range-toggle button.active {
  background: var(--primary);
  color: #fff;
}
.time-range-toggle button:not(.active):hover {
  background: rgba(90,143,92,0.08);
}

/* === Page & Content Grid === */
.page {
  padding: 28px 24px 40px;
}

/* === Content Grid === */
.content-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

.list-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.list-head h2 {
  margin: 0;
  font-family: var(--title-font);
  color: var(--primary);
  position: relative;
}
.list-head h2::after {
  content: '';
  display: block;
  width: 40px; height: 3px;
  background: linear-gradient(90deg, var(--accent), transparent);
  border-radius: 2px;
  margin-top: 6px;
}

.list-column { min-width: 0; }

/* === Post Cards with Leaf Decorations === */
.card {
  border: 1px solid var(--line);
  background: var(--card);
  border-radius: 20px;
  box-shadow: 0 2px 14px rgba(45,58,41,0.06);
}

.post-card {
  padding: 22px 22px 18px;
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform 0.35s ease, box-shadow 0.35s ease;
  position: relative;
  overflow: visible;
  animation: growIn 0.5s ease both;
}
.post-card::before {
  content: '';
  position: absolute; top: -6px; right: -4px;
  width: 36px; height: 20px;
  background: linear-gradient(135deg, rgba(90,143,92,0.3), rgba(139,195,74,0.1));
  border-radius: 0 50% 0 50%;
  transform: rotate(30deg);
  z-index: 2;
  transition: transform 0.3s, opacity 0.3s;
}
.post-card:hover {
  transform: scale(1.02) translateY(-4px);
  box-shadow: 0 12px 36px rgba(45,58,41,0.13), 0 4px 12px rgba(90,143,92,0.08);
  border-color: var(--primary);
}
.post-card:hover::before {
  transform: rotate(40deg) scale(1.15);
  opacity: 0.9;
}
.post-card.selected {
  transform: scale(1.02) translateY(-4px);
  box-shadow: 0 12px 36px rgba(45,58,41,0.13), 0 4px 12px rgba(90,143,92,0.08);
  border-color: var(--primary);
}
@keyframes growIn {
  from { opacity: 0; transform: scale(0.94) translateY(16px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.post-topline,
.score-row,
.detail-topline {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--muted);
  font-size: 13px;
  font-family: var(--tag-font);
}

.post-card h3,
.detail-card h2 {
  margin: 12px 0 10px;
  line-height: 1.35;
  font-family: var(--title-font);
  transition: color 0.2s;
}
.post-card:hover h3 {
  color: var(--primary);
}

.summary, .detail-summary {
  color: var(--muted);
  line-height: 1.7;
}

.meta-row, .detail-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 14px 0;
}

/* === Category-Specific Pill Colors === */
.pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 12px;
  border-radius: 100px;
  font-family: var(--tag-font);
  font-size: 11px;
  font-weight: 700;
  background: var(--soft);
  color: var(--text);
  transition: transform 0.2s;
}
.pill:hover { transform: scale(1.06); }

.pill.tag-campus_activity { background: var(--tag-campus_activity); color: var(--tag-campus_activity-fg); }
.pill.tag-lecture { background: var(--tag-lecture); color: var(--tag-lecture-fg); }
.pill.tag-volunteer { background: var(--tag-volunteer); color: var(--tag-volunteer-fg); }
.pill.tag-recruitment { background: var(--tag-recruitment); color: var(--tag-recruitment-fg); }
.pill.tag-competition { background: var(--tag-competition); color: var(--tag-competition-fg); }
.pill.tag-graduate_study { background: var(--tag-graduate_study); color: var(--tag-graduate_study-fg); }
.pill.tag-exam_certification { background: var(--tag-exam_certification); color: var(--tag-exam_certification-fg); }
.pill.tag-other { background: var(--tag-other); color: var(--tag-other-fg); }

.pill.success { background: rgba(90,143,92,0.12); color: var(--primary); }
.pill.warning { background: rgba(232,116,63,0.12); color: var(--accent); }
.pill.muted { background: rgba(107,122,102,0.12); color: var(--muted); }

.score-row { margin-top: 10px; }
.pill.tag-sm {
  padding: 2px 8px;
  font-size: 10px;
}
.post-date {
  font-size: 12px;
  font-family: var(--tag-font);
  color: var(--muted);
}
.post-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  gap: 8px;
}
.deadline-tag {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 12px;
  font-family: var(--tag-font);
  color: var(--accent);
  font-weight: 700;
}
.deadline-urgent {
  background: #fde2df;
  color: #a82d25;
}
.deadline-soon {
  background: #fff0d8;
  color: #b86700;
}
.deadline-later {
  background: rgba(90,143,92,0.12);
  color: var(--primary);
}
.deadline-muted {
  background: rgba(107,122,102,0.12);
  color: var(--muted);
}
.source-tag {
  font-size: 11px;
  font-family: var(--tag-font);
  color: var(--muted);
  opacity: 0.7;
}
.list-head small {
  font-size: 13px;
  font-weight: 400;
  color: var(--muted);
  margin-left: 8px;
}

/* === Inline Expand === */
.post-expand {
  border-top: 1px solid var(--line);
  margin-top: 12px;
  padding-top: 12px;
  animation: expandIn 0.25s ease;
}
@keyframes expandIn {
  from { opacity: 0; max-height: 0; }
  to { opacity: 1; max-height: 200px; }
}
.expand-grid {
  display: flex;
  gap: 20px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.expand-grid div {
  display: flex;
  gap: 6px;
  font-size: 12px;
}
.expand-grid dt {
  color: var(--muted);
  font-family: var(--tag-font);
}
.expand-grid dd {
  margin: 0;
}

.state {
  padding: 24px;
  color: var(--muted);
}
.state.error {
  color: #a13333;
  border-color: rgba(161,51,51,0.35);
}

/* === Lychee Loading Animation === */
.loading-state {
  display: flex;
  justify-content: center;
  padding: 48px 24px !important;
}
.lychee-loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.lychee-spin-loader {
  overflow: visible;
}
.lychee-spinner {
  transform-box: fill-box;
  transform-origin: center center;
  transform-style: preserve-3d;
  animation: lycheeSpin 0.9s linear infinite;
}
.loading-text {
  font-size: 0.85rem;
  color: var(--muted);
  animation: fadeInOut 1.2s ease-in-out infinite;
}
@keyframes lycheeSpin {
  0% { transform: rotateY(0deg); }
  25% { transform: rotateY(90deg); }
  50% { transform: rotateY(180deg); }
  75% { transform: rotateY(270deg); }
  100% { transform: rotateY(360deg); }
}
@keyframes fadeInOut {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

/* === Buttons === */
.sync-button, .ghost, .open-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 16px;
  border-radius: 100px;
  border: 1.5px solid rgba(255,255,255,0.3);
  background: rgba(255,255,255,0.15);
  color: #fff;
  text-decoration: none;
  cursor: pointer;
  font-family: var(--tag-font);
  font-size: 13px;
  font-weight: 700;
  transition: all 0.3s;
  backdrop-filter: blur(4px);
}
.sync-button:hover {
  background: rgba(255,255,255,0.28);
  transform: translateY(-1px);
}
.sync-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ghost {
  background: transparent;
  border-color: var(--primary);
  color: var(--primary);
}
.ghost:hover {
  background: var(--primary);
  color: #fff;
}

.job-chip {
  padding: 8px 12px;
  border-radius: 100px;
  background: rgba(255,255,255,0.15);
  color: #fff;
  font-size: 13px;
  font-family: var(--tag-font);
  backdrop-filter: blur(4px);
}

.sync-summary {
  max-width: 760px;
  margin: 0 auto 18px;
  padding: 12px 16px;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: rgba(255,255,255,0.72);
  display: grid;
  grid-template-columns: minmax(80px, 1.1fr) repeat(4, minmax(72px, 1fr));
  gap: 10px;
  align-items: center;
  box-shadow: 0 6px 18px rgba(45,58,41,0.06);
}

.sync-summary-title {
  color: var(--primary);
  font-family: var(--tag-font);
  font-size: 13px;
  font-weight: 900;
  text-align: left;
}

.sync-metric {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 5px;
  min-width: 0;
  color: var(--muted);
  font-size: 12px;
  font-family: var(--tag-font);
}

.sync-metric strong {
  color: var(--text);
  font-size: 19px;
  line-height: 1;
}

.sync-metric.filtered strong {
  color: var(--accent);
}

.load-more-wrap {
  margin-top: 10px;
  display: flex;
  justify-content: center;
}

.open-link {
  background: transparent;
  border: none;
  color: var(--primary);
  padding: 0;
  font-size: 13px;
  position: relative;
  padding-bottom: 1px;
}
.open-link::after {
  content: '';
  position: absolute; bottom: 0; left: 0;
  width: 0; height: 1.5px;
  background: var(--accent);
  transition: width 0.3s;
  border-radius: 1px;
}
.open-link:hover {
  color: var(--accent);
}
.open-link:hover::after {
  width: 100%;
}

/* === Footer === */
.app-footer {
  text-align: center;
  padding: 32px 24px;
  color: var(--muted);
  font-size: 12px;
  border-top: 1px solid var(--line);
  margin-top: 48px;
}
.app-footer::before {
  content: '';
  display: block;
  width: 60px; height: 3px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  border-radius: 2px;
  margin: 0 auto 16px;
}

.support-widget {
  width: auto;
  margin: 0 0 0 4px;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.support-copy {
  display: grid;
  gap: 2px;
  text-align: left;
  min-width: 76px;
}

.support-copy strong {
  display: none;
}

.support-copy span {
  color: var(--muted);
  opacity: 0.64;
  font-size: 12px;
}

.support-action {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.support-lychee-button {
  width: 48px;
  height: 48px;
  border: 0;
  padding: 0;
  border-radius: 44% 52% 48% 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.72);
  box-shadow: 0 8px 20px rgba(120,24,30,0.12);
  cursor: pointer;
  transform-origin: center center;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.support-lychee-button:hover {
  transform: translateY(-2px) scale(1.04);
  box-shadow: 0 12px 24px rgba(120,24,30,0.18);
}

.support-lychee-button.liked {
  background: #fff4f2;
  box-shadow: 0 10px 24px rgba(152,36,51,0.22);
}

.support-lychee-button.popping {
  animation: supportPop 0.52s ease;
}

.support-lychee-button:disabled {
  cursor: default;
  opacity: 1;
}

.support-lychee-button:disabled:hover {
  transform: none;
}

.support-basket {
  position: relative;
  min-width: 82px;
  height: 58px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.support-basket svg {
  filter: drop-shadow(0 5px 8px rgba(80,50,22,0.16));
}

.support-count {
  position: absolute;
  bottom: 4px;
  min-width: 24px;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(255,255,255,0.86);
  color: #7c4f28;
  font-family: var(--tag-font);
  font-size: 12px;
  font-weight: 900;
}

.support-plus-one {
  position: absolute;
  left: 50%;
  top: -10px;
  color: var(--accent);
  font-family: var(--tag-font);
  font-size: 17px;
  font-weight: 900;
  pointer-events: none;
  animation: supportFloat 0.95s ease-out forwards;
}

@keyframes supportPop {
  0% { transform: scale(1); }
  42% { transform: scale(1.14) rotate(-4deg); }
  100% { transform: scale(1); }
}

@keyframes supportFloat {
  0% { opacity: 0; transform: translate(-50%, 10px) scale(0.9); }
  20% { opacity: 1; }
  100% { opacity: 0; transform: translate(-50%, -32px) scale(1.08); }
}

/* === Dark Mode === */
.app-shell.dark {
  --bg: #1a1f1a;
  --card: #242a24;
  --line: #3a4a3a;
  --text: #d4e0d4;
  --muted: #8a9a8a;
  --primary: #7ab87c;
  --accent: #f09060;
  --soft: #2a3a2a;
}
.app-shell.dark body,
.app-shell.dark {
  background: #1a1f1a;
  color: #d4e0d4;
}
.app-shell.dark .hero {
  background: linear-gradient(160deg, #2a4a2c 0%, #3a6a3c 35%, #4a7a4c 65%, #5a8a5c 100%);
}
.app-shell.dark .toolbar {
  background: #242a24;
  border-bottom-color: #3a4a3a;
}
.app-shell.dark .toolbar-grid input {
  background: rgba(122,184,124,0.06) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%238a9a8a' stroke-width='2'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'/%3E%3C/svg%3E") 14px center no-repeat;
}

/* === Icon Buttons (Lang / Dark / GitHub) === */
.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px; height: 36px;
  border-radius: 50%;
  border: 1.5px solid rgba(255,255,255,0.3);
  background: rgba(255,255,255,0.1);
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  font-size: 12px;
  font-weight: 700;
  font-family: var(--tag-font);
  backdrop-filter: blur(4px);
}
.icon-btn:hover {
  background: rgba(255,255,255,0.25);
  transform: translateY(-1px);
}
.lang-btn {
  font-size: 11px;
  letter-spacing: 0.5px;
}

/* === Footer Team Credit === */
.footer-team {
  font-size: 11px;
  opacity: 0.4;
  margin-top: 6px;
  letter-spacing: 1px;
}

/* === Guide Overlay === */
.guide-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.guide-backdrop {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(3px);
}
.guide-dialog {
  position: relative;
  background: var(--card);
  color: var(--text);
  border-radius: 20px;
  padding: 32px 36px 24px;
  max-width: 420px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  text-align: center;
  animation: guideIn 0.4s ease;
}
@keyframes guideIn {
  from { opacity: 0; transform: translateY(30px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.guide-close {
  position: absolute;
  top: 12px; right: 16px;
  background: none; border: none;
  font-size: 22px; color: var(--muted);
  cursor: pointer;
}
.guide-arrow {
  position: absolute;
  top: -28px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 28px;
  color: var(--primary);
  animation: guideBounce 1.5s ease infinite;
}
@keyframes guideBounce {
  0%, 100% { transform: translateX(-50%) translateY(0); }
  50% { transform: translateX(-50%) translateY(-8px); }
}
.guide-dialog h3 {
  margin: 0 0 12px;
  font-family: var(--title-font);
  font-size: 22px;
  color: var(--primary);
}
.guide-dialog p {
  color: var(--muted);
  line-height: 1.7;
  margin: 0 0 16px;
}
.guide-dots {
  display: flex;
  gap: 6px;
  justify-content: center;
  margin-bottom: 18px;
}
.guide-dots span {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--line);
  transition: all 0.3s;
}
.guide-dots span.active {
  background: var(--primary);
  transform: scale(1.3);
}
.guide-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}
.guide-skip, .guide-next {
  padding: 8px 20px;
  border-radius: 100px;
  font-family: var(--tag-font);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}
.guide-skip {
  background: transparent;
  border: 1.5px solid var(--line);
  color: var(--muted);
}
.guide-skip:hover {
  border-color: var(--muted);
  color: var(--text);
}
.guide-next {
  background: var(--primary);
  border: none;
  color: #fff;
}
.guide-next:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* === Responsive === */
@media (max-width: 980px) {
  .toolbar-grid,
  .stats-grid,
  .content-grid,
  .detail-grid {
    grid-template-columns: 1fr;
  }
  .hero-inner {
    flex-direction: column;
    gap: 14px;
    text-align: center;
  }
  .brand { justify-content: center; }
  .hero-actions {
    margin-left: 0;
    justify-content: center;
  }
  .detail-card { position: static; }
  .toolbar-grid {
    display: flex;
    flex-wrap: nowrap;
    padding: 0 12px;
  }
  .post-card::before { display: none; }
  .support-widget {
    width: 100%;
    margin-left: 0;
    flex-direction: row;
    justify-content: flex-end;
    gap: 10px;
  }
  .support-copy {
    text-align: right;
  }
}
</style>
