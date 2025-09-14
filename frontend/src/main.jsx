import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom'
import './styles.css'
import axios from 'axios'
import AutoTariffPage from './auto-tariff.jsx'
import MarkupManager from './markup-manager.jsx'
import AutoTransportPage from './auto-transport.jsx'
import RailwayTransportPage from './railway-transport.jsx'
import SeaTransportPage from './sea-transport.jsx'
import AirTransportPage from './air-transport.jsx'
import MultimodalTransportPage from './multimodal-transport.jsx'
import TransportSelectorPage from './transport-selector.jsx'
import UserManagement from './components/UserManagement.jsx'
import MarkupManagement from './components/MarkupManagement.jsx'

const API_BASE = import.meta.env.VITE_API || 'http://127.0.0.1:8000'
axios.defaults.baseURL = API_BASE
axios.interceptors.request.use((config) => {
  const t = localStorage.getItem('token')
  if (t) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${t}`
  }
  return config
})
axios.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem('token')
      if (!location.pathname.startsWith('/login')) {
        location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

function useAuth() {
  const [token, setToken] = React.useState(localStorage.getItem('token') || '')
  const [user, setUser] = React.useState(null)

  // Загружаем информацию о пользователе при инициализации
  React.useEffect(() => {
    const loadUser = async () => {
      const t = localStorage.getItem('token')
      if (t) {
        try {
          const response = await axios.get('/auth/me', {
            headers: { 'Authorization': `Bearer ${t}` }
          })
          setUser(response.data)
        } catch (err) {
          // Если токен недействителен, удаляем его
          localStorage.removeItem('token')
          setToken('')
        }
      }
    }
    loadUser()
  }, [])

  const login = async (username, password) => {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    const res = await axios.post('/auth/login', params, { baseURL: API_BASE })
    const t = res.data.access_token
    localStorage.setItem('token', t)
    setToken(t)
    const me = await axios.get('/auth/me', { baseURL: API_BASE, headers: { Authorization: `Bearer ${t}` } })
    setUser(me.data)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken('')
    setUser(null)
  }

  return { token, user, login, logout }
}

function Header({ user, onLogout, onToggleSidebar, sidebarOpen }) {
  const nav = useNavigate()
  return (
    <header className="app-header">
      <div className="header-left">
        <button 
          className={`menu-toggle ${sidebarOpen ? 'active' : ''}`}
          onClick={onToggleSidebar}
          title={sidebarOpen ? "Закрыть меню" : "Открыть меню"}
        >
          <span className="hamburger">
            <span></span>
            <span></span>
            <span></span>
          </span>
        </button>
        <div className="header-brand">
          <div className="header-logo">
            <span className="logo-letter">В</span>
          </div>
          <div className="header-title">
            {import.meta.env.VITE_BRAND_NAME || 'Верес-Тариф'}
          </div>
        </div>
      </div>
      <div className="header-user">
        <div className="user-info">
          <div className="user-avatar">
            {user?.full_name?.charAt(0) || user?.username?.charAt(0) || 'Г'}
          </div>
          <div className="user-details">
            <div className="user-name">{user?.full_name || user?.username || 'Гость'}</div>
            <div className="user-role">{user?.role || 'Пользователь'}</div>
          </div>
        </div>
        {user && (
          <button 
            className="logout-btn" 
            onClick={() => { onLogout(); nav('/login') }}
            title="Выйти из системы"
          >
            <span>Выйти</span>
            <span className="logout-icon">🚪</span>
          </button>
        )}
      </div>
    </header>
  )
}

function Sidebar({ user, onLogout, isOpen, onClose }) {
  const nav = useNavigate()
  const location = window.location.pathname
  
  // Базовые пункты меню для всех пользователей
  const baseNavItems = [
    { to: "/transport-selector", icon: "🚛", label: "Выбор транспорта", desc: "Выберите тип перевозки", roles: ['admin', 'employee', 'forwarder', 'client'] }
  ]
  
  // Пункты меню для разных ролей
  const roleNavItems = {
    admin: [
      { to: "/auto-tariff", icon: "🤖", label: "Авто-тарифы", desc: "ИИ создание тарифов" },
      { to: "/user-management", icon: "👥", label: "Пользователи", desc: "Управление пользователями" },
      { to: "/markup-management", icon: "💰", label: "Наценки", desc: "Управление наценками" },
      { to: "/history", icon: "📊", label: "История запросов", desc: "История и статистика" },
      { to: "/archive", icon: "📑", label: "Архив", desc: "Архив тарифов" }
    ],
    employee: [
      { to: "/auto-tariff", icon: "🤖", label: "Авто-тарифы", desc: "ИИ создание тарифов" },
      { to: "/user-management", icon: "👥", label: "Пользователи", desc: "Управление экспедиторами и клиентами" },
      { to: "/markup-management", icon: "💰", label: "Наценки", desc: "Управление наценками" },
      { to: "/history", icon: "📊", label: "История запросов", desc: "История и статистика" },
      { to: "/archive", icon: "📑", label: "Архив", desc: "Архив тарифов" }
    ],
    forwarder: [
      { to: "/auto-tariff", icon: "🤖", label: "Авто-тарифы", desc: "ИИ создание тарифов" }
    ],
    client: [
      { to: "/history", icon: "📊", label: "История запросов", desc: "История и статистика" }
    ]
  }
  
  // Объединяем пункты меню в зависимости от роли
  const getNavItems = () => {
    const userRole = user?.role || 'client'
    const roleItems = roleNavItems[userRole] || []
    return [...baseNavItems, ...roleItems]
  }
  
  const navItems = getNavItems()
  
  const handleLinkClick = () => {
    // Закрываем меню при клике на ссылку на мобильных устройствах
    if (window.innerWidth <= 768) {
      onClose?.()
    }
  }
  
  return (
    <>
      {/* Overlay для мобильных устройств */}
      {isOpen && <div className="sidebar-overlay" onClick={onClose}></div>}
      
      <aside className={`app-sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h3 className="sidebar-title">Навигация</h3>
          <button className="sidebar-close" onClick={onClose} title="Закрыть меню">
            <span>×</span>
          </button>
        </div>
        
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <Link 
              key={item.to}
              to={item.to} 
              className={`nav-link ${location === item.to ? 'active' : ''}`}
              onClick={handleLinkClick}
            >
              <div className="nav-icon">{item.icon}</div>
              <div className="nav-content">
                <div className="nav-label">{item.label}</div>
                <div className="nav-desc">{item.desc}</div>
              </div>
              {location === item.to && <div className="nav-indicator"></div>}
            </Link>
          ))}
        </nav>
        
        <div className="sidebar-footer">
          <button 
            className="sidebar-logout-btn" 
            onClick={() => { onLogout?.(); nav('/login') }}
          >
            <span className="logout-icon">🚪</span>
            <span>Выйти</span>
          </button>
        </div>
      </aside>
    </>
  )
}

