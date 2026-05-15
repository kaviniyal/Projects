-- =============================================================================
-- Enterprise Knowledge Base Management System — Database Schema
-- =============================================================================
-- This is the reference SQL schema. The actual application uses SQLAlchemy
-- which creates these tables automatically on startup.
-- =============================================================================

-- Roles
CREATE TABLE roles (
    role_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name    VARCHAR(50) UNIQUE NOT NULL,
    description  VARCHAR(255)
);

-- Users
CREATE TABLE users (
    user_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name             VARCHAR(100) NOT NULL,
    email            VARCHAR(120) UNIQUE NOT NULL,
    hashed_password  VARCHAR(255) NOT NULL,
    department       VARCHAR(100),
    role_id          INTEGER NOT NULL,
    is_active        BOOLEAN DEFAULT 1 NOT NULL,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

CREATE INDEX idx_users_email ON users(email);

-- Categories (hierarchical via self-FK)
CREATE TABLE categories (
    category_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name  VARCHAR(100) NOT NULL,
    description    VARCHAR(255),
    parent_id      INTEGER,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES categories(category_id)
);

CREATE INDEX idx_categories_name ON categories(category_name);

-- Tags
CREATE TABLE tags (
    tag_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name  VARCHAR(50) UNIQUE NOT NULL
);

-- Articles
CREATE TABLE articles (
    article_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title               VARCHAR(255) NOT NULL,
    content             TEXT NOT NULL,
    summary             VARCHAR(500),
    category_id         INTEGER NOT NULL,
    author_id           INTEGER NOT NULL,
    reviewer_id         INTEGER,
    status              VARCHAR(30) DEFAULT 'Draft' NOT NULL,
    approval_comments   TEXT,
    version             INTEGER DEFAULT 1 NOT NULL,
    view_count          INTEGER DEFAULT 0 NOT NULL,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    published_at        DATETIME,
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    FOREIGN KEY (author_id)   REFERENCES users(user_id),
    FOREIGN KEY (reviewer_id) REFERENCES users(user_id)
);

CREATE INDEX idx_articles_title  ON articles(title);
CREATE INDEX idx_articles_status ON articles(status);

-- Article ↔ Tags (many-to-many)
CREATE TABLE article_tags (
    article_id  INTEGER NOT NULL,
    tag_id      INTEGER NOT NULL,
    PRIMARY KEY (article_id, tag_id),
    FOREIGN KEY (article_id) REFERENCES articles(article_id),
    FOREIGN KEY (tag_id)     REFERENCES tags(tag_id)
);

-- Attachments
CREATE TABLE attachments (
    attachment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id     INTEGER NOT NULL,
    file_name      VARCHAR(255) NOT NULL,
    stored_name    VARCHAR(255) NOT NULL,
    file_size      INTEGER NOT NULL,
    content_type   VARCHAR(100),
    uploaded_at    DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (article_id) REFERENCES articles(article_id)
);

-- Comments
CREATE TABLE comments (
    comment_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id    INTEGER NOT NULL,
    user_id       INTEGER NOT NULL,
    comment_text  TEXT NOT NULL,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (article_id) REFERENCES articles(article_id),
    FOREIGN KEY (user_id)    REFERENCES users(user_id)
);

-- Ratings (1-5)
CREATE TABLE ratings (
    rating_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id    INTEGER NOT NULL,
    user_id       INTEGER NOT NULL,
    rating_value  INTEGER NOT NULL CHECK (rating_value BETWEEN 1 AND 5),
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (article_id) REFERENCES articles(article_id),
    FOREIGN KEY (user_id)    REFERENCES users(user_id)
);

-- Bookmarks (favorites)
CREATE TABLE bookmarks (
    bookmark_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id   INTEGER NOT NULL,
    user_id      INTEGER NOT NULL,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (article_id) REFERENCES articles(article_id),
    FOREIGN KEY (user_id)    REFERENCES users(user_id)
);

-- Article view log (for analytics)
CREATE TABLE article_views (
    view_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id  INTEGER NOT NULL,
    user_id     INTEGER,
    viewed_at   DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (article_id) REFERENCES articles(article_id),
    FOREIGN KEY (user_id)    REFERENCES users(user_id)
);

CREATE INDEX idx_views_article_id ON article_views(article_id);
CREATE INDEX idx_views_viewed_at  ON article_views(viewed_at);

-- =============================================================================
-- Seed data
-- =============================================================================
INSERT INTO roles (role_name, description) VALUES
    ('Admin',    'Full system access — manage users, categories, and settings'),
    ('Author',   'Create and manage knowledge articles'),
    ('Reviewer', 'Review and approve submitted articles'),
    ('Employee', 'Search and read approved articles');

INSERT INTO categories (category_name, description) VALUES
    ('HR Policies',       'Human resources policies and procedures'),
    ('IT Support',        'Technical support and troubleshooting guides'),
    ('Infrastructure',    'Network, servers, and infrastructure documentation'),
    ('Training Materials','Onboarding and training documents'),
    ('Finance',           'Finance and accounting procedures'),
    ('Operations',        'Operational SOPs and process documentation');

-- Default admin user (password 'admin123' bcrypt-hashed)
-- The actual hash is generated at runtime by seed.py. Replace this in production.
