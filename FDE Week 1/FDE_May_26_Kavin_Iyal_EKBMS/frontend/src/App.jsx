import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import { ProtectedRoute } from './components/Common'
import { useAuth } from './context/AuthContext'

import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import ArticleList from './pages/ArticleList'
import ArticleDetail from './pages/ArticleDetail'
import ArticleEditor from './pages/ArticleEditor'
import SearchPage from './pages/SearchPage'
import MyArticles from './pages/MyArticles'
import ApprovalQueue from './pages/ApprovalQueue'
import Bookmarks from './pages/Bookmarks'
import CategoryManagement from './pages/CategoryManagement'
import UserManagement from './pages/UserManagement'

function AppShell({ children }) {
  const { isAuthenticated } = useAuth()
  return (
    <div className="app">
      {isAuthenticated && <Navbar />}
      <div className={isAuthenticated ? 'main-content' : ''}>{children}</div>
    </div>
  )
}

function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/articles" element={<ProtectedRoute><ArticleList /></ProtectedRoute>} />
        <Route path="/articles/new" element={<ProtectedRoute roles={['Author', 'Admin']}><ArticleEditor /></ProtectedRoute>} />
        <Route path="/articles/:id" element={<ProtectedRoute><ArticleDetail /></ProtectedRoute>} />
        <Route path="/articles/:id/edit" element={<ProtectedRoute roles={['Author', 'Admin']}><ArticleEditor /></ProtectedRoute>} />
        <Route path="/search" element={<ProtectedRoute><SearchPage /></ProtectedRoute>} />
        <Route path="/my-articles" element={<ProtectedRoute roles={['Author', 'Admin']}><MyArticles /></ProtectedRoute>} />
        <Route path="/approvals" element={<ProtectedRoute roles={['Reviewer', 'Admin']}><ApprovalQueue /></ProtectedRoute>} />
        <Route path="/bookmarks" element={<ProtectedRoute><Bookmarks /></ProtectedRoute>} />
        <Route path="/categories" element={<ProtectedRoute roles={['Admin']}><CategoryManagement /></ProtectedRoute>} />
        <Route path="/users" element={<ProtectedRoute roles={['Admin']}><UserManagement /></ProtectedRoute>} />

        <Route path="*" element={
          <div className="empty-state">
            <div className="empty-state-icon">🤷</div>
            <div className="empty-state-title">Page not found</div>
          </div>
        } />
      </Routes>
    </AppShell>
  )
}

export default App
