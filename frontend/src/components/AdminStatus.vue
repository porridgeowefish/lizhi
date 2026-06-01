<template>
  <div class="admin-page">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-logo" aria-hidden="true">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <path d="M145.1,102.2 Q152.0,112.0 145.1,121.8 Q148.0,133.4 138.2,139.8 Q136.8,151.6 125.6,153.6 Q119.9,163.7 109.0,161.0 Q100.0,168.0 91.0,161.0 Q80.1,163.7 74.4,153.6 Q63.2,151.6 61.8,139.8 Q52.0,133.4 54.9,121.8 Q48.0,112.0 54.9,102.2 Q52.0,90.6 61.8,84.2 Q63.2,72.4 74.4,70.4 Q80.1,60.3 91.0,63.0 Q100.0,56.0 109.0,63.0 Q119.9,60.3 125.6,70.4 Q136.8,72.4 138.2,84.2 Q148.0,90.6 145.1,102.2 Z" fill="#E53935"/>
            <g fill="#C62828" opacity="0.3">
              <circle cx="96" cy="78" r="2.5"/><circle cx="110" cy="78" r="2.5"/><circle cx="75" cy="92" r="2.5"/><circle cx="89" cy="92" r="2.5"/><circle cx="103" cy="92" r="2.5"/><circle cx="117" cy="92" r="2.5"/><circle cx="68" cy="106" r="2.5"/><circle cx="82" cy="106" r="2.5"/><circle cx="96" cy="106" r="2.5"/><circle cx="110" cy="106" r="2.5"/><circle cx="124" cy="106" r="2.5"/><circle cx="75" cy="120" r="2.5"/><circle cx="89" cy="120" r="2.5"/><circle cx="103" cy="120" r="2.5"/><circle cx="117" cy="120" r="2.5"/><circle cx="131" cy="120" r="2.5"/><circle cx="82" cy="134" r="2.5"/><circle cx="96" cy="134" r="2.5"/><circle cx="110" cy="134" r="2.5"/><circle cx="124" cy="134" r="2.5"/>
            </g>
            <path d="M100 62 C99 48 101 36 99 24" stroke="#2E7D32" stroke-width="3" fill="none" stroke-linecap="round"/>
            <path d="M99 28 C89 16 74 12 64 18 C74 22 89 26 99 28Z" fill="#43A047"/>
          </svg>
        </div>
        <div>
          <strong>荔知</strong>
          <small>后台状态看板</small>
        </div>
      </div>

      <nav class="sidebar-nav" aria-label="后台状态导航">
        <a v-for="item in navItems" :key="item.id" :href="'#' + item.id" :class="{ active: activeSection === item.id }" @click.prevent="scrollTo(item.id)">
          {{ item.label }}
        </a>
      </nav>

      <div class="sidebar-footer">
        <span class="conn-dot" :class="healthTone"></span>
        <span>{{ healthShortLabel }}</span>
      </div>
    </aside>

    <main class="main">
      <header class="page-header">
        <div>
          <h1>荔知后台状态看板</h1>
          <p>真实 API 数据，每 30 秒自动刷新</p>
        </div>
        <div class="header-meta">
          <span class="status-badge" :class="healthTone"><span class="dot"></span>{{ healthLabel }}</span>
          <span>{{ lastUpdatedLabel }}</span>
        </div>
      </header>

      <div class="content">
        <section id="overview" class="section">
          <div class="section-title">总览</div>
          <div class="kpi-row">
            <article class="card">
              <div class="card-label">总文章</div>
              <div class="card-value">{{ formatNumber(ingestion?.posts_total) }}</div>
              <p class="card-help">数据库中已入库的文章总数。</p>
            </article>
            <article class="card">
              <div class="card-label">等待处理</div>
              <div class="card-value warning">{{ formatNumber(queue?.pending) }}</div>
              <p class="card-help">队列中还没开始执行的任务。</p>
            </article>
            <article class="card">
              <div class="card-label">启用来源</div>
              <div class="card-value info">{{ formatNumber(ingestion?.sources_enabled) }}</div>
              <p class="card-help">当前会参与自动采集的公众号来源。</p>
            </article>
            <article class="card">
              <div class="card-label">支持数</div>
              <div class="card-value danger">{{ formatNumber(support?.count) }}</div>
              <p class="card-help">前台用户点击“加荔枝”的累计次数。</p>
            </article>
          </div>

          <div class="status-grid">
            <article class="card status-card">
              <h3>服务状态</h3>
              <div class="status-lines">
                <div><span>后端服务</span><strong>{{ healthLabel }}</strong></div>
                <div><span>数据库</span><strong>{{ health?.database === 'ok' ? '正常' : '异常或未知' }}</strong></div>
                <div><span>上游配置</span><strong>{{ health?.upstream_configured ? '已配置' : '未配置' }}</strong></div>
              </div>
            </article>
            <article class="card status-card">
              <h3>最近成功同步</h3>
              <div v-if="ingestion?.last_successful_sync" class="status-lines">
                <div><span>同步编号</span><strong>#{{ ingestion.last_successful_sync.id }}</strong></div>
                <div><span>完成时间</span><strong>{{ formatDateTime(ingestion.last_successful_sync.finished_at) }}</strong></div>
                <div><span>结果</span><strong>新增 {{ ingestion.last_successful_sync.posts_inserted }}，更新 {{ ingestion.last_successful_sync.posts_updated }}</strong></div>
              </div>
              <p v-else class="empty">暂无成功同步记录。</p>
            </article>
          </div>
        </section>

        <section id="queue" class="section">
          <div class="section-title">队列</div>
          <div class="card table-card">
            <table class="data-table queue-table">
              <colgroup>
                <col class="queue-status-col">
                <col class="queue-help-col">
                <col class="queue-number-col">
              </colgroup>
              <thead>
                <tr><th>状态</th><th>含义</th><th class="num">数量</th></tr>
              </thead>
              <tbody>
                <tr v-for="row in queueRows" :key="row.key">
                  <td><span class="badge" :class="row.badge">{{ row.label }}</span></td>
                  <td>{{ row.help }}</td>
                  <td class="num">{{ formatNumber(row.count) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section id="pipeline" class="section">
          <div class="section-title">处理管线</div>
          <div class="card table-card">
            <table class="data-table pipeline-table">
              <colgroup>
                <col class="pipeline-type-col">
                <col class="pipeline-number-col">
                <col class="pipeline-number-col">
                <col class="pipeline-number-col">
                <col class="pipeline-number-col">
              </colgroup>
              <thead>
                <tr>
                  <th>任务类型</th>
                  <th class="num">等待中</th>
                  <th class="num">运行中</th>
                  <th class="num">已完成</th>
                  <th class="num">异常</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in pipelineRows" :key="row.type">
                  <td>{{ jobTypeLabel(row.type) }}</td>
                  <td class="num">{{ formatNumber(row.pending) }}</td>
                  <td class="num">{{ formatNumber(row.running) }}</td>
                  <td class="num">{{ formatNumber(row.succeeded) }}</td>
                  <td class="num">{{ formatNumber(row.failed + row.dead + row.cancelled) }}</td>
                </tr>
                <tr v-if="!pipelineRows.length"><td colspan="5" class="empty">暂无任务管线数据。</td></tr>
              </tbody>
            </table>
          </div>
        </section>

        <section id="activity" class="section">
          <div class="section-title">24小时新增</div>
          <div class="card">
            <div v-if="hourlyRows.length" class="bar-chart">
              <div v-for="row in hourlyRows" :key="row.hour" class="bar-row">
                <span class="bar-label">{{ row.label }}</span>
                <div class="bar-track"><div class="bar-fill" :style="{ width: row.width + '%' }"></div></div>
                <span class="bar-count">{{ row.inserted }}</span>
              </div>
            </div>
            <p v-else class="empty">最近 24 小时没有新增文章。若上游确实有新内容，需要检查刷新来源和同步文章任务。</p>
          </div>
        </section>

        <section id="sources" class="section">
          <div class="section-title">来源</div>
          <div class="card table-card">
            <table class="data-table">
              <thead>
                <tr><th style="width: 72px;">排名</th><th>来源名称</th><th class="num">24小时新增</th></tr>
              </thead>
              <tbody>
                <tr v-for="(source, index) in topSources" :key="source.source_name">
                  <td class="rank">#{{ index + 1 }}</td>
                  <td>{{ source.source_name }}</td>
                  <td class="num">{{ formatNumber(source.inserted) }}</td>
                </tr>
                <tr v-if="!topSources.length"><td colspan="3" class="empty">最近 24 小时暂无来源新增。</td></tr>
              </tbody>
            </table>
          </div>
        </section>

        <section id="content" class="section">
          <div class="section-title">内容分布</div>
          <div class="stats-row">
            <article class="card">
              <h3>机会性质</h3>
              <div class="stat-list">
                <div v-for="item in statPairs(categories?.content_type_stats, contentTypeLabel)" :key="item.key" class="stat-item">
                  <span>
                    {{ item.label }}
                    <small>{{ contentTypeHelp(item.key) }}</small>
                  </span>
                  <strong>{{ formatNumber(item.value) }}</strong>
                </div>
                <p v-if="!statPairs(categories?.content_type_stats).length" class="empty">暂无数据</p>
              </div>
            </article>
            <article class="card">
              <h3>当前可参与性</h3>
              <div class="stat-list">
                <div v-for="item in statPairs(categories?.participation_stats, participationLabel)" :key="item.key" class="stat-item">
                  <span>
                    {{ item.label }}
                    <small>{{ participationHelp(item.key) }}</small>
                  </span>
                  <strong>{{ formatNumber(item.value) }}</strong>
                </div>
                <p v-if="!statPairs(categories?.participation_stats).length" class="empty">暂无数据</p>
              </div>
            </article>
            <article class="card">
              <h3>时间状态</h3>
              <div class="stat-list">
                <div v-for="item in statPairs(categories?.time_status_stats, timeStatusLabel)" :key="item.key" class="stat-item">
                  <span>
                    {{ item.label }}
                    <small>{{ timeStatusHelp(item.key) }}</small>
                  </span>
                  <strong>{{ formatNumber(item.value) }}</strong>
                </div>
                <p v-if="!statPairs(categories?.time_status_stats).length" class="empty">暂无数据</p>
              </div>
              <div v-if="statPairs(categories?.time_unknown_breakdown).length" class="stat-breakdown">
                <h4>未识别时间原因</h4>
                <div v-for="item in statPairs(categories?.time_unknown_breakdown, unknownTimeReasonLabel)" :key="item.key" class="stat-item compact">
                  <span>
                    {{ item.label }}
                    <small>{{ unknownTimeReasonHelp(item.key) }}</small>
                  </span>
                  <strong>{{ formatNumber(item.value) }}</strong>
                </div>
              </div>
            </article>
          </div>
        </section>

        <section id="guide" class="section">
          <div class="section-title">使用说明</div>
          <div class="guide-grid">
            <article class="card guide-card">
              <h3>怎么用</h3>
              <ol>
                <li>先看“服务状态”和“等待处理”：确认后端、数据库和队列是否正常。</li>
                <li>再看“处理管线”：判断是刷新来源、同步文章、抓取正文还是 LLM 处理卡住。</li>
                <li>最后看“24小时新增”和“来源”：确认系统有没有稳定拿到新文章，以及主要来自哪些公众号。</li>
              </ol>
            </article>
            <article class="card guide-card">
              <h3>指标含义</h3>
              <ul>
                <li><strong>总文章</strong>：数据库里已经保存的文章数量，不等于首页默认可见机会数。</li>
                <li><strong>等待中</strong>：还没被 worker 领取的任务，持续上涨说明处理速度不够。</li>
                <li><strong>运行中</strong>：worker 正在处理的任务，长期不变可能是任务卡住。</li>
                <li><strong>失败终止</strong>：重试后仍失败的任务，需要看日志或上游内容是否失效。</li>
                <li><strong>最近成功同步</strong>：最近一次成功写入同步审计的时间和新增/更新结果。</li>
              </ul>
            </article>
            <article class="card guide-card">
              <h3>监控建议</h3>
              <ul>
                <li>如果 24 小时无新增，但公众号上游有新文章，优先检查“刷新来源”和“同步文章”。</li>
                <li>如果“抓取正文”积压很多，说明正文爬取速度或上游访问稳定性需要关注。</li>
                <li>如果“LLM处理”积压很多，说明 AI 处理速度、开关或额度可能是瓶颈。</li>
                <li>公网只需要访问 <code>80 /api/*</code>；<code>8002</code> 是本机后端端口，不应公网开放。</li>
              </ul>
            </article>
          </div>
          <article class="card guide-card glossary-card">
            <h3>内容分布怎么看</h3>
            <div class="glossary-grid">
              <div>
                <h4>机会性质</h4>
                <p>回答“这篇文章本质上是不是一个机会”。<strong>明确机会</strong>通常是报名、招募、比赛、活动等；<strong>参考信息</strong>偏通知、资讯或政策，可能有用但不一定要行动；<strong>未判定</strong>表示规则暂时没有足够信息归类。</p>
              </div>
              <div>
                <h4>当前可参与性</h4>
                <p>回答“用户现在还能不能参与”。<strong>现在可参与</strong>代表报名、投递或参加条件大概率仍有效；<strong>当前不可参与</strong>通常是已过期、结果公示、回顾或纯通知；<strong>信息不足</strong>常见于摘要太短、正文缺失或时间尚未提取。</p>
              </div>
              <div>
                <h4>时间状态</h4>
                <p><strong>未识别时间</strong>表示没有提取到活动开始或截止时间，它们会按发布时间参与排序；<strong>未开始/进行中/已过期</strong>来自活动时间和截止时间的结构化提取。</p>
              </div>
            </div>
          </article>
          <article class="card guide-card architecture-card">
            <h3>文章采集、筛选与处理架构</h3>
            <div ref="mermaidEl" class="mermaid-box"></div>
          </article>
        </section>

        <section v-if="errorMessage" class="section">
          <div class="card error-card">
            <strong>加载异常</strong>
            <span>{{ errorMessage }}</span>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import mermaid from 'mermaid'
import { getHealth, getIngestionHealth, getJobSummary, getPostCategories, getSupport } from '../api.js'

const POLL_MS = 30000

const JOB_TYPE_LABELS = {
  refresh_source: '刷新来源',
  sync_source_posts: '同步文章',
  fetch_content: '抓取正文',
  llm_post: 'LLM处理',
}

const CONTENT_TYPE_LABELS = {
  actionable: '明确机会',
  reference: '参考信息',
  non_actionable: '非机会内容',
  unknown: '未判定',
  campus_activity: '校园活动',
  lecture: '讲座论坛',
  volunteer: '志愿公益',
  competition: '学科竞赛',
  recruitment: '就业招聘',
  graduate_study: '升学留学',
  exam_certification: '考试考证',
  other: '其他',
}

const PARTICIPATION_LABELS = {
  participable: '现在可参与',
  non_participable: '当前不可参与',
  uncertain: '信息不足',
  open: '现在可参与',
  restricted: '有限制',
  informational: '仅信息',
  unknown: '未知',
}

const TIME_STATUS_LABELS = {
  undated: '未识别时间',
  upcoming: '未开始',
  ongoing: '进行中',
  deadline_soon: '即将截止',
  expired: '已过期',
  unknown: '未知',
}

const CONTENT_TYPE_HELP = {
  actionable: '文章本质是一个可报名、可参加或可投递的机会',
  reference: '文章有信息价值，但不一定构成一个可参与机会',
  non_actionable: '回顾、结果、公示、介绍等不构成机会的内容',
  unknown: '规则暂时没有足够信息判断机会性质',
}

const PARTICIPATION_HELP = {
  participable: '从时间和文本看，用户当前大概率还能报名、投递或参加',
  non_participable: '已过期、不可报名，或本身只是回顾/公示/通知',
  uncertain: '正文、时间或参与条件不足，暂时无法判断当前能否参与',
}

const TIME_STATUS_HELP = {
  undated: '未提取到活动开始或截止时间',
  upcoming: '关键时间还没到',
  ongoing: '活动时间范围内',
  deadline_soon: '截止时间接近',
  expired: '活动或截止时间已过',
  unknown: '时间信息不足',
}

const UNKNOWN_TIME_REASON_LABELS = {
  content_missing: '正文缺失',
  llm_waiting: '等待 LLM',
  llm_failed: 'LLM 失败',
  processed_no_time: '已处理但无时间',
  other: '其他原因',
}

const UNKNOWN_TIME_REASON_HELP = {
  content_missing: '正文还没抓到或抓取失败，时间通常藏在正文里',
  llm_waiting: '正文已准备好，但还没完成结构化时间提取',
  llm_failed: 'LLM 处理重试后失败，需要看失败任务或日志',
  processed_no_time: '已经处理过，但正文里没有明确活动开始或截止时间',
  other: '状态不在常规分类中，需要进一步排查',
}

const PIPELINE_MERMAID = `flowchart LR
  Timer["定时器<br/>systemd timer"] --> Enqueue["入队器<br/>enqueue_refresh_jobs"]
  Enqueue --> Queue[("job_queue<br/>数据库队列")]
  Queue --> Refresh["refresh_worker<br/>刷新来源 / 同步文章"]
  Refresh --> Upstream["WeRSS / 公众号源"]
  Upstream --> Prescreen["规则初筛<br/>过滤广告、回顾、乱码"]
  Prescreen -->|通过| Store["入库<br/>posts / projections"]
  Prescreen -->|过滤| Discard["丢弃记录<br/>discarded_posts"]
  Store -->|缺正文| Queue
  Queue --> Content["content_worker<br/>抓取正文"]
  Content --> Store
  Store -->|需要结构化| Queue
  Queue --> LLM["llm_worker<br/>标题、摘要、分类、时间"]
  LLM --> Projection["更新投影<br/>机会性质 / 当前可参与性 / 时间状态"]
  Projection --> API["/api/posts<br/>/api/jobs/ingestion-health"]
  API --> Dashboard["后台看板 / 前台机会列表"]`

export default {
  name: 'AdminStatus',
  setup() {
    const health = ref(null)
    const queue = ref(null)
    const ingestion = ref(null)
    const categories = ref(null)
    const support = ref(null)
    const errorMessage = ref('')
    const lastUpdated = ref(null)
    const activeSection = ref('overview')
    const mermaidEl = ref(null)
    let pollTimer = null
    let observer = null

    const navItems = [
      { id: 'overview', label: '总览' },
      { id: 'queue', label: '队列' },
      { id: 'pipeline', label: '处理管线' },
      { id: 'activity', label: '24小时新增' },
      { id: 'sources', label: '来源' },
      { id: 'content', label: '内容分布' },
      { id: 'guide', label: '使用说明' },
    ]

    const healthTone = computed(() => {
      if (!health.value) return 'warn'
      if (health.value.status === 'ok') return 'ok'
      if (health.value.status === 'degraded') return 'warn'
      return 'bad'
    })
    const healthLabel = computed(() => {
      if (!health.value) return '加载中'
      if (health.value.status === 'ok') return '运行正常'
      if (health.value.status === 'degraded') return '部分降级'
      return '异常'
    })
    const healthShortLabel = computed(() => {
      if (!health.value) return '连接中'
      return `数据库：${health.value.database === 'ok' ? '正常' : '异常'}`
    })
    const lastUpdatedLabel = computed(() => {
      if (!lastUpdated.value) return '尚未刷新'
      return `更新 ${lastUpdated.value.toLocaleTimeString('zh-CN', { hour12: false })}`
    })

    const queueRows = computed(() => [
      { key: 'pending', label: '等待中', help: '已入队但尚未被 worker 领取', count: queue.value?.pending || 0, badge: 'badge-amber' },
      { key: 'running', label: '运行中', help: 'worker 正在处理', count: queue.value?.running || 0, badge: 'badge-blue' },
      { key: 'succeeded', label: '已完成', help: '处理成功并已记录结果', count: queue.value?.succeeded || 0, badge: 'badge-green' },
      { key: 'failed', label: '失败待重试', help: '失败但还没达到最大重试次数', count: queue.value?.failed || 0, badge: 'badge-red' },
      { key: 'dead', label: '失败终止', help: '达到最大重试次数后停止', count: queue.value?.dead || 0, badge: 'badge-gray' },
      { key: 'cancelled', label: '已取消', help: '被治理逻辑取消或跳过', count: queue.value?.cancelled || 0, badge: 'badge-gray' },
    ])

    const pipelineRows = computed(() => {
      const rows = {}
      for (const item of ingestion.value?.queue_by_type_status || []) {
        const type = item.job_type || 'unknown'
        const status = item.status || 'pending'
        if (!rows[type]) rows[type] = { type, pending: 0, running: 0, succeeded: 0, failed: 0, dead: 0, cancelled: 0 }
        if (Object.prototype.hasOwnProperty.call(rows[type], status)) rows[type][status] += Number(item.count || 0)
      }
      return Object.values(rows).sort((a, b) => jobTypeLabel(a.type).localeCompare(jobTypeLabel(b.type), 'zh-CN'))
    })

    const hourlyRows = computed(() => {
      const rows = ingestion.value?.posts_inserted_by_hour_24h || []
      const max = Math.max(1, ...rows.map((row) => Number(row.inserted || 0)))
      return rows.map((row) => {
        const raw = String(row.hour || '')
        const label = raw.includes('T') ? raw.split('T')[1].slice(0, 5) : raw.slice(-5)
        const inserted = Number(row.inserted || 0)
        return { hour: row.hour, label, inserted, width: Math.max(2, Math.round((inserted / max) * 100)) }
      })
    })

    const topSources = computed(() => (ingestion.value?.top_sources_inserted_24h || []).slice(0, 10))

    async function loadAll() {
      const results = await Promise.allSettled([
        getHealth(),
        getJobSummary(),
        getIngestionHealth(),
        getPostCategories(),
        getSupport('admin-status-board'),
      ])
      const [healthResult, queueResult, ingestionResult, categoriesResult, supportResult] = results
      if (healthResult.status === 'fulfilled') health.value = healthResult.value
      if (queueResult.status === 'fulfilled') queue.value = queueResult.value
      if (ingestionResult.status === 'fulfilled') ingestion.value = ingestionResult.value
      if (categoriesResult.status === 'fulfilled') categories.value = categoriesResult.value
      if (supportResult.status === 'fulfilled') support.value = supportResult.value
      const rejected = results.find((result) => result.status === 'rejected')
      errorMessage.value = rejected ? (rejected.reason?.response?.data?.detail || rejected.reason?.message || '部分接口加载失败') : ''
      lastUpdated.value = new Date()
    }

    function scrollTo(id) {
      document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      activeSection.value = id
    }
    function initScrollSpy() {
      observer = new IntersectionObserver((entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) activeSection.value = entry.target.id
        }
      }, { rootMargin: '-90px 0px -65% 0px', threshold: 0 })
      for (const item of navItems) {
        const element = document.getElementById(item.id)
        if (element) observer.observe(element)
      }
    }
    function formatNumber(value) {
      const number = Number(value || 0)
      return Number.isFinite(number) ? number.toLocaleString('zh-CN') : '0'
    }
    function formatDateTime(value) {
      if (!value) return '暂无'
      const date = new Date(value)
      return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString('zh-CN', { hour12: false })
    }
    function statPairs(obj, labeler = (value) => value) {
      return Object.entries(obj || {})
        .sort((a, b) => Number(b[1] || 0) - Number(a[1] || 0))
        .map(([key, value]) => ({ key, label: labeler(key), value }))
    }
    function jobTypeLabel(value) { return JOB_TYPE_LABELS[value] || String(value || '未知任务') }
    function contentTypeLabel(value) { return CONTENT_TYPE_LABELS[value] || String(value || '未知') }
    function participationLabel(value) { return PARTICIPATION_LABELS[value] || String(value || '未知') }
    function timeStatusLabel(value) { return TIME_STATUS_LABELS[value] || String(value || '未知') }
    function unknownTimeReasonLabel(value) { return UNKNOWN_TIME_REASON_LABELS[value] || String(value || '未知原因') }
    function contentTypeHelp(value) { return CONTENT_TYPE_HELP[value] || '保留后端原始分类值' }
    function participationHelp(value) { return PARTICIPATION_HELP[value] || '保留后端原始参与状态' }
    function timeStatusHelp(value) { return TIME_STATUS_HELP[value] || '保留后端原始时间状态' }
    function unknownTimeReasonHelp(value) { return UNKNOWN_TIME_REASON_HELP[value] || '保留后端原始原因' }
    async function renderMermaid() {
      if (!mermaidEl.value) return
      try {
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: 'strict',
          theme: 'base',
          themeVariables: {
            fontFamily: 'PingFang SC, Microsoft YaHei, sans-serif',
            primaryColor: '#eff6ff',
            primaryTextColor: '#111827',
            primaryBorderColor: '#93c5fd',
            lineColor: '#64748b',
            secondaryColor: '#ecfdf5',
            tertiaryColor: '#fff7ed',
          },
        })
        const { svg } = await mermaid.render(`admin-pipeline-${Date.now()}`, PIPELINE_MERMAID)
        mermaidEl.value.innerHTML = svg
      } catch (error) {
        mermaidEl.value.innerHTML = '<p class="empty">架构图渲染失败，请刷新页面重试。</p>'
      }
    }

    onMounted(() => {
      loadAll()
      initScrollSpy()
      nextTick(renderMermaid)
      pollTimer = window.setInterval(loadAll, POLL_MS)
    })
    onUnmounted(() => {
      if (pollTimer) window.clearInterval(pollTimer)
      if (observer) observer.disconnect()
    })

    return {
      navItems,
      activeSection,
      health,
      queue,
      ingestion,
      categories,
      support,
      errorMessage,
      mermaidEl,
      healthTone,
      healthLabel,
      healthShortLabel,
      lastUpdatedLabel,
      queueRows,
      pipelineRows,
      hourlyRows,
      topSources,
      scrollTo,
      formatNumber,
      formatDateTime,
      statPairs,
      jobTypeLabel,
      contentTypeLabel,
      participationLabel,
      timeStatusLabel,
      unknownTimeReasonLabel,
      contentTypeHelp,
      participationHelp,
      timeStatusHelp,
      unknownTimeReasonHelp,
    }
  },
}
</script>

<style scoped>
* { box-sizing: border-box; }

.admin-page {
  min-height: 100vh;
  background: #f9fafb;
  color: #111827;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 100;
  width: 216px;
  display: flex;
  flex-direction: column;
  background: #1f2937;
  color: #fff;
  overflow-y: auto;
}

.sidebar-brand {
  min-height: 76px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid #374151;
}

.brand-logo {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  background: #111827;
  border: 1px solid #374151;
  flex: 0 0 auto;
}

.brand-logo svg { width: 34px; height: 34px; }
.sidebar-brand strong { display: block; font-size: 17px; line-height: 1.1; }
.sidebar-brand small { display: block; margin-top: 3px; color: #9ca3af; font-size: 12px; }

.sidebar-nav {
  flex: 1;
  padding: 8px 0;
}

.sidebar-nav a {
  display: block;
  min-height: 38px;
  padding: 10px 16px;
  border-left: 3px solid transparent;
  color: #d1d5db;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
}

.sidebar-nav a:hover {
  background: #374151;
  color: #fff;
}

.sidebar-nav a.active {
  background: #111827;
  color: #fff;
  border-left-color: #3b82f6;
}

.sidebar-footer {
  padding: 14px 16px;
  border-top: 1px solid #374151;
  color: #d1d5db;
  font-size: 12px;
}

.conn-dot,
.dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  margin-right: 6px;
  background: #f59e0b;
  vertical-align: middle;
}

.conn-dot.ok,
.dot.ok,
.status-badge.ok .dot { background: #10b981; }
.conn-dot.bad,
.dot.bad,
.status-badge.bad .dot { background: #ef4444; }

.main {
  margin-left: 216px;
  min-height: 100vh;
}

.page-header {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;
  background: #fff;
}

.page-header h1 {
  margin: 0;
  font-size: 20px;
  line-height: 1.25;
}

.page-header p {
  margin: 4px 0 0;
  color: #6b7280;
  font-size: 13px;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #6b7280;
  font-size: 12px;
  white-space: nowrap;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid #fde68a;
  background: #fffbeb;
  color: #b45309;
  font-weight: 700;
}

.status-badge.ok {
  border-color: #a7f3d0;
  background: #ecfdf5;
  color: #047857;
}

.status-badge.bad {
  border-color: #fecaca;
  background: #fef2f2;
  color: #dc2626;
}

.content {
  padding: 24px;
}

.section {
  scroll-margin-top: 86px;
  margin-bottom: 26px;
}

.section-title {
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
  color: #6b7280;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.05em;
}

.card {
  background: #fff;
  border: 1px solid #e5e7eb;
  padding: 16px;
}

.card h3 {
  margin: 0 0 12px;
  font-size: 15px;
}

.card-label {
  margin-bottom: 8px;
  color: #9ca3af;
  font-size: 12px;
  font-weight: 800;
}

.card-value {
  color: #111827;
  font-size: 30px;
  font-weight: 800;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.card-value.warning { color: #d97706; }
.card-value.danger { color: #dc2626; }
.card-value.info { color: #2563eb; }
.card-help {
  margin: 10px 0 0;
  color: #6b7280;
  font-size: 12px;
  line-height: 1.5;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.status-grid,
.stats-row,
.guide-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.stats-row,
.guide-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 0;
}

.status-lines {
  display: grid;
  gap: 10px;
}

.status-lines div,
.stat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.status-lines span,
.stat-item span {
  color: #6b7280;
}

.status-lines strong,
.stat-item strong {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.table-card {
  padding: 0;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 13px;
}

.data-table th {
  padding: 9px 12px;
  border-bottom: 1px solid #e5e7eb;
  border-left: 1px solid #e5e7eb;
  background: #f9fafb;
  color: #6b7280;
  text-align: left;
  font-size: 12px;
  font-weight: 800;
}

.data-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
  border-left: 1px solid #f3f4f6;
  color: #374151;
}

.data-table th:first-child,
.data-table td:first-child {
  border-left: 0;
}

.queue-status-col {
  width: 18%;
}

.queue-help-col {
  width: 64%;
}

.queue-number-col {
  width: 18%;
}

.pipeline-type-col {
  width: 26%;
}

.pipeline-number-col {
  width: 18.5%;
}

.data-table tr:last-child td {
  border-bottom: 0;
}

.num {
  text-align: center;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}

.badge {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 0 8px;
  font-size: 12px;
  font-weight: 800;
}

.badge-amber { background: #fef3c7; color: #92400e; }
.badge-blue { background: #dbeafe; color: #1d4ed8; }
.badge-green { background: #d1fae5; color: #047857; }
.badge-red { background: #fee2e2; color: #b91c1c; }
.badge-gray { background: #f3f4f6; color: #4b5563; }

.bar-chart {
  display: grid;
  gap: 9px;
}

.bar-row {
  display: grid;
  grid-template-columns: 52px 1fr 52px;
  align-items: center;
  gap: 10px;
}

.bar-label,
.bar-count {
  color: #6b7280;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.bar-count {
  text-align: right;
  font-weight: 700;
}

.bar-track {
  height: 12px;
  background: #e5e7eb;
}

.bar-fill {
  height: 100%;
  background: #2563eb;
}

.rank {
  color: #1d4ed8;
  font-weight: 800;
}

.stat-list {
  display: grid;
  gap: 9px;
}

.stat-item {
  align-items: flex-start;
}

.stat-item span {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 2px;
}

.stat-item small {
  color: #9ca3af;
  font-size: 12px;
  line-height: 1.45;
}

.stat-breakdown {
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.stat-breakdown h4 {
  margin: 0 0 12px;
  color: #111827;
  font-size: 14px;
}

.stat-item.compact {
  padding: 7px 0;
}

.guide-card ol,
.guide-card ul {
  margin: 0;
  padding-left: 20px;
  color: #374151;
  font-size: 13px;
  line-height: 1.75;
}

.guide-card code {
  color: #1d4ed8;
  font-family: Consolas, "Courier New", monospace;
}

.glossary-card,
.architecture-card {
  margin-top: 16px;
}

.glossary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.glossary-grid h4 {
  margin: 0 0 8px;
  color: #111827;
  font-size: 14px;
}

.glossary-grid p {
  margin: 0;
  color: #4b5563;
  font-size: 13px;
  line-height: 1.75;
}

.mermaid-box {
  width: 100%;
  min-height: 360px;
  overflow-x: auto;
  padding: 12px;
  border: 1px solid #e5e7eb;
  background: #fbfdff;
}

.mermaid-box :deep(svg) {
  display: block;
  max-width: none;
  min-width: 980px;
  margin: 0 auto;
}

.empty {
  color: #9ca3af;
  font-size: 13px;
}

.error-card {
  display: flex;
  gap: 10px;
  border-color: #fecaca;
  background: #fef2f2;
  color: #991b1b;
}

@media (max-width: 1040px) {
  .kpi-row,
  .stats-row,
  .guide-grid,
  .glossary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .sidebar {
    position: static;
    width: 100%;
    height: auto;
  }

  .sidebar-nav {
    display: flex;
    overflow-x: auto;
    padding: 0;
  }

  .sidebar-nav a {
    flex: 0 0 auto;
    border-left: 0;
    border-bottom: 3px solid transparent;
  }

  .sidebar-nav a.active {
    border-left: 0;
    border-bottom-color: #3b82f6;
  }

  .sidebar-footer {
    display: none;
  }

  .main {
    margin-left: 0;
  }

  .page-header {
    position: static;
    align-items: flex-start;
    flex-direction: column;
  }

  .header-meta {
    white-space: normal;
    flex-wrap: wrap;
  }

  .content {
    padding: 16px;
  }

  .kpi-row,
  .status-grid,
  .stats-row,
  .guide-grid,
  .glossary-grid {
    grid-template-columns: 1fr;
  }

  .table-card {
    overflow-x: auto;
  }

  .data-table {
    min-width: 560px;
  }
}
</style>
