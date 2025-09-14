import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './MarkupManagement.css';

const MarkupManagement = ({ user }) => {
  const [suppliers, setSuppliers] = useState([]);
  const [discounts, setDiscounts] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('suppliers');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [editingSupplier, setEditingSupplier] = useState(null);
  const [editingDiscount, setEditingDiscount] = useState(null);
  const [showDiscountForm, setShowDiscountForm] = useState(false);

  const [supplierForm, setSupplierForm] = useState({
    markup_percent: 0,
    markup_fixed: 0
  });

  const [discountForm, setDiscountForm] = useState({
    user_id: '',
    supplier_id: '',
    discount_percent: 0
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [suppliersRes, discountsRes, usersRes] = await Promise.all([
        axios.get('/markups/suppliers', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        axios.get('/markups/discounts', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        axios.get('/users/', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
      ]);

      setSuppliers(suppliersRes.data);
      setDiscounts(discountsRes.data);
      setUsers(usersRes.data);
    } catch (err) {
      setError('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const handleSupplierEdit = (supplier) => {
    setEditingSupplier(supplier);
    setSupplierForm({
      markup_percent: supplier.markup_percent || 0,
      markup_fixed: supplier.markup_fixed || 0
    });
  };

  const handleSupplierSave = async () => {
    try {
      await axios.put(`/markups/suppliers/${editingSupplier.id}/markup`, supplierForm, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      setSuccess('Наценки поставщика обновлены');
      setEditingSupplier(null);
      fetchData();
    } catch (err) {
      setError('Ошибка обновления наценок');
    }
  };

  const handleDiscountSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingDiscount) {
        await axios.put(`/markups/discounts/${editingDiscount.id}`, {
          discount_percent: discountForm.discount_percent
        }, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        setSuccess('Скидка обновлена');
      } else {
        await axios.post('/markups/discounts', discountForm, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        setSuccess('Скидка создана');
      }
      setShowDiscountForm(false);
      setEditingDiscount(null);
      resetDiscountForm();
      fetchData();
    } catch (err) {
      setError('Ошибка сохранения скидки');
    }
  };

  const handleDiscountEdit = (discount) => {
    setEditingDiscount(discount);
    setDiscountForm({
      user_id: discount.user_id,
      supplier_id: discount.supplier_id,
      discount_percent: discount.discount_percent
    });
    setShowDiscountForm(true);
  };

  const handleDiscountDelete = async (discountId) => {
    if (!window.confirm('Удалить скидку?')) return;
    
    try {
      await axios.delete(`/markups/discounts/${discountId}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      setSuccess('Скидка удалена');
      fetchData();
    } catch (err) {
      setError('Ошибка удаления скидки');
    }
  };

  const resetDiscountForm = () => {
    setDiscountForm({
      user_id: '',
      supplier_id: '',
      discount_percent: 0
    });
  };

  const getUserName = (userId) => {
    const user = users.find(u => u.id === userId);
    return user ? (user.full_name || user.username) : 'Неизвестный пользователь';
  };

  const getSupplierName = (supplierId) => {
    const supplier = suppliers.find(s => s.id === supplierId);
    return supplier ? supplier.name : 'Неизвестный поставщик';
  };

  if (loading) {
    return <div className="loading">Загрузка данных...</div>;
  }

  return (
    <div className="markup-management">
      <div className="markup-header">
        <h2>Управление наценками и скидками</h2>
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'suppliers' ? 'active' : ''}`}
            onClick={() => setActiveTab('suppliers')}
          >
            Наценки поставщиков
          </button>
          <button 
            className={`tab ${activeTab === 'discounts' ? 'active' : ''}`}
            onClick={() => setActiveTab('discounts')}
          >
            Скидки пользователей
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      {activeTab === 'suppliers' && (
        <div className="suppliers-section">
          <h3>Наценки поставщиков</h3>
          <div className="suppliers-list">
            {suppliers.map(supplier => (
              <div key={supplier.id} className="supplier-card">
                <div className="supplier-info">
                  <h4>{supplier.name}</h4>
                  <p>{supplier.contact_person || 'Контактное лицо не указано'}</p>
                </div>
                
                {editingSupplier?.id === supplier.id ? (
                  <div className="edit-form">
                    <div className="form-group">
                      <label>Наценка в %</label>
                      <input
                        type="number"
                        step="0.01"
                        value={supplierForm.markup_percent}
                        onChange={(e) => setSupplierForm({
                          ...supplierForm,
                          markup_percent: parseFloat(e.target.value) || 0
                        })}
                      />
                    </div>
                    <div className="form-group">
                      <label>Фиксированная наценка (руб.)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={supplierForm.markup_fixed}
                        onChange={(e) => setSupplierForm({
                          ...supplierForm,
                          markup_fixed: parseFloat(e.target.value) || 0
                        })}
                      />
                    </div>
                    <div className="form-actions">
                      <button onClick={handleSupplierSave} className="save-btn">
                        Сохранить
                      </button>
                      <button 
                        onClick={() => setEditingSupplier(null)} 
                        className="cancel-btn"
                      >
                        Отмена
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="supplier-markup">
                    <div className="markup-info">
                      <span>Наценка: {supplier.markup_percent || 0}%</span>
                      <span>Фиксированная: {supplier.markup_fixed || 0} руб.</span>
                    </div>
                    <button 
                      onClick={() => handleSupplierEdit(supplier)}
                      className="edit-btn"
                    >
                      Редактировать
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'discounts' && (
        <div className="discounts-section">
          <div className="discounts-header">
            <h3>Скидки пользователей</h3>
            <button 
              onClick={() => setShowDiscountForm(true)}
              className="create-discount-btn"
            >
              Создать скидку
            </button>
          </div>

          {showDiscountForm && (
            <div className="discount-form">
              <h4>{editingDiscount ? 'Редактировать скидку' : 'Создать скидку'}</h4>
              <form onSubmit={handleDiscountSubmit}>
                <div className="form-row">
                  <div className="form-group">
                    <label>Пользователь *</label>
                    <select
                      value={discountForm.user_id}
                      onChange={(e) => setDiscountForm({
                        ...discountForm,
                        user_id: parseInt(e.target.value)
                      })}
                      required
                    >
                      <option value="">Выберите пользователя</option>
                      {users.map(user => (
                        <option key={user.id} value={user.id}>
                          {user.full_name || user.username} ({user.role})
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label>Поставщик *</label>
                    <select
                      value={discountForm.supplier_id}
                      onChange={(e) => setDiscountForm({
                        ...discountForm,
                        supplier_id: parseInt(e.target.value)
                      })}
                      required
                    >
                      <option value="">Выберите поставщика</option>
                      {suppliers.map(supplier => (
                        <option key={supplier.id} value={supplier.id}>
                          {supplier.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label>Размер скидки (%) *</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="100"
                      value={discountForm.discount_percent}
                      onChange={(e) => setDiscountForm({
                        ...discountForm,
                        discount_percent: parseFloat(e.target.value) || 0
                      })}
                      required
                    />
                  </div>
                </div>
                
                <div className="form-actions">
                  <button type="submit" className="save-btn">
                    {editingDiscount ? 'Обновить' : 'Создать'}
                  </button>
                  <button 
                    type="button" 
                    onClick={() => {
                      setShowDiscountForm(false);
                      setEditingDiscount(null);
                      resetDiscountForm();
                    }}
                    className="cancel-btn"
                  >
                    Отмена
                  </button>
                </div>
              </form>
            </div>
          )}

          <div className="discounts-list">
            {discounts.map(discount => (
              <div key={discount.id} className="discount-card">
                <div className="discount-info">
                  <div className="discount-user">
                    <strong>{getUserName(discount.user_id)}</strong>
                    <span>скидка у</span>
                    <strong>{getSupplierName(discount.supplier_id)}</strong>
                  </div>
                  <div className="discount-percent">
                    {discount.discount_percent}%
                  </div>
                </div>
                <div className="discount-actions">
                  <button 
                    onClick={() => handleDiscountEdit(discount)}
                    className="edit-btn"
                  >
                    Редактировать
                  </button>
                  <button 
                    onClick={() => handleDiscountDelete(discount.id)}
                    className="delete-btn"
                  >
                    Удалить
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MarkupManagement;
