import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, LineChart, Line, AreaChart, Area,
  ResponsiveContainer,
} from 'recharts';
import analyticsService from '../services/analyticsService';

// ─── Colour palettes ──────────────────────────────────────────────────────────
const PRIORITY_COLORS = {
  Critical: '#ef4444',
  High:     '#f97316',
  Medium:   '#eab308',
  Low:      '#22c55e',
};
const STATUS_COLORS = {
  Open:        '#3b82f6',
  'In Progress':'#a855f7',
  Resolved:    '#22c55e',
  Closed:      '#6b7280',
};
const CHART_COLORS = [
  '#6366f1','#22c55e','#f97316','#3b82f6',
  '#ec4899','#14b8a6','#eab308','#8b5cf6',
];

// ─── Helpers ──────────────────────────────────────────────────────────────────
const fmtMonth = (m) => {
  if (!m) return m;
  const [y, mo] = m.split('-');
  return new Date(y, mo - 1).toLocaleString('default', { month: 'short', year: '2-digit' });
};

const KPICard = ({ label, value, sub, color = '#6366f1' }) => (
  <div className="kpi-card" style={{ borderTop: `4px solid ${color}` }}>
    <div className="kpi-value" style={{ color }}>{value ?? '—'}</div>
    <div className="kpi-label">{label}</div>
    {sub && <div className="kpi-sub">{sub}</div>}
  </div>
);

const SectionTitle = ({ title, subtitle }) => (
  <div className="section-header">
    <h2 className="section-title">{title}</h2>
    {subtitle && <p className="section-subtitle">{subtitle}</p>}
  </div>
);

