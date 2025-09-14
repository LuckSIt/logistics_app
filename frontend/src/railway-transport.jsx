import React from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API || 'http://127.0.0.1:8000'

function RailwayTransportPage({ token, user }) {
  const [form, setForm] = React.useState({
    transport_type: 'rail',
    basis: 'FOB',
    origin_country: '',
    origin_city: '',
    destination_country: '',
    destination_city: '',
    weight_kg: '',
    volume_m3: '',
    cargo_name: '',
    hs_code: '',
    border_crossing: '',
    customs_clearance: '',
    cargo_ready_date: '',
    vehicle_type: '',
    quantity: '',
    special_conditions: '',
    container_type: '20ft',
    wagon_type: 'container'
  })
  
  const [rows, setRows] = React.useState(null)
  const [isLoading, setIsLoading] = React.useState(false)
  const [currentTime, setCurrentTime] = React.useState(new Date())
  const [selectedItems, setSelectedItems] = React.useState([])

  React.useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    console.log('🚀 Начинаем расчет...', form)
    setIsLoading(true)
    try {
      // Преобразуем данные формы в формат, ожидаемый backend
      const requestData = {
        transport_type: form.transport_type,
        basis: form.basis,
        origin_country: form.origin_country,
        origin_city: form.origin_city,
        destination_country: form.destination_country,
        destination_city: form.destination_city,
        vehicle_type: form.vehicle_type,
        cargo_name: form.cargo_name,
        weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : null,
        volume_m3: form.volume_m3 ? parseFloat(form.volume_m3) : null,
        hs_code: form.hs_code,
        border_point: form.border_crossing,
        customs_point: form.customs_clearance,
        ready_date: form.cargo_ready_date,
        shipments_count: form.quantity ? parseInt(form.quantity) : null,
        special_conditions: form.special_conditions
      }
      
      console.log('📤 Отправляем данные:', requestData)
      
      const res = await axios.post('/calculate', requestData, { 
        baseURL: API_BASE, 
        headers: { Authorization: `Bearer ${token}` } 
      })
      console.log('✅ Получен ответ:', res.data)
      setRows(res.data)
      
      // Сохраняем запрос в историю
      try {
        await axios.post('/requests/save', {
          request_data: requestData
        }, {
          baseURL: API_BASE,
          headers: { Authorization: `Bearer ${token}` }
        })
      } catch (historyError) {
        console.warn('Не удалось сохранить запрос в историю:', historyError)
        // Не показываем ошибку пользователю, так как основной расчет прошел успешно
      }
    } catch (error) {
      console.error('❌ Ошибка расчёта:', error)
      console.error('❌ Детали ошибки:', error.response?.data)
      alert(`Ошибка при расчёте: ${error.response?.data?.detail || error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleItemSelect = (index) => {
    setSelectedItems(prev => 
      prev.includes(index) 
        ? prev.filter(i => i !== index)
        : [...prev, index]
    )
  }

  const downloadKP = async () => {
    if (!rows || selectedItems.length === 0) {
      alert('Выберите тарифы для генерации КП')
      return
    }

    try {
      const selectedTariffs = selectedItems.map(i => rows[i])
      const gen = await axios.post('/offers/generate', { 
        request: { 
          ...form, 
          selected_tariffs: selectedTariffs,
          results: selectedTariffs
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
      a.download = `railway_offer_${offerId}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Ошибка генерации КП:', error)
      alert('Ошибка при генерации КП')
    }
  }

  const renderPrice = (price) => {
    if (!price || price === 'по запросу') return 'по запросу'
    return new Intl.NumberFormat('ru-RU', { 
      style: 'currency', 
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(price)
  }

  return (
    <div className="content">
      <div className="container">
        <div className="card card-pad">
          <div className="header-section">
            <h2 className="title">🚂 Расчёт стоимости доставки</h2>
            <div className="subtitle">Заполните форму для получения тарифов на перевозку груза</div>
          </div>

          <form onSubmit={handleSubmit} className="form-grid">
            <div className="form-section">
              <h3>🚂 Вид доставки и базис</h3>
              <div className="form-group">
                <label>Вид доставки *</label>
                <select
                  value={form.transport_type}
                  onChange={(e) => setForm(prev => ({ ...prev, transport_type: e.target.value }))}
                  required
                >
                  <option value="auto">🚛 Автомобильный</option>
                  <option value="rail">🚂 Железнодорожный</option>
                  <option value="sea">🚢 Морской</option>
                  <option value="air">✈️ Авиа</option>
                  <option value="multimodal">🚢🚂✈️🚛 Мультимодал</option>
                </select>
              </div>
              <div className="form-group">
                <label>Базис поставки *</label>
                <select
                  value={form.basis}
                  onChange={(e) => setForm(prev => ({ ...prev, basis: e.target.value }))}
                  required
                >
                  <option value="EXW">EXW</option>
                  <option value="FCA">FCA</option>
                  <option value="FOB">FOB</option>
                  <option value="CFR">CFR</option>
                  <option value="CIF">CIF</option>
                  <option value="CIP">CIP</option>
                  <option value="CPT">CPT</option>
                  <option value="DAP">DAP</option>
                  <option value="DDP">DDP</option>
                </select>
              </div>
            </div>

            <div className="form-section">
              <h3>📍 Маршрут</h3>
              <div className="form-group">
                <label>Страна отправления *</label>
                <select
                  value={form.origin_country}
                  onChange={(e) => setForm(prev => ({ ...prev, origin_country: e.target.value }))}
                  required
                >
                  <option value="">Выберите страну</option>
                  <option value="RU">🇷🇺 Россия</option>
                  <option value="CN">🇨🇳 Китай</option>
                  <option value="DE">🇩🇪 Германия</option>
                  <option value="US">🇺🇸 США</option>
                  <option value="KZ">🇰🇿 Казахстан</option>
                  <option value="BY">🇧🇾 Беларусь</option>
                  <option value="UZ">🇺🇿 Узбекистан</option>
                  <option value="TR">🇹🇷 Турция</option>
                  <option value="IT">🇮🇹 Италия</option>
                  <option value="FR">🇫🇷 Франция</option>
                </select>
              </div>
              <div className="form-group">
                <label>Город/станция/порт отправления груза *</label>
                <input
                  type="text"
                  value={form.origin_city}
                  onChange={(e) => setForm(prev => ({ ...prev, origin_city: e.target.value }))}
                  placeholder="Москва"
                  required
                />
              </div>
              <div className="form-group">
                <label>Страна доставки *</label>
                <select
                  value={form.destination_country}
                  onChange={(e) => setForm(prev => ({ ...prev, destination_country: e.target.value }))}
                  required
                >
                  <option value="">Выберите страну</option>
                  <option value="RU">🇷🇺 Россия</option>
                  <option value="CN">🇨🇳 Китай</option>
                  <option value="DE">🇩🇪 Германия</option>
                  <option value="US">🇺🇸 США</option>
                  <option value="KZ">🇰🇿 Казахстан</option>
                  <option value="BY">🇧🇾 Беларусь</option>
                  <option value="UZ">🇺🇿 Узбекистан</option>
                  <option value="TR">🇹🇷 Турция</option>
                  <option value="IT">🇮🇹 Италия</option>
                  <option value="FR">🇫🇷 Франция</option>
                </select>
              </div>
              <div className="form-group">
                <label>Город/станция/порт доставки груза *</label>
                <input
                  type="text"
                  value={form.destination_city}
                  onChange={(e) => setForm(prev => ({ ...prev, destination_city: e.target.value }))}
                  placeholder="Санкт-Петербург"
                  required
                />
              </div>
            </div>

            <div className="form-section">
              <h3>📦 Характеристики груза</h3>
              <div className="form-group">
                <label>Наименование груза *</label>
                <input
                  type="text"
                  value={form.cargo_name}
                  onChange={(e) => setForm(prev => ({ ...prev, cargo_name: e.target.value }))}
                  placeholder="Оборудование, товары"
                  required
                />
              </div>
              <div className="form-group">
                <label>Вес, кг *</label>
                <input
                  type="number"
                  value={form.weight_kg}
                  onChange={(e) => setForm(prev => ({ ...prev, weight_kg: e.target.value }))}
                  placeholder="1000"
                  required
                />
              </div>
              <div className="form-group">
                <label>Объём, м³ *</label>
                <input
                  type="number"
                  step="0.1"
                  value={form.volume_m3}
                  onChange={(e) => setForm(prev => ({ ...prev, volume_m3: e.target.value }))}
                  placeholder="5.5"
                  required
                />
              </div>
              <div className="form-group">
                <label>Код ТНВЭД *</label>
                <input
                  type="text"
                  value={form.hs_code}
                  onChange={(e) => setForm(prev => ({ ...prev, hs_code: e.target.value }))}
                  placeholder="1234567890"
                  required
                />
              </div>
            </div>

            <div className="form-section">
              <h3>🛂 Таможенные условия</h3>
              <div className="form-group">
                <label>Погранпереход предпочитаемый</label>
                <input
                  type="text"
                  value={form.border_crossing}
                  onChange={(e) => setForm(prev => ({ ...prev, border_crossing: e.target.value }))}
                  placeholder="Брест, Хасан"
                />
              </div>
              <div className="form-group">
                <label>Место таможенного оформления</label>
                <select
                  value={form.customs_clearance}
                  onChange={(e) => setForm(prev => ({ ...prev, customs_clearance: e.target.value }))}
                >
                  <option value="">По умолчанию</option>
                  <option value="moscow_svh">Московский СВХ</option>
                  <option value="spb_svh">Санкт-Петербургский СВХ</option>
                  <option value="vladivostok_svh">Владивостокский СВХ</option>
                  <option value="novorossiysk_svh">Новороссийский СВХ</option>
                </select>
              </div>
              <div className="form-group">
                <label>Дата готовности груза</label>
                <input
                  type="date"
                  value={form.cargo_ready_date}
                  onChange={(e) => setForm(prev => ({ ...prev, cargo_ready_date: e.target.value }))}
                />
              </div>
            </div>

            <div className="form-section">
              <h3>🚂 Транспорт</h3>
              <div className="form-group">
                <label>Тип транспортной единицы</label>
                <select
                  value={form.vehicle_type}
                  onChange={(e) => setForm(prev => ({ ...prev, vehicle_type: e.target.value }))}
                >
                  <option value="">Выберите тип</option>
                  <option value="tent_20t_82m3">Тент 20т 82м³</option>
                  <option value="tent_20t_90m3">Тент 20т 90м³</option>
                  <option value="tent_20t_110m3">Тент 20т 110м³</option>
                  <option value="tent_20t_120m3">Тент 20т 120м³</option>
                  <option value="40hc">40 HC</option>
                  <option value="20hc">20 HC</option>
                  <option value="40dc">40 DC</option>
                  <option value="20dc">20 DC</option>
                  <option value="40rf">40 RF</option>
                  <option value="20rf">20 RF</option>
                </select>
              </div>
              <div className="form-group">
                <label>Количество партий/авто/контейнеров</label>
                <input
                  type="number"
                  value={form.quantity}
                  onChange={(e) => setForm(prev => ({ ...prev, quantity: e.target.value }))}
                  placeholder="1"
                  min="1"
                />
              </div>
            </div>

            <div className="form-section">
              <h3>⚠️ Особые условия</h3>
              <div className="form-group">
                <label>Особые условия (класс опасности, температура, хрупкость)</label>
                <textarea
                  value={form.special_conditions}
                  onChange={(e) => setForm(prev => ({ ...prev, special_conditions: e.target.value }))}
                  placeholder="Например: Класс опасности 3, температура хранения -18°C, хрупкий груз"
                  rows="3"
                />
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={isLoading}>
                {isLoading ? 'Рассчитываем...' : 'Рассчитать стоимость доставки'}
              </button>
            </div>
          </form>

          <div className="results-section">
            {rows ? (
              <>
                <div className="results-header">
                  <h3>📊 Результаты расчёта</h3>
                  <div className="results-meta">
                    <span>Время расчёта: {currentTime.toLocaleString('ru-RU')}</span>
                    <span>Маршрут: {form.origin_city} → {form.destination_city}</span>
                  </div>
                </div>

                <table className="results-table">
                  <thead>
                    <tr>
                      <th>Выбрать</th>
                      <th>Время</th>
                      <th>Тип доставки</th>
                      <th>Маршрут</th>
                      <th>Базис</th>
                      <th>Стоимость</th>
                      <th>Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Array.isArray(rows) ? rows.map((row, index) => (
                      <tr key={index}>
                        <td>
                          <input
                            type="checkbox"
                            checked={selectedItems.includes(index)}
                            onChange={() => handleItemSelect(index)}
                          />
                        </td>
                        <td>
                          {currentTime.toLocaleString('ru-RU', { 
                            timeZone: 'Europe/Moscow',
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </td>
                        <td>🚂 Железнодорожная доставка</td>
                        <td>{(form.origin_city||'-') + ' → ' + (form.destination_city||'-')}</td>
                        <td>{form.basis || '-'}</td>
                        <td>{renderPrice(row?.final_price_rub || row?.price || 'по запросу')}</td>
                        <td>
                          <button className="btn btn-secondary" onClick={() => {
                            setSelectedItems([index])
                            downloadKP()
                          }}>
                            Скачать КП
                          </button>
                        </td>
                      </tr>
                    )) : (
                      <tr>
                        <td>
                          <input
                            type="checkbox"
                            checked={selectedItems.includes(0)}
                            onChange={() => handleItemSelect(0)}
                          />
                        </td>
                        <td>
                          {currentTime.toLocaleString('ru-RU', { 
                            timeZone: 'Europe/Moscow',
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </td>
                        <td>🚂 Железнодорожная доставка</td>
                        <td>{(form.origin_city||'-') + ' → ' + (form.destination_city||'-')}</td>
                        <td>{form.basis || '-'}</td>
                        <td>{renderPrice(rows?.final_price_rub || rows?.price || 'по запросу')}</td>
                        <td><button className="btn btn-secondary" onClick={downloadKP}>Скачать КП</button></td>
                      </tr>
                    )}
                  </tbody>
                </table>
                
                {selectedItems.length > 0 && (
                  <div className="bulk-actions">
                    <button className="btn btn-primary" onClick={downloadKP}>
                      📄 Скачать КП для выбранных ({selectedItems.length})
                    </button>
                  </div>
                )}

                <div className="notes-section">
                  <div className="note">
                    <strong>💰 Стоимость включает:</strong> Тарификатор жд + СВХ (если выбрано) + автовывоз (если выбрано)
                  </div>
                  <div className="note">
                    <strong>⏱️ Сроки:</strong> Обычно 3-14 дней в зависимости от расстояния и типа груза
                  </div>
                  <div className="note">
                    <strong>📋 Документы:</strong> ЖД накладная, документы на груз, сертификаты
                  </div>
                  <div className="note">
                    <strong>🚛 Дополнительно:</strong> Возможна доставка до двери с использованием автомобильного транспорта
                  </div>
                </div>
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>
                {isLoading ? (
                  '🚂 Рассчитываем стоимость железнодорожной доставки...'
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
                    <span>Заполните форму и нажмите "Рассчитать" для получения тарифов</span>
                    <span style={{ fontSize: '12px', color: '#888' }}>
                      {currentTime.toLocaleString('ru-RU', { 
                        timeZone: 'Europe/Moscow',
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                      })}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default RailwayTransportPage
