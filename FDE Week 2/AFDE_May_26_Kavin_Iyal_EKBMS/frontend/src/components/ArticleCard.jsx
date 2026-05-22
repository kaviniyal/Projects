import { Link } from 'react-router-dom'
import { Badge, StarRating } from './Common'

/**
 * Reusable article card used in list and search views.
 */
function ArticleCard({ article }) {
  const formatDate = (d) => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })

  return (
    <Link to={`/articles/${article.article_id}`} className="article-card">
      <div className="article-card-header">
        <Badge value={article.status} />
        <span className="text-xs text-muted">v{article.version}</span>
      </div>

      <div className="article-card-title">{article.title}</div>

      {article.summary && (
        <div className="article-card-summary">{article.summary}</div>
      )}

      {article.tags && article.tags.length > 0 && (
        <div className="mb-2">
          {article.tags.slice(0, 4).map((tag) => (
            <span key={tag.tag_id} className="tag">#{tag.tag_name}</span>
          ))}
        </div>
      )}

      <div className="article-card-meta">
        <span>
          <strong>{article.category_name}</strong> · {article.author_name}
        </span>
        <span>{formatDate(article.updated_at)}</span>
      </div>

      <div className="flex items-center justify-between mt-2">
        <StarRating value={article.average_rating} count={article.rating_count} readOnly />
        <span className="text-xs text-muted">👁 {article.view_count}</span>
      </div>
    </Link>
  )
}

export default ArticleCard
