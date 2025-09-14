import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './RequestHistory.css';

const RequestHistory = ({ user }) => {
  const [requests, setRequests] = useState([]);
  const [users, setUsers] = useState([]);
  const [commercialOffers, setCommercialOffers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('requests');
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    user_id: '',
    limit: 50,
    offset: 0
  });

  useEffect(() => {
    fetchData();
  }, [filters]);

  const fetchData = async () => {
    try {
      const [requestsRes, usersRes, offersRes, statsRes] = await Promise.all([
        axios.get('/request-history/', {
          params: filters,
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        axios.get('/request-history/users', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        axios.get('/request-history/commercial-offers', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        axios.get('/request-history/stats', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
      ]);

      setRequests(requestsRes.data);
      setUsers(usersRes.data);
      setCommercialOffers(offersRes.data);
      setStats(statsRes.data);
    } catch (err) {
      setError('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      offset: 0 // Сбрасываем offset при изменении фильтров
    }));
  };

  const getUserName = (userId) => {
    const user = users.find(u => u.id === userId);
    return user ? (user.full_name || user.username) : 'Неизвестный пользователь';
  };

  const getUserRole = (userId) => {
    const user = users.find(u => u.id === userId);
    return user ? user.role : 'unknown';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU');
  };

  const formatRequestData = (requestData) => {
    try {
      const data = typeof requestData === 'string' ? JSON.parse(requestData) : requestData;
      return {
        transport_type: data.transport_type || 'Не указан',
        origin_city: data.origin_city || 'Не указан',
        destination_city: data.destination_city || 'Не указан',
        basis: data.basis || 'Не указан'
      };
    } catch {
      return {
        transport_type: 'Ошибка парсинга',
        origin_city: 'Ошибка парсинга',
        destination_city: 'Ошибка парсинга',
        basis: 'Ошибка парсинга'
      };
    }
  };

  if (loading) {
    return <div className="loading">Загрузка истории запросов...</div>;
  }

  return (
    <div className="request-history">
      <div className="history-header">
        <h2>История запросов и статистика</h2>
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'requests' ? 'active' : ''}`}
            onClick={() => setActiveTab('requests')}
          >
            Запросы
          </button>
          <button 
            className={`tab ${activeTab === 'offers' ? 'active' : ''}`}
            onClick={() => setActiveTab('offers')}
          >
            КП
          </button>
          <button 
            className={`tab ${activeTab === 'stats' ? 'active' : ''}`}
            onClick={() => setActiveTab('stats')}
          >
            Статистика
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {activeTab === 'requests' && (
        <div className="requests-section">
          <div className="filters">
            <div className="filter-group">
              <label>Пользователь:</label>
              <select
                value={filters.user_id}
                onChange={(e) => handleFilterChange('user_id', e.target.value)}
              >
                <option value="">Все пользователи</option>
                {users.map(user => (
                  <option key={user.id} value={user.id}>
                    {user.full_name || user.username} ({user.role})
                  </option>
                ))}
              </select>
            </div>
            
            <div className="filter-group">
              <label>Количество записей:</label>
              <select
                value={filters.limit}
                onChange={(e) => handleFilterChange('limit', parseInt(e.target.value))}
              >
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
                <option value={200}>200</option>
              </select>
            </div>
          </div>

          <div className="requests-list">
            {requests.map(request => {
              const requestData = formatRequestData(request.request_data);
              return (
                <div key={request.id} className="request-card">
                  <div className="request-header">
                    <div className="request-user">
                      <span className="user-name">{getUserName(request.user_id)}</span>
                      <span className={`user-role role-${getUserRole(request.user_id)}`}>
                        {getUserRole(request.user_id)}
                      </span>
                    </div>
                    <div className="request-date">
                      {formatDate(request.created_at)}
                    </div>
                  </div>
                  
                  <div className="request-details">
                    <div className="detail-item">
                      <span className="label">Тип транспорта:</span>
                      <span className="value">{requestData.transport_type}</span>
                    </div>
                    <div className="detail-item">
                      <span className="label">Маршрут:</span>
                      <span className="value">
                        {requestData.origin_city} → {requestData.destination_city}
                      </span>
                    </div>
                    <div className="detail-item">
                      <span className="label">Основание:</span>
                      <span className="value">{requestData.basis}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {activeTab === 'offers' && (
        <div className="offers-section">
          <h3>Коммерческие предложения</h3>
          <div className="offers-list">
            {commercialOffers.map(offer => (
              <div key={offer.id} className="offer-card">
                <div className="offer-header">
                  <div className="offer-user">
                    <span className="user-name">{getUserName(offer.user_id)}</span>
                    <span className={`user-role role-${getUserRole(offer.user_id)}`}>
                      {getUserRole(offer.user_id)}
                    </span>
                  </div>
                  <div className="offer-date">
                    {formatDate(offer.created_at)}
                  </div>
                </div>
                
                <div className="offer-details">
                  <div className="offer-file">
                    <span className="label">Файл:</span>
                    <span className="value">{offer.file_path.split('/').pop()}</span>
                  </div>
                  {offer.request_id && (
                    <div className="offer-request">
                      <span className="label">Связанный запрос:</span>
                      <span className="value">#{offer.request_id}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'stats' && stats && (
        <div className="stats-section">
          <h3>Статистика</h3>
          
          <div className="stats-overview">
            <div className="stat-card">
              <div className="stat-number">{stats.total_requests}</div>
              <div className="stat-label">Всего запросов</div>
            </div>
          </div>

          <div className="stats-details">
            <div className="user-stats">
              <h4>Статистика по пользователям</h4>
              <div className="user-stats-list">
                {stats.user_stats.map((stat, index) => (
                  <div key={index} className="user-stat-item">
                    <div className="user-info">
                      <span className="user-name">{stat.user_name}</span>
                      <span className={`user-role role-${stat.role}`}>
                        {stat.role}
                      </span>
                    </div>
                    <div className="request-count">
                      {stat.request_count} запросов
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="daily-stats">
              <h4>Активность за последние 30 дней</h4>
              <div className="daily-stats-list">
                {stats.daily_stats.map((stat, index) => (
                  <div key={index} className="daily-stat-item">
                    <div className="date">{stat.date}</div>
                    <div className="count">{stat.count} запросов</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RequestHistory;
