/**
 * Reusable Badge for ticket status and priority.
 *
 * The CSS class is derived from `type` + a slugged version of `value` so
 * that, for example, "In Progress" maps to `badge-in-progress`.
 */
function Badge({ type, value }) {
  const slug = value.toLowerCase().replace(/\s+/g, '-')
  return <span className={`badge badge-${slug}`}>{value}</span>
}

export function StatusBadge({ status }) {
  return <Badge type="status" value={status} />
}

export function PriorityBadge({ priority }) {
  return <Badge type="priority" value={priority} />
}

export default Badge
