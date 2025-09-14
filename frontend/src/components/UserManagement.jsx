import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './UserManagement.css';

const UserManagement = ({ user }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [formData, setFormData] = useState({
    username: '',
    password: '',
    role: 'client',
    full_name: '',
    email: '',
    phone: '',
    company_name: '',
    responsible_person: ''
  });

  const roleLabels = {
    admin: 'Администратор',
    employee: 'Сотрудник',
    forwarder: 'Экспедитор',
    client: 'Клиент'
  };

  const roleDescriptions = {
    admin: 'Полный доступ ко всем функциям системы',
    employee: 'Управление экспедиторами и клиентами, установка наценок',
    forwarder: 'Добавление тарифов, выбор транспорта',
    client: 'Выбор транспорта, скачивание КП'
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      let endpoint = '/users/';
      if (user.role === 'employee') {
        endpoint = '/users/forwarders-and-clients';
      }
      
      const response = await axios.get(endpoint, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setUsers(response.data);
    } catch (err) {
      setError('Ошибка загрузки пользователей');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      if (editingUser) {
        // Обновление пользователя
        let endpoint = `/users/${editingUser.id}`;
        if (user.role === 'employee') {
          endpoint = `/users/forwarder/${editingUser.id}`;
        }
        
        await axios.put(endpoint, formData, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        setSuccess('Пользователь успешно обновлен');
      } else {
        // Создание нового пользователя
        let endpoint = '/users/';
        if (user.role === 'employee') {
          endpoint = '/users/forwarder';
        }
        
        await axios.post(endpoint, formData, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        setSuccess('Пользователь успешно создан');
      }

      setShowCreateForm(false);
      setEditingUser(null);
      resetForm();
      fetchUsers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка сохранения пользователя');
    }
  };

  const handleEdit = (user) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      password: '',
      role: user.role,
      full_name: user.full_name || '',
      email: user.email || '',
      phone: user.phone || '',
      company_name: user.company_name || '',
      responsible_person: user.responsible_person || ''
    });
    setShowCreateForm(true);
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этого пользователя?')) {
      return;
    }

    try {
      let endpoint = `/users/${userId}`;
      if (user.role === 'employee') {
        endpoint = `/users/forwarder/${userId}`;
      }
      
      await axios.delete(endpoint, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setSuccess('Пользователь успешно удален');
      fetchUsers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка удаления пользователя');
    }
  };

  const resetForm = () => {
    setFormData({
      username: '',
      password: '',
      role: 'client',
      full_name: '',
      email: '',
      phone: '',
      company_name: '',
      responsible_person: ''
    });
  };

  const handleCancel = () => {
    setShowCreateForm(false);
    setEditingUser(null);
    resetForm();
    setError('');
    setSuccess('');
  };

  if (loading) {
    return <div className="loading">Загрузка пользователей...</div>;
  }

  return (
    <div className="user-management">
      <div className="user-management-header">
        <h2>Управление пользователями</h2>
        <button 
          className="create-user-btn"
          onClick={() => setShowCreateForm(true)}
        >
          Создать пользователя
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      {showCreateForm && (
        <div className="create-user-form">
          <h3>{editingUser ? 'Редактировать пользователя' : 'Создать пользователя'}</h3>
          
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label>Логин *</label>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  required
                  disabled={editingUser}
                />
              </div>
              
              <div className="form-group">
                <label>Пароль {editingUser ? '' : '*'}</label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  required={!editingUser}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Роль *</label>
                <select
                  name="role"
                  value={formData.role}
                  onChange={handleChange}
                  required
                >
                  {user.role === 'admin' && <option value="admin">Администратор</option>}
                  {user.role === 'admin' && <option value="employee">Сотрудник</option>}
                  <option value="forwarder">Экспедитор</option>
                  <option value="client">Клиент</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Полное имя</label>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>
              
              <div className="form-group">
                <label>Телефон</label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Название компании</label>
                <input
                  type="text"
                  name="company_name"
                  value={formData.company_name}
                  onChange={handleChange}
                />
              </div>
              
              <div className="form-group">
                <label>Ответственное лицо</label>
                <input
                  type="text"
                  name="responsible_person"
                  value={formData.responsible_person}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="save-btn">
                {editingUser ? 'Обновить' : 'Создать'}
              </button>
              <button type="button" onClick={handleCancel} className="cancel-btn">
                Отмена
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="users-list">
        <h3>Список пользователей</h3>
        <div className="users-table">
          <div className="table-header">
            <div>Логин</div>
            <div>Роль</div>
            <div>Полное имя</div>
            <div>Email</div>
            <div>Компания</div>
            <div>Действия</div>
          </div>
          
          {users.map((userItem) => (
            <div key={userItem.id} className="table-row">
              <div className="username">{userItem.username}</div>
              <div className="role">
                <span className={`role-badge role-${userItem.role}`}>
                  {roleLabels[userItem.role]}
                </span>
                <div className="role-description">
                  {roleDescriptions[userItem.role]}
                </div>
              </div>
              <div className="full-name">{userItem.full_name || '-'}</div>
              <div className="email">{userItem.email || '-'}</div>
              <div className="company">{userItem.company_name || '-'}</div>
              <div className="actions">
                <button 
                  onClick={() => handleEdit(userItem)}
                  className="edit-btn"
                >
                  Редактировать
                </button>
                {userItem.id !== user.id && (
                  <button 
                    onClick={() => handleDelete(userItem.id)}
                    className="delete-btn"
                  >
                    Удалить
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default UserManagement;
