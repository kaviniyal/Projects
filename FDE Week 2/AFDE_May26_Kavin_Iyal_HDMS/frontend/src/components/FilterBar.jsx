import { CATEGORIES, PRIORITIES, STATUSES } from '../services/ticketService'

/**
 * Filter bar used on the Listing and Search pages.
 *
 * `showKeyword` toggles the keyword input — only the Search page uses it.
 */
function FilterBar({ filters, onFilterChange, onReset, showKeyword = false }) {
  const handleChange = (field, value) => {
    onFilterChange({ ...filters, [field]: value })
  }

  return (
    <div className="filters-bar">
      {showKeyword && (
        <div className="filter-field">
          <label>Search keyword</label>
          <input
            type="text"
            className="form-input"
            placeholder="Search by name, description, etc..."
            value={filters.keyword || ''}
            onChange={(e) => handleChange('keyword', e.target.value)}
          />
        </div>
      )}

      <div className="filter-field">
        <label>Status</label>
        <select
          className="form-select"
          value={filters.status || ''}
          onChange={(e) => handleChange('status', e.target.value)}
        >
          <option value="">All Statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      <div className="filter-field">
        <label>Category</label>
        <select
          className="form-select"
          value={filters.category || ''}
          onChange={(e) => handleChange('category', e.target.value)}
        >
          <option value="">All Categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      <div className="filter-field">
        <label>Priority</label>
        <select
          className="form-select"
          value={filters.priority || ''}
          onChange={(e) => handleChange('priority', e.target.value)}
        >
          <option value="">All Priorities</option>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>

      <button onClick={onReset} className="btn btn-secondary">Reset</button>
    </div>
  )
}

export default FilterBar
