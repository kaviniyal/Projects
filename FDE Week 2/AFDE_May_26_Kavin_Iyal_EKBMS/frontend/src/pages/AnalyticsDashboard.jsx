/**
 * AnalyticsDashboard — Phase 2
 * Full reporting dashboard: category trends, author activity,
 * search keywords, monthly publication, top tags, and ETL pipeline
 * management (Admin only).
 */

import { useEffect, useState, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import { analyticsService, etlService } from '../services/apiService'

// ─── colour palette for bar charts (inline SVG) ─────────────────────────────
const COLOURS = [
  '#4f46e5', '#059669', '#d97706', '#dc2626', '#0284c7',
  '#7c3aed', '#db2777', '#0891b2', '#65a30d', '#ea580c',
]

// ─── tiny helpers ─────────────────────────────────────────────────────────────
function pct(value, max) {
  return max === 0 ? 0 : Math.round((value / max) * 100)
}

function num(v) {
  return typeof v === 'number' ? v.toLocaleString() : v ?? 0
}

function StatCard({ label, value, icon, colour = 'primary', sub }) {
  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <span className="stat-card-label">{label}</span>
        <div className={`stat-card-icon ${colour}`}>{icon}</div>
      </div>
      <div className="stat-card-value">{num(value)}</div>
      {sub && <div className="text-xs text-muted" style={{ marginTop: 4 }}>{sub}</div>}
    </div>
  )
}

