import React from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API || 'http://127.0.0.1:8000'

function TextExtractionPage({ token }) {
  const [files, setFiles] = React.useState([])
  const [uploadedFiles, setUploadedFiles] = React.useState([])
  const [results, setResults] = React.useState([])
  const [isLoading, setIsLoading] = React.useState(false)
  const [supportedFormats, setSupportedFormats] = React.useState([])
  const [includeMetadata, setIncludeMetadata] = React.useState(false)
  const [selectedText, setSelectedText] = React.useState('')
  const [analysisType, setAnalysisType] = React.useState('general')
  const [analysisResult, setAnalysisResult] = React.useState(null)

  // Загружаем поддерживаемые форматы при монтировании компонента
  React.useEffect(() => {
    loadSupportedFormats()
  }, [])

  const loadSupportedFormats = async () => {
    try {
      const response = await axios.get('/text-extraction/supported-formats', {
        baseURL: API_BASE,
        headers: { Authorization: `Bearer ${token}` }
      })
      setSupportedFormats(response.data.supported_formats)
    } catch (error) {
      console.error('Ошибка загрузки поддерживаемых форматов:', error)
    }
  }

  const handleFileSelect = (event) => {
    const selectedFiles = Array.from(event.target.files)
    setFiles(selectedFiles)
  }

  const handleUpload = async () => {
    if (files.length === 0) {
      alert('Выберите файлы для загрузки')
      return
    }

    setIsLoading(true)
    setResults([])

    try {
      const formData = new FormData()
      files.forEach(file => {
        formData.append('files', file)
      })
      formData.append('include_metadata', includeMetadata)

      const response = await axios.post('/text-extraction/extract-text-batch', formData, {
        baseURL: API_BASE,
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      })

      setResults(response.data.results)
      setUploadedFiles(files)
    } catch (error) {
      console.error('Ошибка загрузки файлов:', error)
      alert('Ошибка при обработке файлов: ' + (error.response?.data?.detail || error.message))
    } finally {
      setIsLoading(false)
    }
  }

  const handleSingleFileUpload = async (file) => {
    setIsLoading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('include_metadata', includeMetadata)

      const response = await axios.post('/text-extraction/extract-text', formData, {
        baseURL: API_BASE,
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      })

      setResults([response.data])
      setUploadedFiles([file])
    } catch (error) {
      console.error('Ошибка загрузки файла:', error)
      alert('Ошибка при обработке файла: ' + (error.response?.data?.detail || error.message))
    } finally {
      setIsLoading(false)
    }
  }

  const handleAnalyzeText = async () => {
    if (!selectedText.trim()) {
      alert('Введите текст для анализа')
      return
    }

    try {
      const formData = new FormData()
      formData.append('text', selectedText)
      formData.append('analysis_type', analysisType)

      const response = await axios.post('/text-extraction/analyze-text', formData, {
        baseURL: API_BASE,
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      })

      setAnalysisResult(response.data)
    } catch (error) {
      console.error('Ошибка анализа текста:', error)
      alert('Ошибка при анализе текста: ' + (error.response?.data?.detail || error.message))
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Текст скопирован в буфер обмена')
    }).catch(() => {
      alert('Ошибка копирования в буфер обмена')
    })
  }

  const downloadText = (text, filename) => {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${filename}_extracted.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="content">
      <div className="container">
        <div className="card card-pad" style={{ maxWidth: 1200 }}>
          <h2 className="title">Извлечение текста из файлов</h2>
          
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
          </div>

          {/* Загрузка файлов */}
          <div className="form-section">
            <h4>📁 Загрузка файлов</h4>
            <div className="section-description">
              Выберите один или несколько файлов для извлечения текста
            </div>
            
            <div style={{ marginBottom: 16 }}>
              <input 
                type="file" 
                multiple 
                onChange={handleFileSelect}
                accept={supportedFormats.join(',')}
                style={{ marginBottom: 12 }}
              />
              
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <input 
                    type="checkbox" 
                    checked={includeMetadata}
                    onChange={(e) => setIncludeMetadata(e.target.checked)}
                  />
                  Включить метаданные (страницы, таблицы, изображения)
                </label>
              </div>
              
              <div className="toolbar">
                <button 
                  className="btn btn-primary" 
                  onClick={handleUpload}
                  disabled={isLoading || files.length === 0}
                >
                  {isLoading ? 'Обрабатываем...' : `Извлечь текст из ${files.length} файлов`}
                </button>
              </div>
            </div>

            {/* Выбранные файлы */}
            {files.length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <h5>Выбранные файлы:</h5>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {files.map((file, index) => (
                    <div key={index} style={{ 
                      padding: 8, 
                      border: '1px solid var(--border)', 
                      borderRadius: '4px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}>
                      <span>{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
                      <button 
                        className="btn btn-secondary"
                        onClick={() => handleSingleFileUpload(file)}
                        disabled={isLoading}
                        style={{ fontSize: '12px', padding: '4px 8px' }}
                      >
                        Обработать отдельно
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Результаты извлечения */}
          {results.length > 0 && (
            <div className="form-section">
              <h4>📄 Результаты извлечения</h4>
              <div className="section-description">
                Извлеченный текст из загруженных файлов
              </div>
              
              {results.map((result, index) => (
                <div key={index} style={{ 
                  marginBottom: 20, 
                  padding: 16, 
                  border: '1px solid var(--border)', 
                  borderRadius: '8px',
                  backgroundColor: result.success ? 'var(--muted-surface)' : '#fee'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                    <h5 style={{ margin: 0 }}>{result.filename}</h5>
                    <div style={{ display: 'flex', gap: 8 }}>
                      {result.success && (
                        <>
                          <button 
                            className="btn btn-secondary"
                            onClick={() => copyToClipboard(result.text)}
                            style={{ fontSize: '12px', padding: '4px 8px' }}
                          >
                            Копировать
                          </button>
                          <button 
                            className="btn btn-secondary"
                            onClick={() => downloadText(result.text, result.filename)}
                            style={{ fontSize: '12px', padding: '4px 8px' }}
                          >
                            Скачать
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                  
                  {result.success ? (
                    <div>
                      <div style={{ marginBottom: 8, fontSize: '12px', color: 'var(--text-muted)' }}>
                        Размер файла: {(result.file_size / 1024).toFixed(1)} KB | 
                        Длина текста: {result.text_length} символов
                        {includeMetadata && (
                          <>
                            | Страниц: {result.pages} | 
                            Таблиц: {result.tables} | 
                            Изображений: {result.images}
                          </>
                        )}
                      </div>
                      
                      <div style={{ 
                        maxHeight: 300, 
                        overflow: 'auto', 
                        padding: 12, 
                        backgroundColor: 'white', 
                        border: '1px solid var(--border)',
                        borderRadius: '4px',
                        fontFamily: 'monospace',
                        fontSize: '12px',
                        whiteSpace: 'pre-wrap'
                      }}>
                        {result.preview || result.text}
                      </div>
                      
                      {result.text && result.text.length > 500 && (
                        <div style={{ marginTop: 8, fontSize: '12px', color: 'var(--text-muted)' }}>
                          Показан предварительный просмотр. Полный текст доступен для копирования и скачивания.
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{ color: '#e53e3e' }}>
                      Ошибка: {result.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Анализ текста */}
          <div className="form-section">
            <h4>🔍 Анализ текста</h4>
            <div className="section-description">
              Анализируйте извлеченный текст для поиска структурированной информации
            </div>
            
            <div style={{ marginBottom: 16 }}>
              <textarea
                placeholder="Вставьте текст для анализа..."
                value={selectedText}
                onChange={(e) => setSelectedText(e.target.value)}
                style={{ 
                  width: '100%', 
                  minHeight: 120, 
                  padding: 12,
                  border: '1px solid var(--border)',
                  borderRadius: '4px',
                  fontFamily: 'monospace',
                  fontSize: '12px'
                }}
              />
            </div>
            
            <div style={{ display: 'flex', gap: 12, marginBottom: 16, alignItems: 'center' }}>
              <select 
                value={analysisType}
                onChange={(e) => setAnalysisType(e.target.value)}
                style={{ padding: '8px 12px' }}
              >
                <option value="general">Общий анализ</option>
                <option value="logistics">Логистический анализ</option>
                <option value="pricing">Анализ цен</option>
              </select>
              
              <button 
                className="btn btn-primary"
                onClick={handleAnalyzeText}
                disabled={!selectedText.trim()}
              >
                Анализировать
              </button>
            </div>

            {/* Результаты анализа */}
            {analysisResult && (
              <div style={{ 
                padding: 16, 
                backgroundColor: 'var(--muted-surface)', 
                borderRadius: '8px',
                border: '1px solid var(--border)'
              }}>
                <h5 style={{ margin: '0 0 12px 0' }}>Результаты анализа</h5>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
                  <div>
                    <strong>Основная статистика:</strong>
                    <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
                      <li>Длина текста: {analysisResult.text_length} символов</li>
                      <li>Количество слов: {analysisResult.word_count}</li>
                      <li>Количество строк: {analysisResult.line_count}</li>
                      <li>Символов без пробелов: {analysisResult.characters_without_spaces}</li>
                    </ul>
                  </div>
                  
                  {analysisType === 'general' && (
                    <div>
                      <strong>Найденная информация:</strong>
                      <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
                        <li>Email адреса: {analysisResult.emails_found?.length || 0}</li>
                        <li>Телефоны: {analysisResult.phones_found?.length || 0}</li>
                        <li>Даты: {analysisResult.dates_found?.length || 0}</li>
                        <li>Содержит числа: {analysisResult.has_numbers ? 'Да' : 'Нет'}</li>
                        <li>Содержит валюту: {analysisResult.has_currency ? 'Да' : 'Нет'}</li>
                      </ul>
                    </div>
                  )}
                  
                  {analysisType === 'logistics' && (
                    <div>
                      <strong>Логистическая информация:</strong>
                      <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
                        <li>Города: {analysisResult.cities_found?.length || 0}</li>
                        <li>Типы транспорта: {analysisResult.transport_types?.length || 0}</li>
                        <li>Базисы поставки: {analysisResult.incoterms_bases?.length || 0}</li>
                        <li>Информация о маршрутах: {analysisResult.has_route_info ? 'Да' : 'Нет'}</li>
                        <li>Информация о контейнерах: {analysisResult.has_container_info ? 'Да' : 'Нет'}</li>
                      </ul>
                    </div>
                  )}
                  
                  {analysisType === 'pricing' && (
                    <div>
                      <strong>Ценовая информация:</strong>
                      <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
                        <li>Упоминаний цен: {analysisResult.total_price_mentions || 0}</li>
                        <li>Диапазонов цен: {analysisResult.price_ranges?.length || 0}</li>
                        <li>Минимальная цена: {analysisResult.min_price || 'Не найдено'}</li>
                        <li>Максимальная цена: {analysisResult.max_price || 'Не найдено'}</li>
                        <li>Содержит валюту: {analysisResult.has_currency_info ? 'Да' : 'Нет'}</li>
                      </ul>
                    </div>
                  )}
                </div>
                
                {/* Детальная информация */}
                {analysisType === 'general' && analysisResult.emails_found?.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <strong>Найденные email адреса:</strong>
                    <div style={{ marginTop: 8 }}>
                      {analysisResult.emails_found.map((email, index) => (
                        <span key={index} style={{ 
                          display: 'inline-block', 
                          padding: '4px 8px', 
                          margin: '2px', 
                          backgroundColor: 'var(--primary)', 
                          color: 'white', 
                          borderRadius: '4px', 
                          fontSize: '12px' 
                        }}>
                          {email}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {analysisType === 'logistics' && analysisResult.cities_found?.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <strong>Найденные города:</strong>
                    <div style={{ marginTop: 8 }}>
                      {analysisResult.cities_found.map((city, index) => (
                        <span key={index} style={{ 
                          display: 'inline-block', 
                          padding: '4px 8px', 
                          margin: '2px', 
                          backgroundColor: 'var(--secondary)', 
                          color: 'white', 
                          borderRadius: '4px', 
                          fontSize: '12px' 
                        }}>
                          {city}
                        </span>
                      ))}
                    </div>
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

export default TextExtractionPage
