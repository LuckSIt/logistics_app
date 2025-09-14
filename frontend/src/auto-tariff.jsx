import React from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API || 'http://127.0.0.1:8000'

function AutoTariffPage({ token }) {
  const [suppliers, setSuppliers] = React.useState([])
  const [supplierId, setSupplierId] = React.useState('')
  const [transportType, setTransportType] = React.useState('auto')  // Добавляем тип транспорта
  const [file, setFile] = React.useState(null)
  const [isLoading, setIsLoading] = React.useState(false)
  const [extractedData, setExtractedData] = React.useState(null)
  const [message, setMessage] = React.useState('')
  const [useLLM, setUseLLM] = React.useState(false)  // Флаг для использования LLM парсера
  const [llmModel, setLlmModel] = React.useState('mistral')  // Модель LLM
  const [availableModels, setAvailableModels] = React.useState(['mistral'])  // Доступные модели
  const [supportedFormats, setSupportedFormats] = React.useState([])
  const [selectedTransport, setSelectedTransport] = React.useState(null)
  const [showCreateSupplier, setShowCreateSupplier] = React.useState(false)
  const [newSupplier, setNewSupplier] = React.useState({
    name: '',
    contact_person: '',
    contact_email: '',
    contact_phone: ''
  })

  // Загружаем поставщиков и поддерживаемые форматы при монтировании компонента
  React.useEffect(() => {
    loadSuppliers()
    loadSupportedFormats()
    loadAvailableModels()
  }, [])

  const loadAvailableModels = async () => {
    try {
      const response = await axios.get('/llm-parser/models', {
        baseURL: API_BASE,
        headers: { Authorization: `Bearer ${token}` }
      })
      setAvailableModels(response.data.available_models || ['mistral'])
    } catch (error) {
      console.error('Ошибка загрузки моделей:', error)
      setAvailableModels(['mistral'])
    }
  }

  const loadSuppliers = async () => {
    try {
      const response = await axios.get('/suppliers/', {
        baseURL: API_BASE,
        headers: { Authorization: `Bearer ${token}` }
      })
      setSuppliers(response.data)
    } catch (error) {
      console.error('Ошибка загрузки поставщиков:', error)
    }
  }

  const loadSupportedFormats = async () => {
    try {
      const response = await axios.get('/auto-tariff/supported-formats', {
        baseURL: API_BASE,
        headers: { Authorization: `Bearer ${token}` }
      })
      setSupportedFormats(response.data.supported_formats)
    } catch (error) {
      console.error('Ошибка загрузки поддерживаемых форматов:', error)
    }
  }

  const handleCreateSupplier = async () => {
    if (!newSupplier.name.trim()) {
      alert('Введите название поставщика')
      return
    }

    setIsLoading(true)
    setMessage('')

    try {
      const response = await axios.post('/suppliers/client', newSupplier, {
        baseURL: API_BASE,
        headers: { Authorization: `Bearer ${token}` }
      })

      // Добавляем нового поставщика в список
      setSuppliers(prev => [...prev, response.data])
      setSupplierId(response.data.id.toString())
      setShowCreateSupplier(false)
      setNewSupplier({ name: '', contact_person: '', contact_email: '', contact_phone: '' })
      setMessage('Поставщик успешно создан!')
    } catch (error) {
      console.error('Ошибка создания поставщика:', error)
      const errorMsg = error.response?.data?.detail || error.message
      setMessage(`Ошибка создания поставщика: ${errorMsg}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileSelect = (event) => {
    const selectedFile = event.target.files?.[0]
    setFile(selectedFile)
    
    // Автоматически извлекаем название поставщика из имени файла
    if (selectedFile) {
      const fileName = selectedFile.name
      const nameWithoutExt = fileName.split('.').slice(0, -1).join('.')
      
      // Убираем временные файлы Excel
      if (!nameWithoutExt.startsWith('~$') && nameWithoutExt.trim().length > 2) {
        const extractedName = nameWithoutExt.trim()
        
        // Проверяем, есть ли уже такой поставщик
        const existingSupplier = suppliers.find(s => 
          s.name.toLowerCase() === extractedName.toLowerCase()
        )
        
        if (!existingSupplier) {
          // Предлагаем создать нового поставщика
          setNewSupplier(prev => ({ ...prev, name: extractedName }))
          setShowCreateSupplier(true)
        } else {
          // Выбираем существующего поставщика
          setSupplierId(existingSupplier.id.toString())
        }
      }
    }
  }

  const handleTransportSelect = (transport) => {
    setSelectedTransport(transport)
    setTransportType(transport.id)
  }

  const handleExtractData = async () => {
    if (!supplierId || !file) {
      alert('Выберите поставщика и файл')
      return
    }

    setIsLoading(true)
    setMessage('')
    setExtractedData(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('supplier_id', supplierId)
      formData.append('transport_type', transportType)
      
      // Добавляем параметры LLM если используется
      if (useLLM) {
        formData.append('use_llm', 'true')
        formData.append('llm_model', llmModel)
      }

      // Выбираем эндпоинт в зависимости от типа парсера
      const endpoint = useLLM ? '/llm-parser/upload' : '/auto-tariff/extract-tariff-data'

      const response = await axios.post(endpoint, formData, {
        baseURL: API_BASE,
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      })

      console.log('API Response:', response.data) // Отладочная информация
      
      // Обрабатываем ответ в зависимости от типа парсера
      if (useLLM) {
        // LLM парсер возвращает данные в другом формате
        const llmData = {
          tariff_data: {
            transport_type: transportType,
            basis: 'EXW',
            routes: response.data.data || []
          }
        }
        setExtractedData(llmData)
        setMessage(`LLM (${llmModel}) успешно извлек ${response.data.parsed_rows} записей из файла`)
      } else {
        setExtractedData(response.data)
        setMessage('Данные успешно извлечены из файла')
      }
    } catch (error) {
      console.error('Ошибка извлечения данных:', error)
      const errorMsg = error.response?.data?.detail || error.message
      setMessage(`Ошибка: ${errorMsg}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveTariff = async (tariffData) => {
    setIsLoading(true)
    setMessage('')

    try {
      // Сохраняем каждый маршрут как отдельный тариф
      const savedTariffs = []
      
      for (const route of tariffData.routes) {
        const routeTariffData = {
          ...tariffData,
          ...route,  // Добавляем данные маршрута
          supplier_id: parseInt(supplierId),
          source_file: extractedData.filename
        }
        
        // Удаляем routes из данных тарифа, так как это не поле базы данных
        delete routeTariffData.routes
        
        const response = await axios.post('/auto-tariff/save-tariff', routeTariffData, {
          baseURL: API_BASE,
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })
        
        savedTariffs.push(response.data.tariff_id)
      }

      setMessage(`Успешно сохранено ${savedTariffs.length} тарифов! ID: ${savedTariffs.join(', ')}`)
      setExtractedData(null)
      setFile(null)
      setSelectedTransport(null)
      // Очищаем input файла
      const fileInput = document.querySelector('input[type="file"]')
      if (fileInput) fileInput.value = ''
    } catch (error) {
      console.error('Ошибка сохранения тарифа:', error)
      const errorMsg = error.response?.data?.detail || error.message
      setMessage(`Ошибка сохранения: ${errorMsg}`)
    } finally {
      setIsLoading(false)
    }
  }

  const updateTariffField = (field, value) => {
    if (!extractedData) return
    
    setExtractedData(prev => ({
      ...prev,
      tariff_data: {
        ...prev.tariff_data,
        [field]: value
      }
    }))
  }

  const updateRouteField = (routeIndex, field, value) => {
    if (!extractedData) return
    
    setExtractedData(prev => ({
      ...prev,
      tariff_data: {
        ...prev.tariff_data,
        routes: prev.tariff_data.routes.map((route, index) => 
          index === routeIndex ? { ...route, [field]: value } : route
        )
      }
    }))
  }

  const addRoute = () => {
    if (!extractedData) return
    
    const newRoute = {
      origin_country: "Россия",
      origin_city: "",
      destination_country: "Россия",
      destination_city: "",
      price_rub: null,
      price_usd: null,
      transit_time_days: null
    }
    
    setExtractedData(prev => ({
      ...prev,
      tariff_data: {
        ...prev.tariff_data,
        routes: [...prev.tariff_data.routes, newRoute]
      }
    }))
  }

  const removeRoute = (routeIndex) => {
    if (!extractedData) return
    
    setExtractedData(prev => ({
      ...prev,
      tariff_data: {
        ...prev.tariff_data,
        routes: prev.tariff_data.routes.filter((_, index) => index !== routeIndex)
      }
    }))
  }

  const formatDate = (date) => {
    if (!date) return ''
    if (typeof date === 'string') return date
    if (date instanceof Date) {
      return date.toISOString().split('T')[0]
    }
    return date
  }

  const transportTypes = [
    {
      id: 'auto',
      title: '🚛 Автомобильные перевозки',
      subtitle: 'FTL и LTL доставка',
      description: 'Автоматическое создание тарифов для автомобильных перевозок. Подходит для файлов с данными о грузовиках, фурах и автомобильных маршрутах.',
      features: [
        'Парсинг тарифов грузовиков',
        'FTL и LTL перевозки',
        'Автомобильные маршруты',
        'Типы ТС: тенты, рефрижераторы'
      ],
      color: '#4CAF50'
    },
    {
      id: 'rail',
      title: '🚂 Железнодорожные перевозки',
      subtitle: 'Контейнерные и вагонные перевозки',
      description: 'Создание тарифов для железнодорожных перевозок. Обработка данных о контейнерах, вагонах и ж/д маршрутах.',
      features: [
        'Контейнерные перевозки',
        'Вагонные перевозки',
        'Железнодорожные маршруты',
        'Типы ТС: 20/40 НС, вагоны'
      ],
      color: '#FF9800'
    },
    {
      id: 'sea',
      title: '🚢 Морские перевозки',
      subtitle: 'FCL, LCL и навалочные грузы',
      description: 'Автоматическое создание тарифов для морских перевозок. Обработка данных о контейнерных и навалочных грузах.',
      features: [
        'FCL и LCL перевозки',
        'Навалочные грузы',
        'Морские маршруты',
        'Портовые услуги'
      ],
      color: '#2196F3'
    },
    {
      id: 'air',
      title: '✈️ Авиаперевозки',
      subtitle: 'Express и стандартная доставка',
      description: 'Создание тарифов для авиационных перевозок. Обработка данных о воздушных маршрутах и авиационных услугах.',
      features: [
        'Express доставка',
        'Стандартная доставка',
        'Авиационные маршруты',
        'Авиационные сборы'
      ],
      color: '#9C27B0'
    },
    {
      id: 'multimodal',
      title: '🚢🚂✈️🚛 Мультимодальные перевозки',
      subtitle: 'Комбинированная доставка',
      description: 'Автоматическое создание тарифов для мультимодальных перевозок. Обработка сложных комбинированных маршрутов.',
      features: [
        'Море + Железная дорога',
        'Самолёт + Автомобиль',
        'Комбинированные маршруты',
        'Оптимизация стоимости'
      ],
      color: '#607D8B'
    }
  ]

  // Если выбран тип транспорта, показываем форму загрузки
  if (selectedTransport) {
    return (
      <div className="content">
        <div className="container">
          <div className="card card-pad" style={{ maxWidth: 1200 }}>
            <div className="header-section">
              <button 
                className="btn btn-secondary" 
                onClick={() => setSelectedTransport(null)}
                style={{ marginBottom: 20 }}
              >
                ← Назад к выбору транспорта
              </button>
              <h2 className="title">🤖 Автоматическое создание тарифов</h2>
              <div className="subtitle">Выбран тип транспорта: {selectedTransport.title}</div>
            </div>

            {/* Информация о поддерживаемых форматах */}
            <div style={{ marginBottom: 20, padding: 15, backgroundColor: 'var(--muted-surface)', borderRadius: 'var(--radius)' }}>
              <h3 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>Поддерживаемые форматы</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {supportedFormats.map(format => (
                  <span key={format} style={{ 
                    padding: '4px 8px', 
                    backgroundColor: 'var(--primary)', 
                    color: 'white', 
                    borderRadius: '4px', 
                    fontSize: '12px' 
                  }}>
                    {format}
                  </span>
                ))}
              </div>
              <p style={{ margin: '10px 0 0 0', fontSize: '14px', color: 'var(--text-muted)' }}>
                Система автоматически извлечет данные из файла и заполнит форму создания тарифа
              </p>
            </div>

            {/* Информация о создании поставщиков */}
            <div style={{ marginBottom: 20, padding: 15, backgroundColor: 'var(--success-surface)', borderRadius: 'var(--radius)', border: '1px solid var(--success)' }}>
              <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: 'var(--success)' }}>💡 Создание поставщиков</h3>
              <p style={{ margin: '0 0 8px 0', fontSize: '14px', color: 'var(--text)' }}>
                Если нужного поставщика нет в списке, вы можете создать нового:
              </p>
              <ul style={{ margin: '0 0 8px 0', fontSize: '14px', color: 'var(--text)', paddingLeft: '20px' }}>
                <li>Нажмите кнопку <strong>"+ Новый"</strong> рядом с выбором поставщика</li>
                <li>Заполните форму с контактной информацией</li>
                <li>Система автоматически извлечет название из имени файла</li>
                <li>После создания поставщик будет автоматически выбран</li>
              </ul>
              <p style={{ margin: '0', fontSize: '12px', color: 'var(--text-muted)' }}>
                <strong>Примечание:</strong> Созданные поставщики будут доступны для всех пользователей системы
              </p>
            </div>

            {/* Секция загрузки файла */}
            <div className="form-section">
              <h4>📁 Загрузка файла</h4>
              <div className="section-description">
                Выберите поставщика и файл для автоматического извлечения данных тарифа
              </div>
              
              <div style={{ marginBottom: 16 }}>
                <div style={{ marginBottom: 12 }}>
                  <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>Поставщик:</label>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
                    <select 
                      value={supplierId} 
                      onChange={e => setSupplierId(e.target.value)}
                      style={{ flex: 1, padding: '8px 12px', borderRadius: '4px', border: '1px solid var(--border)' }}
                    >
                      <option value="">Выберите поставщика</option>
                      {suppliers.map(s => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                    </select>
                    <button 
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => setShowCreateSupplier(!showCreateSupplier)}
                      style={{ whiteSpace: 'nowrap' }}
                    >
                      {showCreateSupplier ? 'Отмена' : '+ Новый'}
                    </button>
                  </div>
                </div>

                {/* Форма создания нового поставщика */}
                {showCreateSupplier && (
                  <div style={{ 
                    marginBottom: 16, 
                    padding: 16, 
                    backgroundColor: 'var(--muted-surface)', 
                    borderRadius: 'var(--radius)',
                    border: '1px solid var(--border)'
                  }}>
                    <h4 style={{ margin: '0 0 12px 0', fontSize: '14px' }}>Создать нового поставщика</h4>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                      <div>
                        <label style={{ display: 'block', marginBottom: 4, fontSize: '12px', fontWeight: 500 }}>
                          Название поставщика *
                        </label>
                        <input
                          type="text"
                          value={newSupplier.name}
                          onChange={e => setNewSupplier(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="Введите название компании"
                          style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '12px' }}
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', marginBottom: 4, fontSize: '12px', fontWeight: 500 }}>
                          Контактное лицо
                        </label>
                        <input
                          type="text"
                          value={newSupplier.contact_person}
                          onChange={e => setNewSupplier(prev => ({ ...prev, contact_person: e.target.value }))}
                          placeholder="ФИО контактного лица"
                          style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '12px' }}
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', marginBottom: 4, fontSize: '12px', fontWeight: 500 }}>
                          Email
                        </label>
                        <input
                          type="email"
                          value={newSupplier.contact_email}
                          onChange={e => setNewSupplier(prev => ({ ...prev, contact_email: e.target.value }))}
                          placeholder="email@example.com"
                          style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '12px' }}
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', marginBottom: 4, fontSize: '12px', fontWeight: 500 }}>
                          Телефон
                        </label>
                        <input
                          type="tel"
                          value={newSupplier.contact_phone}
                          onChange={e => setNewSupplier(prev => ({ ...prev, contact_phone: e.target.value }))}
                          placeholder="+7 (999) 123-45-67"
                          style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '12px' }}
                        />
                      </div>
                    </div>
                    <div style={{ marginTop: 12, display: 'flex', gap: '8px' }}>
                      <button 
                        type="button"
                        className="btn btn-primary"
                        onClick={handleCreateSupplier}
                        disabled={isLoading}
                        style={{ fontSize: '12px' }}
                      >
                        {isLoading ? 'Создание...' : 'Создать поставщика'}
                      </button>
                      <button 
                        type="button"
                        className="btn btn-secondary"
                        onClick={() => {
                          setShowCreateSupplier(false)
                          setNewSupplier({ name: '', contact_person: '', contact_email: '', contact_phone: '' })
                        }}
                        style={{ fontSize: '12px' }}
                      >
                        Отмена
                      </button>
                    </div>
                  </div>
                )}
                
                <div style={{ marginBottom: 12 }}>
                  <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>Файл:</label>
                  <input 
                    type="file" 
                    onChange={handleFileSelect}
                    accept={supportedFormats.join(',')}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '4px', border: '1px solid var(--border)' }}
                  />
                </div>

                {/* LLM Parser Options */}
                <div style={{ 
                  marginBottom: 12, 
                  padding: '12px 16px', 
                  backgroundColor: 'var(--muted-surface)', 
                  borderRadius: 'var(--radius)', 
                  border: '1px solid var(--border)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                    <input
                      type="checkbox"
                      id="useLLM"
                      checked={useLLM}
                      onChange={(e) => setUseLLM(e.target.checked)}
                      style={{ marginRight: 10 }}
                    />
                    <label htmlFor="useLLM" style={{ fontWeight: 500, cursor: 'pointer', color: 'var(--text)', fontSize: '14px' }}>
                      Использовать LLM‑парсер (Ollama)
                    </label>
                  </div>
                  
                  {useLLM && (
                    <div style={{ marginLeft: 28 }}>
                      <label style={{ display: 'block', marginBottom: 4, fontSize: '13px', color: 'var(--text-muted)' }}>Модель LLM:</label>
                      <select
                        value={llmModel}
                        onChange={(e) => setLlmModel(e.target.value)}
                        style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '14px', backgroundColor: 'var(--surface)', color: 'var(--text)' }}
                      >
                        {availableModels.map(model => (
                          <option key={model} value={model}>{model}</option>
                        ))}
                      </select>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 4 }}>
                        LLM‑парсер использует ИИ для извлечения данных из документов
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="toolbar">
                  <button 
                    className="btn btn-primary" 
                    onClick={handleExtractData}
                    disabled={isLoading || !supplierId || !file}
                    style={{ backgroundColor: selectedTransport.color, borderColor: selectedTransport.color }}
                  >
                    {isLoading ? 'Извлекаем данные...' : 'Извлечь данные из файла'}
                  </button>
                </div>
              </div>

              {message && (
                <div style={{ 
                  padding: 12, 
                  borderRadius: '4px', 
                  backgroundColor: message.includes('Ошибка') ? '#fee' : '#efe',
                  color: message.includes('Ошибка') ? '#c33' : '#363',
                  marginBottom: 16
                }}>
                  {message}
                </div>
              )}
            </div>

            {/* Результаты извлечения и форма редактирования */}
            {extractedData && (
              <div className="form-section">
                <h4>📋 Форма создания тарифов</h4>
                <div className="section-description">
                  Проверьте и отредактируйте извлеченные данные перед сохранением. Каждый маршрут будет сохранен как отдельный тариф.
                </div>

                {/* Отладочная информация */}
                <div className="form-section" style={{ marginBottom: 20 }}>
                  <h5>Отладочная информация:</h5>
                  <div style={{ fontSize: '12px', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                    <div>extractedData: {extractedData ? '✓ Загружены' : '✗ Не загружены'}</div>
                    <div>tariff_data: {extractedData?.tariff_data ? '✓ Загружены' : '✗ Не загружены'}</div>
                    <div>routes: {extractedData?.tariff_data?.routes ? `${extractedData.tariff_data.routes.length} маршрутов` : '✗ Нет маршрутов'}</div>
                    <div>transport_type: {extractedData?.tariff_data?.transport_type || 'Не определен'}</div>
                    <div>basis: {extractedData?.tariff_data?.basis || 'Не определен'}</div>
                  </div>
                </div>

                {/* Предварительный просмотр извлеченного текста */}
                <div className="form-section" style={{ marginBottom: 20 }}>
                  <h5>Извлеченный текст из файла:</h5>
                  <div style={{ 
                    maxHeight: 200, 
                    overflow: 'auto', 
                    padding: 12, 
                    backgroundColor: 'var(--muted-surface)', 
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                    fontFamily: 'monospace',
                    fontSize: '12px',
                    whiteSpace: 'pre-wrap',
                    color: 'var(--text-muted)'
                  }}>
                    {extractedData.extracted_text}
                  </div>
                </div>

                {/* Форма редактирования тарифа */}
                <div className="form-grid">
                  {/* Основные поля */}
                  <div className="form-section">
                    <h5>Основные параметры</h5>
                    
                    <div className="form-group">
                      <label className="form-label">Тип транспорта:</label>
                      <select 
                        value={extractedData?.tariff_data?.transport_type || selectedTransport.id}
                        onChange={e => updateTariffField('transport_type', e.target.value)}
                        className="form-select"
                      >
                        <option value="">Выберите тип транспорта</option>
                        <option value="auto">Автомобильный</option>
                        <option value="rail">Железнодорожный</option>
                        <option value="sea">Морской</option>
                        <option value="air">Авиа</option>
                        <option value="multimodal">Мультимодальный</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Базис поставки:</label>
                      <select 
                        value={extractedData?.tariff_data?.basis || ''}
                        onChange={e => updateTariffField('basis', e.target.value)}
                        className="form-select"
                      >
                        <option value="">Выберите базис поставки</option>
                        <option value="EXW">EXW - Ex Works</option>
                        <option value="FCA">FCA - Free Carrier</option>
                        <option value="FOB">FOB - Free On Board</option>
                        <option value="CFR">CFR - Cost and Freight</option>
                        <option value="CIF">CIF - Cost, Insurance and Freight</option>
                        <option value="CIP">CIP - Carriage and Insurance Paid</option>
                        <option value="CPT">CPT - Carriage Paid To</option>
                        <option value="DAP">DAP - Delivered At Place</option>
                        <option value="DDP">DDP - Delivered Duty Paid</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Тип ТС:</label>
                      <input 
                        type="text"
                        value={extractedData?.tariff_data?.vehicle_type || ''}
                        onChange={e => updateTariffField('vehicle_type', e.target.value)}
                        placeholder="Например: Тент 20т 82м3"
                        className="form-input"
                      />
                    </div>
                  </div>

                  {/* Общие цены и сроки */}
                  <div className="form-section">
                    <h5>Общие параметры</h5>
                    
                    <div className="form-group">
                      <label className="form-label">Общая цена (RUB):</label>
                      <input 
                        type="number"
                        step="0.01"
                        value={extractedData?.tariff_data?.price_rub || ''}
                        onChange={e => updateTariffField('price_rub', e.target.value ? parseFloat(e.target.value) : null)}
                        placeholder="0.00"
                        className="form-input"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Общая цена (USD):</label>
                      <input 
                        type="number"
                        step="0.01"
                        value={extractedData?.tariff_data?.price_usd || ''}
                        onChange={e => updateTariffField('price_usd', e.target.value ? parseFloat(e.target.value) : null)}
                        placeholder="0.00"
                        className="form-input"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Дата действия:</label>
                      <input 
                        type="date"
                        value={formatDate(extractedData?.tariff_data?.validity_date)}
                        onChange={e => updateTariffField('validity_date', e.target.value)}
                        className="form-input"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Общее время в пути (дни):</label>
                      <input 
                        type="number"
                        value={extractedData?.tariff_data?.transit_time_days || ''}
                        onChange={e => updateTariffField('transit_time_days', e.target.value ? parseInt(e.target.value) : null)}
                        placeholder="0"
                        className="form-input"
                      />
                    </div>
                  </div>

                  {/* Дополнительные затраты */}
                  <div className="form-section">
                    <h5>Дополнительные затраты</h5>
                    
                    <div className="form-group">
                      <label className="form-label">СВХ:</label>
                      <input 
                        type="number"
                        step="0.01"
                        value={extractedData?.tariff_data?.cbx_cost || ''}
                        onChange={e => updateTariffField('cbx_cost', e.target.value ? parseFloat(e.target.value) : null)}
                        placeholder="0.00"
                        className="form-input"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Терминальная обработка:</label>
                      <input 
                        type="number"
                        step="0.01"
                        value={extractedData?.tariff_data?.terminal_handling_cost || ''}
                        onChange={e => updateTariffField('terminal_handling_cost', e.target.value ? parseFloat(e.target.value) : null)}
                        placeholder="0.00"
                        className="form-input"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Автовывоз:</label>
                      <input 
                        type="number"
                        step="0.01"
                        value={extractedData?.tariff_data?.auto_pickup_cost || ''}
                        onChange={e => updateTariffField('auto_pickup_cost', e.target.value ? parseFloat(e.target.value) : null)}
                        placeholder="0.00"
                        className="form-input"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Охрана:</label>
                      <input 
                        type="number"
                        step="0.01"
                        value={extractedData?.tariff_data?.security_cost || ''}
                        onChange={e => updateTariffField('security_cost', e.target.value ? parseFloat(e.target.value) : null)}
                        placeholder="0.00"
                        className="form-input"
                      />
                    </div>

                    {/* Авиационные сборы */}
                    <div className="form-group">
                      <label className="form-label">Парковка/Ворота:</label>
                      <input 
                        type="number"
                        step="0.01"
                        value={extractedData?.tariff_data?.car_parking_cost || ''}
                        onChange={e => updateTariffField('car_parking_cost', e.target.value ? parseFloat(e.target.value) : null)}
                        placeholder="0.00"
                        className="form-input"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Обработка:</label>
                      <input 
                        type="number"
                        step="0.01"
                        value={extractedData?.tariff_data?.handling_cost || ''}
                        onChange={e => updateTariffField('handling_cost', e.target.value ? parseFloat(e.target.value) : null)}
                        placeholder="0.00"
                        className="form-input"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Декларация:</label>
                      <input 
                        type="number"
                        step="0.01"
                        value={extractedData?.tariff_data?.declaration_cost || ''}
                        onChange={e => updateTariffField('declaration_cost', e.target.value ? parseFloat(e.target.value) : null)}
                        placeholder="0.00"
                        className="form-input"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Регистрация:</label>
                      <input 
                        type="number"
                        step="0.01"
                        value={extractedData?.tariff_data?.registration_cost || ''}
                        onChange={e => updateTariffField('registration_cost', e.target.value ? parseFloat(e.target.value) : null)}
                        placeholder="0.00"
                        className="form-input"
                      />
                    </div>
                  </div>
                </div>

                {/* Секция маршрутов */}
                <div className="form-section" style={{ marginTop: 20 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <h5>Маршруты ({extractedData?.tariff_data?.routes?.length || 0})</h5>
                    <button 
                      className="btn btn-secondary"
                      onClick={addRoute}
                      style={{ fontSize: '14px', padding: '6px 12px' }}
                    >
                      + Добавить маршрут
                    </button>
                  </div>

                  {extractedData?.tariff_data?.routes?.map((route, index) => (
                    <div key={index} className="form-section" style={{ 
                      marginBottom: 16,
                      backgroundColor: 'var(--muted-surface)'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                        <h6 style={{ margin: 0 }}>Маршрут {index + 1}</h6>
                        <button 
                          className="btn btn-danger"
                          onClick={() => removeRoute(index)}
                          style={{ fontSize: '12px', padding: '4px 8px' }}
                          disabled={extractedData?.tariff_data?.routes?.length === 1}
                        >
                          Удалить
                        </button>
                      </div>

                      <div className="form-grid">
                        <div className="form-group">
                          <label className="form-label">Страна отправления:</label>
                          <input 
                            type="text"
                            value={route.origin_country || ''}
                            onChange={e => updateRouteField(index, 'origin_country', e.target.value)}
                            placeholder="Россия"
                            className="form-input"
                          />
                        </div>

                        <div className="form-group">
                          <label className="form-label">Город отправления:</label>
                          <input 
                            type="text"
                            value={route.origin_city || ''}
                            onChange={e => updateRouteField(index, 'origin_city', e.target.value)}
                            placeholder="Москва"
                            style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '14px' }}
                          />
                        </div>

                        <div>
                          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: '14px' }}>Страна назначения:</label>
                          <input 
                            type="text"
                            value={route.destination_country || ''}
                            onChange={e => updateRouteField(index, 'destination_country', e.target.value)}
                            placeholder="Россия"
                            style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '14px' }}
                          />
                        </div>

                        <div>
                          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: '14px' }}>Город назначения:</label>
                          <input 
                            type="text"
                            value={route.destination_city || ''}
                            onChange={e => updateRouteField(index, 'destination_city', e.target.value)}
                            placeholder="Санкт-Петербург"
                            style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '14px' }}
                          />
                        </div>

                        <div>
                          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: '14px' }}>Цена маршрута (RUB):</label>
                          <input 
                            type="number"
                            step="0.01"
                            value={route.price_rub || ''}
                            onChange={e => updateRouteField(index, 'price_rub', e.target.value ? parseFloat(e.target.value) : null)}
                            placeholder="0.00"
                            style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '14px' }}
                          />
                        </div>

                        <div>
                          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: '14px' }}>Цена маршрута (USD):</label>
                          <input 
                            type="number"
                            step="0.01"
                            value={route.price_usd || ''}
                            onChange={e => updateRouteField(index, 'price_usd', e.target.value ? parseFloat(e.target.value) : null)}
                            placeholder="0.00"
                            style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '14px' }}
                          />
                        </div>

                        <div>
                          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: '14px' }}>Время в пути (дни):</label>
                          <input 
                            type="number"
                            value={route.transit_time_days || ''}
                            onChange={e => updateRouteField(index, 'transit_time_days', e.target.value ? parseInt(e.target.value) : null)}
                            placeholder="0"
                            style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '14px' }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}

                  {(!extractedData?.tariff_data?.routes || extractedData.tariff_data.routes.length === 0) && (
                    <div style={{ 
                      padding: 20, 
                      textAlign: 'center', 
                      border: '2px dashed var(--border)', 
                      borderRadius: '8px',
                      color: 'var(--text-muted)'
                    }}>
                      Маршруты не найдены. Нажмите "Добавить маршрут" для создания.
                    </div>
                  )}
                </div>

                {/* Кнопки действий */}
                <div className="toolbar" style={{ marginTop: 20 }}>
                  <button 
                    className="btn btn-primary"
                    onClick={() => handleSaveTariff(extractedData?.tariff_data)}
                    disabled={isLoading || !extractedData?.tariff_data?.routes || extractedData.tariff_data.routes.length === 0}
                    style={{ backgroundColor: selectedTransport.color, borderColor: selectedTransport.color }}
                  >
                    {isLoading ? 'Сохраняем...' : `Сохранить ${extractedData?.tariff_data?.routes?.length || 0} тарифов в базу`}
                  </button>
                  
                  <button 
                    className="btn btn-secondary"
                    onClick={() => {
                      setExtractedData(null)
                      setFile(null)
                      setMessage('')
                      const fileInput = document.querySelector('input[type="file"]')
                      if (fileInput) fileInput.value = ''
                    }}
                    disabled={isLoading}
                  >
                    Отменить
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Основной интерфейс с карточками
  return (
    <div className="content">
      <div className="container">
        <div className="card card-pad">
          <div className="header-section">
            <h2 className="title">🤖 Автоматическое создание тарифов</h2>
            <div className="subtitle">Выберите тип транспорта для автоматического создания тарифов из файлов</div>
          </div>

          <div className="transport-grid">
            {transportTypes.map((transport) => (
              <div 
                key={transport.id}
                className="transport-card"
                onClick={() => handleTransportSelect(transport)}
                style={{ 
                  borderColor: transport.color,
                  cursor: 'pointer',
                  transition: 'all 0.3s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-5px)'
                  e.currentTarget.style.boxShadow = `0 8px 25px rgba(0,0,0,0.15)`
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)'
                }}
              >
                <div className="transport-card-header" style={{ backgroundColor: transport.color }}>
                  <h3>{transport.title}</h3>
                  <div className="transport-subtitle">{transport.subtitle}</div>
                </div>
                
                <div className="transport-card-body">
                  <p className="transport-description">{transport.description}</p>
                  
                  <div className="transport-features">
                    <h4>Возможности парсинга:</h4>
                    <ul>
                      {transport.features.map((feature, index) => (
                        <li key={index}>✓ {feature}</li>
                      ))}
                    </ul>
                  </div>
                  
                  <button 
                    className="btn btn-primary"
                    style={{ 
                      backgroundColor: transport.color,
                      borderColor: transport.color,
                      width: '100%',
                      marginTop: '20px'
                    }}
                  >
                    Создать тарифы для {transport.title.split(' ')[1]}
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="info-section">
            <h3>ℹ️ Как работает автоматическое создание тарифов?</h3>
            <div className="info-grid">
              <div className="info-item">
                <h4>📁 Загрузка файла</h4>
                <p>Загрузите файл с тарифами в любом поддерживаемом формате (XLSX, PDF, DOCX, JPG, PNG).</p>
              </div>
              <div className="info-item">
                <h4>🤖 Автоматический парсинг</h4>
                <p>Система автоматически извлечет данные из файла с помощью специализированных парсеров.</p>
              </div>
              <div className="info-item">
                <h4>✏️ Редактирование</h4>
                <p>Проверьте и отредактируйте извлеченные данные перед сохранением в базу.</p>
              </div>
              <div className="info-item">
                <h4>💾 Сохранение</h4>
                <p>Сохраните тарифы в базу данных для дальнейшего использования в расчетах.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AutoTariffPage