function Dashboard({ stats, user }) {
  const navigate = useNavigate()
  
  const handleNavigation = (path) => {
    navigate(path)
  }
  
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Панель управления</h1>
        <p className="dashboard-subtitle">Добро пожаловать в систему управления тарифами</p>
      </div>
      
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <div className="stat-value">{stats.tariffs}</div>
            <div className="stat-label">Тарифов в базе</div>
            <div className="stat-trend">+12% за месяц</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🚀</div>
          <div className="stat-content">
            <div className="stat-value">{stats.offers}</div>
            <div className="stat-label">Коммерческих предложений</div>
            <div className="stat-trend">+5% за неделю</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">👥</div>
          <div className="stat-content">
            <div className="stat-value">{stats.users}</div>
            <div className="stat-label">Поставщиков</div>
            <div className="stat-trend">+3 новых</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⚡</div>
          <div className="stat-content">
            <div className="stat-value">98%</div>
            <div className="stat-label">Доступность системы</div>
            <div className="stat-trend">Отлично</div>
          </div>
        </div>
      </div>
      
      <div className="dashboard-actions">
        <div className="action-card">
          <div className="action-icon">🚛</div>
          <div className="action-content">
            <h3>Выбор транспорта</h3>
            <p>Выберите тип перевозки и найдите подходящие тарифы</p>
          </div>
          <button 
            className="action-btn"
            onClick={() => handleNavigation('/transport-selector')}
          >
            Перейти
          </button>
        </div>
        {user?.role !== 'client' && (
          <div className="action-card">
            <div className="action-icon">🤖</div>
            <div className="action-content">
              <h3>Авто-тарифы</h3>
              <p>Создайте тарифы автоматически с помощью ИИ</p>
            </div>
            <button 
              className="action-btn"
              onClick={() => handleNavigation('/auto-tariff')}
            >
              Создать
            </button>
          </div>
        )}
        {user?.role !== 'forwarder' && (
          <div className="action-card">
            <div className="action-icon">📈</div>
            <div className="action-content">
              <h3>Аналитика</h3>
              <p>Просмотрите статистику и отчеты по тарифам</p>
            </div>
            <button 
              className="action-btn"
              onClick={() => handleNavigation('/history')}
            >
              Открыть
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function HistoryPage({ token, user }) {
  const [rows, setRows] = React.useState([])
  const [loading, setLoading] = React.useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const res = await axios.get('/requests/', { baseURL: API_BASE, headers: { Authorization: `Bearer ${token}` } })
      setRows(res.data)
    } finally {
      setLoading(false)
    }
  }

  React.useEffect(() => { if (token) load() }, [token])

  const downloadKP = async (req) => {
    try {
      // Сначала получаем результаты расчета для этого запроса
      const calculateResponse = await axios.post('/calculate', req.request_data, { 
        baseURL: API_BASE, 
        headers: { Authorization: `Bearer ${token}` } 
      })
      
      const results = calculateResponse.data
      
      // Теперь генерируем КП с результатами расчета
      const gen = await axios.post('/offers/generate', { 
        request: { 
          ...req.request_data, 
          selected_tariffs: results,
          results: results
        }
      }, { 
        baseURL: API_BASE, 
        headers: { Authorization: `Bearer ${token}` } 
      })
      
      const offerId = gen.data.id
      const resp = await axios.get(`/offers/${offerId}/download`, { 
        baseURL: API_BASE, 
        headers: { Authorization: `Bearer ${token}` }, 
        responseType: 'blob' 
      })
      
      const blob = new Blob([resp.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `offer_${offerId}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Ошибка генерации КП:', error)
      alert('Ошибка при генерации КП: ' + (error.response?.data?.detail || error.message))
    }
  }

  return (
    <div className="content">
      <div className="container">
        <div className="card card-pad">
          <h2 className="title">История запросов</h2>
          {loading ? <div>Загрузка...</div> : (
            <table>
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Вид</th>
                  <th>Маршрут</th>
                  <th>Базис</th>
                  {(user?.role === 'admin' || user?.role === 'employee') && <th>Клиент</th>}
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {rows.map(r => (
                  <tr key={r.id}>
                    <td>{(() => {
                      const date = new Date(r.created_at);
                      // Добавляем 3 часа для московского времени
                      const moscowTime = new Date(date.getTime() + (3 * 60 * 60 * 1000));
                      return moscowTime.toLocaleString('ru-RU', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: false
                      });
                    })()}</td>
                    <td>{r.request_data?.transport_type || '-'}</td>
                    <td>{(r.request_data?.origin_city||'-') + ' → ' + (r.request_data?.destination_city||'-')}</td>
                    <td>{r.request_data?.basis || '-'}</td>
                    {(user?.role === 'admin' || user?.role === 'employee') && (
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                          <span style={{ fontWeight: 'bold' }}>{r.user?.full_name || r.user?.username || 'Неизвестно'}</span>
                          {r.user?.company_name && (
                            <span style={{ fontSize: '0.8em', color: 'var(--text-muted)' }}>
                              {r.user.company_name}
                            </span>
                          )}
                        </div>
                      </td>
                    )}
                    <td><button className="btn btn-secondary" onClick={()=>downloadKP(r)}>Скачать КП</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}

function ArchivePage({ token }) {
  const [rows, setRows] = React.useState([])
  const [loading, setLoading] = React.useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const res = await axios.get('/tariffs/archive', { baseURL: API_BASE, headers: { Authorization: `Bearer ${token}` } })
      setRows(res.data)
    } finally {
      setLoading(false)
    }
  }

  React.useEffect(() => { if (token) load() }, [token])

  return (
    <div className="content">
      <div className="container">
        <div className="card card-pad">
          <h2 className="title">Архив тарифов</h2>
          {loading ? <div>Загрузка...</div> : (
              <table>
                <thead>
                  <tr>
                  <th>Дата архивирования</th>
                  <th>Поставщик</th>
                    <th>Тип транспорта</th>
                  <th>Маршрут</th>
                    <th>Базис</th>
                    <th>Цена (RUB)</th>
                    <th>Цена (USD)</th>
                    <th>Создатель</th>
                  </tr>
                </thead>
                <tbody>
                {rows.map(r => (
                  <tr key={r.id}>
                    <td>{r.archived_at ? new Date(r.archived_at).toLocaleString('ru-RU') : 'Неизвестно'}</td>
                    <td>{r.supplier_name || '-'}</td>
                    <td>{r.transport_type || '-'}</td>
                    <td>{r.route || '-'}</td>
                    <td>{r.basis || '-'}</td>
                    <td>{r.price_rub ? `${r.price_rub.toLocaleString('ru-RU')} ₽` : '-'}</td>
                    <td>{r.price_usd ? `$${r.price_usd.toLocaleString('ru-RU')}` : '-'}</td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                        <span style={{ fontWeight: 'bold' }}>{r.created_by || 'Система'}</span>
                        {r.created_by_role && (
                          <span style={{ fontSize: '0.8em', color: 'var(--text-muted)' }}>
                            {r.created_by_role === 'forwarder' ? 'Экспедитор' : 
                             r.created_by_role === 'employee' ? 'Сотрудник' : 
                             r.created_by_role === 'admin' ? 'Администратор' : r.created_by_role}
                          </span>
                        )}
                      </div>
                    </td>
                    </tr>
                  ))}
                </tbody>
              </table>
          )}
        </div>
      </div>
    </div>
  )
}

function SettingsPage({ token, user }) {
  const [suppliers, setSuppliers] = React.useState([])
  const [loading, setLoading] = React.useState(true)
  const [activeTab, setActiveTab] = React.useState('suppliers')

  const load = async () => {
    setLoading(true)
    try {
      const res = await axios.get('/suppliers/', { baseURL: API_BASE, headers: { Authorization: `Bearer ${token}` } })
      setSuppliers(res.data)
    } finally {
      setLoading(false)
    }
  }

  React.useEffect(() => { if (token) load() }, [token])

  return (
    <div className="content">
      <div className="container">
        <div className="card card-pad">
          <h2 className="title">Настройки</h2>
          
          <div className="settings-tabs">
            <button 
              className={`tab-button ${activeTab === 'suppliers' ? 'active' : ''}`}
              onClick={() => setActiveTab('suppliers')}
            >
              Поставщики
            </button>
            <button 
              className={`tab-button ${activeTab === 'markup' ? 'active' : ''}`}
              onClick={() => setActiveTab('markup')}
            >
              Управление наценками
            </button>
          </div>

          <div className="settings-content">
            {activeTab === 'suppliers' && (
              <div className="settings-section">
                <h3>Список поставщиков</h3>
                {loading ? <div>Загрузка...</div> : (
                  <table>
                    <thead>
                      <tr>
                        <th>Название</th>
                        <th>Контактное лицо</th>
                        <th>Email</th>
                        <th>Телефон</th>
                        <th>Наценка (%)</th>
                        <th>Фиксированная наценка</th>
                      </tr>
                    </thead>
                    <tbody>
                      {suppliers.map(s => (
                        <tr key={s.id}>
                          <td>{s.name}</td>
                          <td>{s.contact_person || '-'}</td>
                          <td>{s.contact_email || '-'}</td>
                          <td>{s.contact_phone || '-'}</td>
                          <td className={s.markup_percent > 0 ? 'highlight' : ''}>
                            {s.markup_percent || '0'}%
                          </td>
                          <td className={s.markup_fixed > 0 ? 'highlight' : ''}>
                            {s.markup_fixed || '0'} ₽
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {activeTab === 'markup' && (
              <MarkupManager 
                token={token} 
                suppliers={suppliers} 
                onUpdate={load}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function AuthPage({ onLogin, mode = 'client' }) {
  const [username, setUsername] = React.useState('')
  const [password, setPassword] = React.useState('')
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState('')
  const [showPassword, setShowPassword] = React.useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await onLogin(username, password)
    } catch (e) {
      setError(e?.response?.data?.detail || 'Ошибка входа')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-background">
        <div className="auth-particles"></div>
      </div>
      
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <div className="auth-logo">
              <div className="auth-logo-icon">
                <span className="logo-letter">В</span>
              </div>
              <div className="auth-logo-text">
                {import.meta.env.VITE_BRAND_NAME || 'Верес-Тариф'}
              </div>
            </div>
            <h1 className="auth-title">Добро пожаловать</h1>
            <p className="auth-subtitle">Войдите в систему для доступа к тарифам и логистическим решениям</p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="field-group">
              <label className="field-label">Имя пользователя</label>
              <div className="field-input-wrapper">
                <input 
                  type="text"
                  value={username} 
                  onChange={(e) => setUsername(e.target.value)}
                  className="field-input"
                  placeholder="Введите имя пользователя"
                  required
                />
                <div className="field-icon">👤</div>
              </div>
            </div>

            <div className="field-group">
              <label className="field-label">Пароль</label>
              <div className="field-input-wrapper">
                <input 
                  type={showPassword ? "text" : "password"}
                  value={password} 
                  onChange={(e) => setPassword(e.target.value)}
                  className="field-input"
                  placeholder="Введите пароль"
                  required
                />
                <button
                  type="button"
                  className="field-icon field-icon-button"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
            </div>

            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}

            <button 
              type="submit" 
              className="auth-button" 
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="loading-spinner"></span>
                  Вход в систему...
                </>
              ) : (
                <>
                  <span>Войти</span>
                  <span className="button-arrow">→</span>
                </>
              )}
            </button>
          </form>

          <div className="auth-demo">
            <h4 className="demo-title">🚀 Демо-аккаунты для тестирования</h4>
            <div className="demo-accounts">
              <div className="demo-account">
                <div className="demo-badge admin">👑 Администратор</div>
                <button 
                  type="button"
                  className="demo-button"
                  onClick={() => {
                    setUsername('admin')
                    setPassword('admin123')
                  }}
                >
                  admin / admin123
                </button>
              </div>
              <div className="demo-account">
                <div className="demo-badge employee">👨‍💼 Сотрудник</div>
                <button 
                  type="button"
                  className="demo-button"
                  onClick={() => {
                    setUsername('employee1')
                    setPassword('employee123')
                  }}
                >
                  employee1 / employee123
                </button>
              </div>
              <div className="demo-account">
                <div className="demo-badge forwarder">📦 Экспедитор</div>
                <button 
                  type="button"
                  className="demo-button"
                  onClick={() => {
                    setUsername('forwarder1')
                    setPassword('forwarder123')
                  }}
                >
                  forwarder1 / forwarder123
                </button>
              </div>
              <div className="demo-account">
                <div className="demo-badge client">👤 Клиент</div>
                <button 
                  type="button"
                  className="demo-button"
                  onClick={() => {
                    setUsername('client1')
                    setPassword('client123')
                  }}
                >
                  client1 / client123
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function Layout({ auth, children }) {
  const [sidebarOpen, setSidebarOpen] = React.useState(false)
  
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen)
  }
  
  const closeSidebar = () => {
    setSidebarOpen(false)
  }
  
  // Закрываем сайдбар при изменении размера экрана
  React.useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 768) {
        setSidebarOpen(false)
      }
    }
    
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])
  
  return (
    <div className="app-layout">
      <Header 
        user={auth.user} 
        onLogout={auth.logout} 
        onToggleSidebar={toggleSidebar}
        sidebarOpen={sidebarOpen}
      />
      <div className="layout-body">
        <Sidebar 
          user={auth.user}
          onLogout={auth.logout} 
          isOpen={sidebarOpen}
          onClose={closeSidebar}
        />
        <main className="main-content">
          <div className="content-wrapper">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

function App() {
  const auth = useAuth()
  const [stats, setStats] = React.useState({ tariffs: 0, offers: 0, users: 0 })

  React.useEffect(() => {
    const load = async () => {
      try {
        if (!auth.token) return
        const [tariffs, suppliers] = await Promise.all([
          axios.get('/tariffs/', { baseURL: API_BASE, headers: { Authorization: `Bearer ${auth.token}` }}),
          axios.get('/suppliers/', { baseURL: API_BASE, headers: { Authorization: `Bearer ${auth.token}` }}),
        ])
        setStats({ tariffs: tariffs.data.length, offers: 0, users: suppliers.data.length })
      } catch {}
    }
    load()
  }, [auth.token])

  return (
    <BrowserRouter>
      <Routes>
        {!auth.token ? (
          <>
            <Route path="/login" element={<Navigate to="/login/client" />} />
            <Route path="/login/client" element={<AuthPage onLogin={auth.login} mode="client" />} />
            <Route path="/login/admin" element={<AuthPage onLogin={auth.login} mode="admin" />} />
            <Route path="*" element={<AuthPage onLogin={auth.login} />} />
          </>
        ) : (
          <>
            <Route path="/" element={<Layout auth={auth}><Dashboard stats={stats} user={auth.user} /></Layout>} />
            <Route path="/transport-selector" element={<Layout auth={auth}><TransportSelectorPage token={auth.token} user={auth.user} /></Layout>} />
            <Route path="/auto-transport" element={<Layout auth={auth}><AutoTransportPage token={auth.token} user={auth.user} /></Layout>} />
            <Route path="/railway-transport" element={<Layout auth={auth}><RailwayTransportPage token={auth.token} user={auth.user} /></Layout>} />
            <Route path="/sea-transport" element={<Layout auth={auth}><SeaTransportPage token={auth.token} user={auth.user} /></Layout>} />
            <Route path="/air-transport" element={<Layout auth={auth}><AirTransportPage token={auth.token} user={auth.user} /></Layout>} />
            <Route path="/multimodal-transport" element={<Layout auth={auth}><MultimodalTransportPage token={auth.token} user={auth.user} /></Layout>} />
            <Route path="/auto-tariff" element={<Layout auth={auth}><AutoTariffPage token={auth.token} /></Layout>} />
            <Route path="/history" element={<Layout auth={auth}><HistoryPage token={auth.token} user={auth.user} /></Layout>} />
            <Route path="/archive" element={<Layout auth={auth}><ArchivePage token={auth.token} /></Layout>} />
            <Route path="/settings" element={<Layout auth={auth}><SettingsPage token={auth.token} user={auth.user} /></Layout>} />
            {/* Маршруты для системы пользователей */}
            <Route path="/user-management" element={<Layout auth={auth}><UserManagement user={auth.user} /></Layout>} />
            <Route path="/markup-management" element={<Layout auth={auth}><MarkupManagement user={auth.user} /></Layout>} />
            <Route path="*" element={<Navigate to="/" />} />
          </>
        )}
      </Routes>
    </BrowserRouter>
  )
}

createRoot(document.getElementById('root')).render(<App />)
