import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './MarkupManagement.css';

const MarkupManagement = ({ user }) => {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [editingSupplier, setEditingSupplier] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [supplierToDelete, setSupplierToDelete] = useState(null);

  const [supplierForm, setSupplierForm] = useState({
    markup_percent: 0,
    markup_fixed: 0
  });

  const [createForm, setCreateForm] = useState({
    supplier_id: '',
    markup_percent: 0,
    markup_fixed: 0
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const suppliersRes = await axios.get('/suppliers/', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });

      setSuppliers(suppliersRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка загрузки данных');
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
      await axios.patch(`/suppliers/${editingSupplier.id}/markup`, null, {
        params: {
          markup_percent: supplierForm.markup_percent,
          markup_fixed: supplierForm.markup_fixed
        },
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      setSuccess('Наценки поставщика обновлены');
      setEditingSupplier(null);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка обновления наценок');
    }
  };

  const handleCreateMarkup = async () => {
    try {
      await axios.patch(`/suppliers/${createForm.supplier_id}/markup`, null, {
        params: {
          markup_percent: createForm.markup_percent,
          markup_fixed: createForm.markup_fixed
        },
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      setSuccess('Наценка установлена');
      setShowCreateForm(false);
      resetCreateForm();
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка установки наценки');
    }
  };

  const resetCreateForm = () => {
    setCreateForm({
      supplier_id: '',
      markup_percent: 0,
      markup_fixed: 0
    });
  };

  const handleDeleteMarkup = (supplier) => {
    setSupplierToDelete(supplier);
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    try {
      await axios.delete(`/suppliers/${supplierToDelete.id}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      setSuccess('Поставщик удален');
      setShowDeleteConfirm(false);
      setSupplierToDelete(null);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка удаления поставщика');
    }
  };

  const cancelDelete = () => {
    setShowDeleteConfirm(false);
    setSupplierToDelete(null);
  };







  if (loading) {
    return <div className="loading">Загрузка данных...</div>;
  }

  return (
    <div className="markup-management">
      <div className="markup-header">
        <h2>Управление наценками поставщиков</h2>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

        <div className="suppliers-section">
          <div className="suppliers-header">
            <h3>Наценки поставщиков</h3>
            <button 
              onClick={() => setShowCreateForm(true)}
              className="create-supplier-btn"
            >
              Установить наценку
            </button>
          </div>

          {showCreateForm && (
            <div className="create-form">
              <h4>Установить наценку для поставщика</h4>
              <div className="form-row">
                <div className="form-group">
                  <label>Выберите поставщика *</label>
                  <select
                    value={createForm.supplier_id}
                    onChange={(e) => setCreateForm({
                      ...createForm,
                      supplier_id: e.target.value
                    })}
                    required
                  >
                    <option value="">Выберите поставщика</option>
                    {suppliers.map(supplier => (
                      <option key={supplier.id} value={supplier.id}>
                        {supplier.name} {supplier.contact_person ? `(${supplier.contact_person})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Наценка в %</label>
                  <input
                    type="number"
                    step="0.01"
                    value={createForm.markup_percent}
                    onChange={(e) => setCreateForm({
                      ...createForm,
                      markup_percent: parseFloat(e.target.value) || 0
                    })}
                  />
                </div>
                <div className="form-group">
                  <label>Фиксированная наценка (руб.)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={createForm.markup_fixed}
                    onChange={(e) => setCreateForm({
                      ...createForm,
                      markup_fixed: parseFloat(e.target.value) || 0
                    })}
                  />
                </div>
              </div>
              <div className="form-actions">
                <button onClick={handleCreateMarkup} className="save-btn">
                  Установить наценку
                </button>
                <button 
                  onClick={() => {
                    setShowCreateForm(false);
                    resetCreateForm();
                  }} 
                  className="cancel-btn"
                >
                  Отмена
                </button>
              </div>
            </div>
          )}

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
                    <div className="supplier-actions">
                      <button 
                        onClick={() => handleSupplierEdit(supplier)}
                        className="edit-btn"
                      >
                        Редактировать
                      </button>
                      <button 
                        onClick={() => handleDeleteMarkup(supplier)}
                        className="delete-btn"
                      >
                        Удалить поставщика
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Модальное окно подтверждения удаления */}
        {showDeleteConfirm && (
          <div className="modal-overlay">
            <div className="modal-content">
              <div className="modal-header">
                <h3>Подтверждение удаления</h3>
              </div>
              <div className="modal-body">
                <p>Вы уверены, что хотите удалить поставщика <strong>"{supplierToDelete?.name}"</strong>?</p>
                <p className="warning-text">Это действие нельзя отменить.</p>
              </div>
              <div className="modal-actions">
                <button onClick={cancelDelete} className="cancel-btn">
                  Отмена
                </button>
                <button onClick={confirmDelete} className="delete-btn">
                  Удалить
                </button>
              </div>
            </div>
          </div>
        )}
    </div>
  );
};

export default MarkupManagement;
