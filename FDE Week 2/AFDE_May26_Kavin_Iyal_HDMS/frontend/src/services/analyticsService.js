/**
 * Analytics Service – Phase 2
 * All API calls to /analytics/* endpoints (backed by ETL-populated analytics.db)
 */
import api from '../api';

const analyticsService = {
  /** High-level KPI cards */
  getSummary: () => api.get('/analytics/summary').then(r => r.data),

  /** Bar chart: tickets per category */
  getCategoryDistribution: () =>
    api.get('/analytics/category-distribution').then(r => r.data),

  /** Pie/donut: tickets per priority */
  getPriorityDistribution: () =>
    api.get('/analytics/priority-distribution').then(r => r.data),

  /** Pie/donut: tickets per status */
  getStatusDistribution: () =>
    api.get('/analytics/status-distribution').then(r => r.data),

  /** Bar chart: tickets per department */
  getDepartmentCounts: () =>
    api.get('/analytics/department-counts').then(r => r.data),

  /** Line/area: monthly ticket volume */
  getMonthlyVolume: () =>
    api.get('/analytics/monthly-volume').then(r => r.data),

  /** Line: avg resolution time per month */
  getResolutionTrends: () =>
    api.get('/analytics/resolution-trends').then(r => r.data),

  /** Grouped bar / heatmap: category × department */
  getCategoryByDepartment: () =>
    api.get('/analytics/category-by-department').then(r => r.data),

  /** ETL audit info */
  getEtlStatus: () => api.get('/analytics/etl-status').then(r => r.data),
  getEtlHistory: (limit = 10) =>
    api.get(`/analytics/etl-history?limit=${limit}`).then(r => r.data),
};

export default analyticsService;
