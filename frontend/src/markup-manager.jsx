import React from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function MarkupManager({ token, suppliers, onUpdate }) {
  const [editingId, setEditingId] = React.useState(null)
  const [editForm, setEditForm] = React.useState({})
  const [loading, setLoading] = React.useState(false)
  const [message, setMessage] = React.useState('')

  const handleEdit = (supplier) => {
    setEditingId(supplier.id)
    setEditForm({
      markup_percent: supplier.markup_percent || 0,
      markup_fixed: supplier.markup_fixed || 0
    })
    setMessage('')
  }

  const handleSave = async () => {
    if (!editingId) return
    
    setLoading(true)
    setMessage('')
    
    try {
      await axios.patch(`/suppliers/${editingId}/markup/client`, editForm, {
        baseURL: API_BASE,
        headers: { Authorization: `Bearer ${token}` }
      })
      
      setMessage('✅ Наценка успешно обновлена!')
      setEditingId(null)
      setEditForm({})
      
      // Обновляем список поставщиков
      if (onUpdate) {
        onUpdate()
      }
      
    } catch (error) {
      console.error('Ошибка обновления наценки:', error)
      const errorMsg = error.response?.data?.detail || error.message
      setMessage(`❌ Ошибка: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    setEditingId(null)
    setEditForm({})
    setMessage('')
  }

  const handleInputChange = (field, value) => {
    setEditForm(prev => ({
      ...prev,
      [field]: value
    }))
  }

  return (
    <div className="markup-manager">
      <h3>Управление наценками</h3>
      <p className="help-text">
        Установите процентную и фиксированную наценку для каждого поставщика. 
        Наценки применяются автоматически при расчете стоимости.
      </p>
      
      {message && (
        <div className={`message ${message.includes('✅') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}
      
      <div className="markup-table">
        <table>
          <thead>
            <tr>
              <th>Поставщик</th>
              <th>Процентная наценка (%)</th>
              <th>Фиксированная наценка (₽)</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {suppliers.map(supplier => (
              <tr key={supplier.id}>
                <td>{supplier.name}</td>
                <td>
                  {editingId === supplier.id ? (
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="100"
                      value={editForm.markup_percent}
                      onChange={(e) => handleInputChange('markup_percent', parseFloat(e.target.value) || 0)}
                      className="markup-input"
                      placeholder="0"
                    />
                  ) : (
                    <span className={supplier.markup_percent > 0 ? 'highlight' : ''}>
                      {supplier.markup_percent || 0}%
                    </span>
                  )}
                </td>
                <td>
                  {editingId === supplier.id ? (
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={editForm.markup_fixed}
                      onChange={(e) => handleInputChange('markup_fixed', parseFloat(e.target.value) || 0)}
                      className="markup-input"
                      placeholder="0"
                    />
                  ) : (
                    <span className={supplier.markup_fixed > 0 ? 'highlight' : ''}>
                      {supplier.markup_fixed || 0} ₽
                    </span>
                  )}
                </td>
                <td>
                  {editingId === supplier.id ? (
                    <div className="action-buttons">
                      <button 
                        onClick={handleSave} 
                        disabled={loading}
                        className="btn btn-primary btn-sm"
                      >
                        {loading ? 'Сохранение...' : 'Сохранить'}
                      </button>
                      <button 
                        onClick={handleCancel}
                        className="btn btn-secondary btn-sm"
                      >
                        Отмена
                      </button>
                    </div>
                  ) : (
                    <button 
                      onClick={() => handleEdit(supplier)}
                      className="btn btn-outline btn-sm"
                    >
                      Изменить
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="markup-info">
        <h4>Как работают наценки:</h4>
        <ul>
          <li><strong>Процентная наценка:</strong> применяется к базовой стоимости (например, 10% = +10% к цене)</li>
          <li><strong>Фиксированная наценка:</strong> добавляется к итоговой стоимости в рублях</li>
          <li><strong>Формула расчета:</strong> Итоговая цена = (Базовая цена × (1 + % наценки)) + Фиксированная наценка</li>
          <li>Наценки применяются автоматически при расчете коммерческих предложений</li>
        </ul>
      </div>
    </div>
  )
}

export default MarkupManager