// ─── Inline horizontal bar chart (no external charting library needed) ────────
function HBarChart({ data, labelKey, valueKey, colour = '#4f46e5', limit = 10 }) {
  const rows = (data ?? []).slice(0, limit)
  const max = Math.max(...rows.map(r => r[valueKey] ?? 0), 1)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {rows.map((row, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 160, fontSize: 13, color: 'var(--color-gray-700)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {row[labelKey]}
          </div>
          <div style={{ flex: 1, background: 'var(--color-gray-100)', borderRadius: 4, height: 18, position: 'relative' }}>
            <div style={{
              width: `${pct(row[valueKey] ?? 0, max)}%`,
              background: colour,
              height: '100%',
              borderRadius: 4,
              minWidth: 4,
              transition: 'width 0.4s ease',
            }} />
          </div>
          <div style={{ width: 50, fontSize: 12, color: 'var(--color-gray-600)', textAlign: 'right' }}>
            {num(row[valueKey])}
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── Monthly timeline chart ───────────────────────────────────────────────────
function MonthlyChart({ data }) {
  if (!data || data.length === 0) return <div className="text-muted text-sm">No publication data yet.</div>
  const max = Math.max(...data.map(d => d.article_count), 1)
  return (
    <div style={{ display: 'flex', gap: 6, alignItems: 'flex-end', height: 120, overflowX: 'auto', paddingBottom: 4 }}>
      {data.map((d, i) => (
        <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, minWidth: 40 }}>
          <div style={{ fontSize: 11, color: 'var(--color-gray-600)' }}>{d.article_count}</div>
          <div style={{
            width: 28,
            height: `${pct(d.article_count, max) * 0.9 + 10}%`,
            background: COLOURS[i % COLOURS.length],
            borderRadius: '4px 4px 0 0',
          }} />
          <div style={{ fontSize: 10, color: 'var(--color-gray-400)', writingMode: 'vertical-rl', transform: 'rotate(180deg)', height: 36 }}>
            {d.year_month}
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── ETL Status Badge ─────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const colours = {
    completed: 'var(--color-success)',
    completed_with_errors: 'var(--color-warning)',
    running: 'var(--color-info)',
    queued: 'var(--color-info)',
    failed: 'var(--color-danger)',
    never_run: 'var(--color-gray-400)',
  }
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 10px',
      borderRadius: 12,
      fontSize: 12,
      fontWeight: 600,
      color: '#fff',
      background: colours[status] ?? 'var(--color-gray-500)',
    }}>
      {status?.replace(/_/g, ' ') ?? 'unknown'}
    </span>
  )
}


// ─── Main Component ────────────────────────────────────────────────────────────
export default function AnalyticsDashboard() {
  const { user } = useAuth()
  const isAdmin = user?.role_name === 'Admin'

  const [analytics, setAnalytics] = useState(null)
  const [etlSummary, setEtlSummary] = useState(null)
  const [etlJobs, setEtlJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [etlRunning, setEtlRunning] = useState(false)
  const [etlMsg, setEtlMsg] = useState('')
  const [activeTab, setActiveTab] = useState('overview')

  const load = useCallback(async () => {
    try {
      const [analyticsData, etlSummaryData] = await Promise.all([
        analyticsService.full(),
        analyticsService.etlSummary(),
      ])
      setAnalytics(analyticsData)
      setEtlSummary(etlSummaryData)

      if (isAdmin) {
        const jobs = await etlService.listJobs(10)
        setEtlJobs(jobs)
      }
    } catch (err) {
      setError('Failed to load analytics data.')
    } finally {
      setLoading(false)
    }
  }, [isAdmin])

  useEffect(() => { load() }, [load])

  const runETL = async () => {
    setEtlRunning(true)
    setEtlMsg('')
    try {
      const result = await etlService.run()
      setEtlMsg(`✓ ${result.message}`)
      // Refresh after 3 s to pick up progress
      setTimeout(load, 3000)
    } catch (err) {
      setEtlMsg(`✗ ${err.response?.data?.detail ?? 'ETL trigger failed.'}`)
    } finally {
      setEtlRunning(false)
    }
  }

  const regenerateReports = async () => {
    try {
      setEtlMsg('Generating CSV reports…')
      await etlService.generateReports()
      setEtlMsg('✓ Reports generated in datasets/reports/')
    } catch (err) {
      setEtlMsg(`✗ ${err.response?.data?.detail ?? 'Report generation failed.'}`)
    }
  }

  if (loading) return <div className="loading">Loading analytics…</div>
  if (error) return <div className="alert alert-error">{error}</div>

  const a = analytics ?? {}

  // Summary stats
  const totalViews = (a.category_trends ?? []).reduce((sum, c) => sum + (c.total_views ?? 0), 0)
  const totalArticles = (a.by_category ?? []).reduce((sum, c) => sum + (c.article_count ?? 0), 0)
  const topCategory = [...(a.category_trends ?? [])].sort((x, y) => y.total_views - x.total_views)[0]

  const TABS = [
    { id: 'overview', label: '📊 Overview' },
    { id: 'categories', label: '🗂️ Categories' },
    { id: 'authors', label: '✍️ Authors' },
    { id: 'keywords', label: '🔍 Keywords' },
    { id: 'tags', label: '🏷️ Tags' },
    ...(isAdmin ? [{ id: 'etl', label: '⚙️ ETL Pipeline' }] : []),
  ]

  return (
    <div>
      {/* ── Page header ── */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Analytics Dashboard</h1>
          <p className="page-subtitle">Knowledge base insights and ETL pipeline management</p>
        </div>
        {isAdmin && (
          <button
            className="btn btn-primary"
            onClick={runETL}
            disabled={etlRunning}
          >
            {etlRunning ? '⏳ Running ETL…' : '▶ Run ETL Pipeline'}
          </button>
        )}
      </div>

      {etlMsg && (
        <div className={`alert ${etlMsg.startsWith('✓') ? 'alert-success' : 'alert-error'}`} style={{ marginBottom: 16 }}>
          {etlMsg}
        </div>
      )}

      {/* ── Summary stat cards ── */}
      <div className="stats-grid" style={{ marginBottom: 24 }}>
        <StatCard label="Total Articles" value={totalArticles} icon="📚" colour="primary" />
        <StatCard label="Total Views" value={totalViews} icon="👁" colour="info" />
        <StatCard label="Approved" value={(a.by_category ?? []).length > 0 ? (a.most_viewed?.length ?? 0) : 0} icon="✓" colour="success"
          sub="articles with views"
        />
        <StatCard label="Search Queries" value={(a.search_keywords ?? []).reduce((s, k) => s + k.search_count, 0)} icon="🔍" colour="warning" />
        <StatCard label="Active Authors" value={(a.author_activity ?? []).length} icon="✍️" colour="primary" />
        <StatCard
          label="Top Category"
          value={topCategory?.category_name ?? '—'}
          icon="🏆"
          colour="success"
          sub={topCategory ? `${num(topCategory.total_views)} views` : ''}
        />
      </div>

      {/* ── Tab navigation ── */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, borderBottom: '2px solid var(--color-gray-200)', paddingBottom: 0 }}>
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            style={{
              padding: '8px 16px',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontWeight: activeTab === t.id ? 700 : 400,
              color: activeTab === t.id ? 'var(--color-primary)' : 'var(--color-gray-600)',
              borderBottom: activeTab === t.id ? '2px solid var(--color-primary)' : '2px solid transparent',
              marginBottom: -2,
              fontSize: 14,
              whiteSpace: 'nowrap',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ════════════════════════════════════════════════════════
          OVERVIEW TAB
         ════════════════════════════════════════════════════════ */}
      {activeTab === 'overview' && (
        <div>
          <div className="col-2 mb-4">
            {/* Most viewed */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">🔥 Most Viewed Articles</h2>
              </div>
              {(a.most_viewed ?? []).length === 0 ? (
                <div className="text-muted text-sm">No views recorded yet.</div>
              ) : (
                <ol style={{ listStyle: 'none' }}>
                  {(a.most_viewed ?? []).slice(0, 8).map((art, i) => (
                    <li key={art.article_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--color-gray-100)' }}>
                      <span><strong style={{ color: 'var(--color-gray-400)' }}>{i + 1}.</strong> {art.title}</span>
                      <span className="text-xs text-muted">{num(art.view_count)} views</span>
                    </li>
                  ))}
                </ol>
              )}
            </div>

            {/* Monthly publication */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">📅 Monthly Publication Trend</h2>
                <span className="text-sm text-muted">Last 12 months</span>
              </div>
              <MonthlyChart data={a.monthly_publication ?? []} />
            </div>
          </div>

          {/* Status breakdown */}
          <div className="card mb-4">
            <div className="card-header">
              <h2 className="card-title">📋 Articles by Status</h2>
            </div>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {[
                { label: 'Approved', key: 'approved_articles', colour: 'success' },
                { label: 'Pending', key: 'pending_articles', colour: 'warning' },
                { label: 'Draft', key: 'draft_articles', colour: 'info' },
                { label: 'Rejected', key: 'rejected_articles', colour: 'danger' },
                { label: 'Archived', key: 'archived_articles', colour: 'primary' },
              ].map(s => (
                <div key={s.key} className="stat-card" style={{ flex: '1 1 120px', minWidth: 120 }}>
                  <div className="stat-card-label">{s.label}</div>
                  <div className="stat-card-value" style={{ fontSize: '1.5rem' }}>
                    {num(a[s.key] ?? (a.by_category ?? []).length)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════
          CATEGORIES TAB
         ════════════════════════════════════════════════════════ */}
      {activeTab === 'categories' && (
        <div className="col-2 mb-4">
          <div className="card">
            <div className="card-header"><h2 className="card-title">📄 Articles per Category</h2></div>
            <HBarChart
              data={a.category_trends ?? []}
              labelKey="category_name"
              valueKey="article_count"
              colour="#4f46e5"
            />
          </div>
          <div className="card">
            <div className="card-header"><h2 className="card-title">👁 Views per Category</h2></div>
            <HBarChart
              data={a.category_trends ?? []}
              labelKey="category_name"
              valueKey="total_views"
              colour="#059669"
            />
          </div>
          {/* Detail table */}
          <div className="card" style={{ gridColumn: '1 / -1' }}>
            <div className="card-header"><h2 className="card-title">Category Details</h2></div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--color-gray-200)' }}>
                  <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 600 }}>Category</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 600 }}>Articles</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 600 }}>Total Views</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 600 }}>Avg Views/Article</th>
                </tr>
              </thead>
              <tbody>
                {(a.category_trends ?? []).map((c, i) => (
                  <tr key={c.category_id} style={{ borderBottom: '1px solid var(--color-gray-100)', background: i % 2 === 0 ? 'transparent' : 'var(--color-gray-50)' }}>
                    <td style={{ padding: '8px 12px', fontWeight: 500 }}>{c.category_name}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'right' }}>{num(c.article_count)}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'right' }}>{num(c.total_views)}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'right' }}>{c.avg_views_per_article ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════
          AUTHORS TAB
         ════════════════════════════════════════════════════════ */}
      {activeTab === 'authors' && (
        <div>
          <div className="col-2 mb-4">
            <div className="card">
              <div className="card-header"><h2 className="card-title">📝 Articles per Author</h2></div>
              <HBarChart
                data={a.author_activity ?? []}
                labelKey="author_name"
                valueKey="article_count"
                colour="#7c3aed"
              />
            </div>
            <div className="card">
              <div className="card-header"><h2 className="card-title">👁 Views per Author</h2></div>
              <HBarChart
                data={a.author_activity ?? []}
                labelKey="author_name"
                valueKey="total_views"
                colour="#0284c7"
              />
            </div>
          </div>
          <div className="card">
            <div className="card-header"><h2 className="card-title">Author Activity Report</h2></div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--color-gray-200)' }}>
                  <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 600 }}>Author</th>
                  <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 600 }}>Department</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 600 }}>Articles</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 600 }}>Total Views</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 600 }}>Avg Rating</th>
                </tr>
              </thead>
              <tbody>
                {(a.author_activity ?? []).map((au, i) => (
                  <tr key={au.user_id} style={{ borderBottom: '1px solid var(--color-gray-100)', background: i % 2 === 0 ? 'transparent' : 'var(--color-gray-50)' }}>
                    <td style={{ padding: '8px 12px', fontWeight: 500 }}>{au.author_name}</td>
                    <td style={{ padding: '8px 12px', color: 'var(--color-gray-500)' }}>{au.department ?? '—'}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'right' }}>{num(au.article_count)}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'right' }}>{num(au.total_views)}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                      {au.avg_rating != null ? (
                        <span>{'⭐'.repeat(Math.round(au.avg_rating))} {au.avg_rating.toFixed(1)}</span>
                      ) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════
          KEYWORDS TAB
         ════════════════════════════════════════════════════════ */}
      {activeTab === 'keywords' && (
        <div className="col-2 mb-4">
          <div className="card">
            <div className="card-header"><h2 className="card-title">🔍 Top Search Keywords</h2></div>
            {(a.search_keywords ?? []).length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">🔍</div>
                <div className="text-muted">No searches recorded yet. Try using the Search page.</div>
              </div>
            ) : (
              <HBarChart
                data={a.search_keywords ?? []}
                labelKey="keyword"
                valueKey="search_count"
                colour="#dc2626"
              />
            )}
          </div>
          <div className="card">
            <div className="card-header"><h2 className="card-title">Keyword Frequency Table</h2></div>
            {(a.search_keywords ?? []).length === 0 ? (
              <div className="text-muted text-sm">No search data available.</div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--color-gray-200)' }}>
                    <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 600 }}>Rank</th>
                    <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 600 }}>Keyword</th>
                    <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 600 }}>Searches</th>
                  </tr>
                </thead>
                <tbody>
                  {(a.search_keywords ?? []).map((kw, i) => (
                    <tr key={kw.keyword} style={{ borderBottom: '1px solid var(--color-gray-100)' }}>
                      <td style={{ padding: '8px 12px', color: 'var(--color-gray-400)' }}>#{i + 1}</td>
                      <td style={{ padding: '8px 12px', fontWeight: 500 }}>
                        <span style={{ background: 'var(--color-primary-light)', color: 'var(--color-primary)', padding: '2px 8px', borderRadius: 12, fontSize: 12 }}>
                          {kw.keyword}
                        </span>
                      </td>
                      <td style={{ padding: '8px 12px', textAlign: 'right' }}>{num(kw.search_count)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════
          TAGS TAB
         ════════════════════════════════════════════════════════ */}
      {activeTab === 'tags' && (
        <div className="col-2 mb-4">
          <div className="card">
            <div className="card-header"><h2 className="card-title">🏷️ Top Tags by Usage</h2></div>
            <HBarChart
              data={a.top_tags ?? []}
              labelKey="tag_name"
              valueKey="usage_count"
              colour="#0891b2"
              limit={20}
            />
          </div>
          <div className="card">
            <div className="card-header"><h2 className="card-title">Tag Cloud</h2></div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {(a.top_tags ?? []).slice(0, 40).map((t, i) => {
                const maxCount = (a.top_tags?.[0]?.usage_count ?? 1)
                const size = 11 + Math.round((t.usage_count / maxCount) * 14)
                return (
                  <span key={t.tag_name} style={{
                    fontSize: size,
                    color: COLOURS[i % COLOURS.length],
                    background: 'var(--color-gray-50)',
                    border: `1px solid ${COLOURS[i % COLOURS.length]}30`,
                    padding: '3px 10px',
                    borderRadius: 12,
                    cursor: 'default',
                  }}>
                    {t.tag_name} ({t.usage_count})
                  </span>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════
          ETL PIPELINE TAB  (Admin only)
         ════════════════════════════════════════════════════════ */}
      {activeTab === 'etl' && isAdmin && (
        <div>
          {/* ETL controls */}
          <div className="card mb-4">
            <div className="card-header">
              <h2 className="card-title">⚙️ ETL Pipeline Controls</h2>
            </div>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
              <button className="btn btn-primary" onClick={runETL} disabled={etlRunning}>
                {etlRunning ? '⏳ Running…' : '▶ Run Full ETL Pipeline'}
              </button>
              <button className="btn btn-secondary" onClick={regenerateReports} disabled={etlRunning}>
                📥 Re-generate CSV Reports
              </button>
              <button className="btn btn-secondary" onClick={load}>
                🔄 Refresh Status
              </button>
            </div>
            {etlMsg && (
              <div className={`alert ${etlMsg.startsWith('✓') ? 'alert-success' : 'alert-error'}`}>
                {etlMsg}
              </div>
            )}

            {/* ETL summary */}
            {etlSummary && (
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 16 }}>
                <div><span className="text-muted text-sm">Status: </span><StatusBadge status={etlSummary.status} /></div>
                {etlSummary.last_run && <div className="text-sm"><span className="text-muted">Last run: </span>{new Date(etlSummary.last_run).toLocaleString()}</div>}
                {etlSummary.rows_inserted !== undefined && <div className="text-sm"><span className="text-muted">Inserted: </span><strong>{etlSummary.rows_inserted}</strong></div>}
                {etlSummary.rows_updated !== undefined && <div className="text-sm"><span className="text-muted">Updated: </span><strong>{etlSummary.rows_updated}</strong></div>}
                {etlSummary.rows_errored !== undefined && <div className="text-sm"><span className="text-muted">Errors: </span><strong style={{ color: etlSummary.rows_errored > 0 ? 'var(--color-danger)' : 'inherit' }}>{etlSummary.rows_errored}</strong></div>}
              </div>
            )}
          </div>

          {/* ETL job history */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">📋 ETL Job History</h2>
              <span className="text-sm text-muted">Last 10 runs</span>
            </div>
            {etlJobs.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">🔄</div>
                <div className="text-muted">No ETL jobs have been run yet. Click "Run Full ETL Pipeline" to get started.</div>
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--color-gray-200)' }}>
                    <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 600 }}>Job #</th>
                    <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 600 }}>Status</th>
                    <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 600 }}>Started</th>
                    <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 600 }}>Finished</th>
                    <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 600 }}>Inserted</th>
                    <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 600 }}>Updated</th>
                    <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 600 }}>Errors</th>
                  </tr>
                </thead>
                <tbody>
                  {etlJobs.map((job, i) => (
                    <tr key={job.job_id} style={{ borderBottom: '1px solid var(--color-gray-100)', background: i % 2 === 0 ? 'transparent' : 'var(--color-gray-50)' }}>
                      <td style={{ padding: '8px 12px', color: 'var(--color-gray-400)' }}>#{job.job_id}</td>
                      <td style={{ padding: '8px 12px' }}><StatusBadge status={job.status} /></td>
                      <td style={{ padding: '8px 12px', fontSize: 12 }}>{job.started_at ? new Date(job.started_at).toLocaleString() : '—'}</td>
                      <td style={{ padding: '8px 12px', fontSize: 12 }}>{job.finished_at ? new Date(job.finished_at).toLocaleString() : '—'}</td>
                      <td style={{ padding: '8px 12px', textAlign: 'right' }}>{job.rows_inserted}</td>
                      <td style={{ padding: '8px 12px', textAlign: 'right' }}>{job.rows_updated}</td>
                      <td style={{ padding: '8px 12px', textAlign: 'right', color: job.rows_errored > 0 ? 'var(--color-danger)' : 'inherit' }}>{job.rows_errored}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* ETL workflow diagram */}
          <div className="card" style={{ marginTop: 20 }}>
            <div className="card-header"><h2 className="card-title">🔄 ETL Workflow</h2></div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', padding: '12px 0' }}>
              {[
                { step: '1', icon: '📂', title: 'EXTRACT', desc: 'Read CSV/JSON from datasets/' },
                { step: '→' },
                { step: '2', icon: '🔧', title: 'TRANSFORM', desc: 'Clean, dedupe, normalise tags & categories' },
                { step: '→' },
                { step: '3', icon: '💾', title: 'LOAD', desc: 'Upsert articles, tags, authors into SQLite' },
                { step: '→' },
                { step: '4', icon: '📊', title: 'REPORT', desc: 'Generate CSV reports in datasets/reports/' },
              ].map((s, i) =>
                s.title ? (
                  <div key={i} style={{ textAlign: 'center', background: 'var(--color-primary-light)', padding: '12px 20px', borderRadius: 8, minWidth: 140 }}>
                    <div style={{ fontSize: 28 }}>{s.icon}</div>
                    <div style={{ fontWeight: 700, color: 'var(--color-primary)', fontSize: 13 }}>STEP {s.step}: {s.title}</div>
                    <div style={{ fontSize: 11, color: 'var(--color-gray-600)', marginTop: 4 }}>{s.desc}</div>
                  </div>
                ) : (
                  <div key={i} style={{ fontSize: 24, color: 'var(--color-gray-400)' }}>{s.step}</div>
                )
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