const ChartCard = ({ title, children, span = 1 }) => (
  <div className={`chart-card chart-span-${span}`}>
    <h3 className="chart-title">{title}</h3>
    {children}
  </div>
);

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <p className="tooltip-label">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toFixed(p.value % 1 ? 2 : 0) : p.value}</strong>
        </p>
      ))}
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function Analytics() {
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const [data, setData]       = useState({
    summary: null,
    categories: [],
    priorities: [],
    statuses: [],
    departments: [],
    monthlyVolume: [],
    resolutionTrends: [],
    etlStatus: null,
  });

  useEffect(() => {
    const load = async () => {
      try {
        const [
          summary, categories, priorities, statuses,
          departments, monthlyVolume, resolutionTrends, etlStatus,
        ] = await Promise.all([
          analyticsService.getSummary(),
          analyticsService.getCategoryDistribution(),
          analyticsService.getPriorityDistribution(),
          analyticsService.getStatusDistribution(),
          analyticsService.getDepartmentCounts(),
          analyticsService.getMonthlyVolume(),
          analyticsService.getResolutionTrends(),
          analyticsService.getEtlStatus(),
        ]);
        setData({ summary, categories, priorities, statuses, departments, monthlyVolume, resolutionTrends, etlStatus });
      } catch (e) {
        setError(e.response?.data?.detail || e.message || 'Failed to load analytics');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return (
    <div className="analytics-loading">
      <div className="spinner" />
      <p>Loading analytics data…</p>
    </div>
  );

  if (error) return (
    <div className="analytics-error">
      <span className="error-icon">⚠️</span>
      <h2>Analytics data unavailable</h2>
      <p>{error}</p>
      <p className="error-hint">Run <code>python etl/etl_pipeline.py</code> to populate the analytics database.</p>
    </div>
  );

  const { summary, categories, priorities, statuses, departments, monthlyVolume, resolutionTrends, etlStatus } = data;

  return (
    <div className="analytics-page">

      {/* ── Page Header ─────────────────────────────────────────────────────── */}
      <div className="analytics-header">
        <div>
          <h1 className="analytics-title">📊 Analytics Dashboard</h1>
          <p className="analytics-subtitle">Historical ticket metrics powered by the ETL pipeline</p>
        </div>
        {etlStatus?.run_at && (
          <div className="etl-badge">
            <span className={`etl-dot ${etlStatus.status === 'SUCCESS' ? 'etl-dot--ok' : 'etl-dot--err'}`} />
            ETL last ran: {new Date(etlStatus.run_at).toLocaleString()}
            &nbsp;·&nbsp;{etlStatus.records_loaded} records loaded
          </div>
        )}
      </div>

      {/* ── KPI Cards ───────────────────────────────────────────────────────── */}
      <div className="kpi-grid">
        <KPICard label="Total Tickets"         value={summary?.total_tickets}       color="#6366f1" />
        <KPICard label="Open / In-Progress"    value={summary?.open_tickets}         color="#f97316" />
        <KPICard label="Resolved / Closed"     value={summary?.resolved_tickets}     color="#22c55e"
          sub={`${summary?.resolution_rate_pct ?? 0}% resolution rate`} />
        <KPICard label="Avg Resolution"        value={summary?.avg_resolution_days != null ? `${summary.avg_resolution_days} days` : 'N/A'} color="#3b82f6" />
        <KPICard label="Critical Tickets"      value={summary?.critical_tickets}     color="#ef4444" />
        <KPICard label="Departments Tracked"   value={summary?.departments_tracked}  color="#14b8a6" />
      </div>

      {/* ── Row 1: Category + Priority ──────────────────────────────────────── */}
      <SectionTitle title="Issue Distribution" subtitle="Breakdown by category and priority" />
      <div className="charts-grid charts-grid--2">

        <ChartCard title="Tickets by Issue Category">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={categories} margin={{ left: 10, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="category" angle={-35} textAnchor="end" tick={{ fontSize: 12 }} interval={0} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" name="Tickets" radius={[4,4,0,0]}>
                {categories.map((_, i) => (
                  <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Priority Distribution">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={priorities}
                dataKey="count"
                nameKey="priority"
                cx="50%" cy="50%"
                outerRadius={110}
                innerRadius={55}
                paddingAngle={3}
                label={({ priority, percent }) =>
                  `${priority} ${(percent * 100).toFixed(0)}%`
                }
                labelLine={false}
              >
                {priorities.map((p, i) => (
                  <Cell key={i} fill={PRIORITY_COLORS[p.priority] || CHART_COLORS[i]} />
                ))}
              </Pie>
              <Tooltip formatter={(val, name) => [val, name]} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* ── Row 2: Monthly Volume + Resolution Trend ────────────────────────── */}
      <SectionTitle title="Time-Series Trends" subtitle="Monthly volume and resolution performance" />
      <div className="charts-grid charts-grid--2">

        <ChartCard title="Monthly Ticket Volume">
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={monthlyVolume} margin={{ left: 10, right: 20 }}>
              <defs>
                <linearGradient id="volGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" tickFormatter={fmtMonth} tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} labelFormatter={fmtMonth} />
              <Area
                type="monotone" dataKey="count" name="Tickets"
                stroke="#6366f1" strokeWidth={2} fill="url(#volGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Avg Resolution Time (days/month)">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={resolutionTrends} margin={{ left: 10, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" tickFormatter={fmtMonth} tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 12 }} unit=" d" />
              <Tooltip content={<CustomTooltip />} labelFormatter={fmtMonth} />
              <Legend />
              <Line
                type="monotone" dataKey="avg_resolution_days" name="Avg Days"
                stroke="#22c55e" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }}
              />
              <Line
                type="monotone" dataKey="resolved_count" name="Resolved"
                stroke="#f97316" strokeWidth={2} strokeDasharray="5 5"
                dot={{ r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* ── Row 3: Department + Status ───────────────────────────────────────── */}
      <SectionTitle title="Department & Status Breakdown" />
      <div className="charts-grid charts-grid--2">

        <ChartCard title="Tickets by Department">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={departments} layout="vertical" margin={{ left: 90, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="department" tick={{ fontSize: 12 }} width={85} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" name="Tickets" radius={[0,4,4,0]}>
                {departments.map((_, i) => (
                  <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Ticket Status Distribution">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statuses}
                dataKey="count"
                nameKey="status"
                cx="50%" cy="50%"
                outerRadius={110}
                label={({ status, percent }) =>
                  `${status} (${(percent * 100).toFixed(0)}%)`
                }
                labelLine={true}
              >
                {statuses.map((s, i) => (
                  <Cell key={i} fill={STATUS_COLORS[s.status] || CHART_COLORS[i]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* ── Row 4: Top Issues Table ──────────────────────────────────────────── */}
      <SectionTitle title="Top Issue Categories" subtitle="Ranked by ticket volume" />
      <div className="table-card">
        <table className="analytics-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Issue Category</th>
              <th>Ticket Count</th>
              <th>Share</th>
              <th>Volume Bar</th>
            </tr>
          </thead>
          <tbody>
            {categories.map((row, i) => {
              const pct = summary?.total_tickets
                ? ((row.count / summary.total_tickets) * 100).toFixed(1)
                : 0;
              return (
                <tr key={row.category}>
                  <td>{i + 1}</td>
                  <td>
                    <span
                      className="category-dot"
                      style={{ background: CHART_COLORS[i % CHART_COLORS.length] }}
                    />
                    {row.category}
                  </td>
                  <td><strong>{row.count}</strong></td>
                  <td>{pct}%</td>
                  <td>
                    <div className="vol-bar-bg">
                      <div
                        className="vol-bar-fill"
                        style={{
                          width: `${pct}%`,
                          background: CHART_COLORS[i % CHART_COLORS.length],
                        }}
                      />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* ── ETL Status Panel ────────────────────────────────────────────────── */}
      <SectionTitle title="ETL Pipeline Status" subtitle="Last pipeline execution details" />
      <div className="etl-panel">
        {etlStatus?.run_at ? (
          <div className="etl-stats">
            <div className="etl-stat">
              <span className="etl-stat-label">Run At</span>
              <span className="etl-stat-value">{new Date(etlStatus.run_at).toLocaleString()}</span>
            </div>
            <div className="etl-stat">
              <span className="etl-stat-label">Source File</span>
              <span className="etl-stat-value">{etlStatus.source_file?.split(/[\\/]/).pop()}</span>
            </div>
            <div className="etl-stat">
              <span className="etl-stat-label">Extracted</span>
              <span className="etl-stat-value">{etlStatus.records_extracted}</span>
            </div>
            <div className="etl-stat">
              <span className="etl-stat-label">Duplicates Removed</span>
              <span className="etl-stat-value" style={{ color: '#f97316' }}>
                {etlStatus.duplicates_removed}
              </span>
            </div>
            <div className="etl-stat">
              <span className="etl-stat-label">Loaded</span>
              <span className="etl-stat-value" style={{ color: '#22c55e' }}>
                {etlStatus.records_loaded}
              </span>
            </div>
            <div className="etl-stat">
              <span className="etl-stat-label">Status</span>
              <span
                className="etl-stat-value"
                style={{ color: etlStatus.status === 'SUCCESS' ? '#22c55e' : '#ef4444' }}
              >
                {etlStatus.status === 'SUCCESS' ? '✅ SUCCESS' : '❌ FAILED'}
              </span>
            </div>
          </div>
        ) : (
          <div className="etl-no-run">
            <p>⚠️ No ETL runs recorded.</p>
            <code>python etl/etl_pipeline.py</code>
          </div>
        )}
      </div>

    </div>
  );
}
