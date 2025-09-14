import React from 'react'
import { useNavigate } from 'react-router-dom'

function TransportSelectorPage({ token, user }) {
  const navigate = useNavigate()

  const transportTypes = [
    {
      id: 'auto',
      title: '🚛 Автомобильные перевозки',
      subtitle: 'FTL и LTL доставка',
      description: 'Полная и частичная загрузка автомобильным транспортом. Быстрая доставка по России и СНГ.',
      features: [
        'Дверь-дверь доставка',
        'FTL и LTL перевозки',
        'Срочная доставка',
        'Отслеживание груза'
      ],
      route: '/auto-transport',
      color: '#4CAF50'
    },
    {
      id: 'rail',
      title: '🚂 Железнодорожные перевозки',
      subtitle: 'Контейнерные и вагонные перевозки',
      description: 'Экономичная доставка контейнеров и грузов железнодорожным транспортом.',
      features: [
        'Контейнерные перевозки',
        'Вагонные перевозки',
        'СВХ услуги',
        'Таможенное оформление'
      ],
      route: '/railway-transport',
      color: '#FF9800'
    },
    {
      id: 'sea',
      title: '🚢 Морские перевозки',
      subtitle: 'FCL, LCL и навалочные грузы',
      description: 'Международные морские перевозки контейнеров и навалочных грузов.',
      features: [
        'FCL и LCL перевозки',
        'Навалочные грузы',
        'Портовые услуги',
        'Международные маршруты'
      ],
      route: '/sea-transport',
      color: '#2196F3'
    },
    {
      id: 'air',
      title: '✈️ Авиаперевозки',
      subtitle: 'Express и стандартная доставка',
      description: 'Быстрая доставка грузов воздушным транспортом по всему миру.',
      features: [
        'Express доставка',
        'Стандартная доставка',
        'Экономичная доставка',
        'Чартерные рейсы'
      ],
      route: '/air-transport',
      color: '#9C27B0'
    },
    {
      id: 'multimodal',
      title: '🚢🚂✈️🚛 Мультимодальные перевозки',
      subtitle: 'Комбинированная доставка',
      description: 'Оптимальное сочетание различных видов транспорта для сложных маршрутов.',
      features: [
        'Море + Железная дорога',
        'Самолёт + Автомобиль',
        'Комбинированные маршруты',
        'Оптимизация стоимости'
      ],
      route: '/multimodal-transport',
      color: '#607D8B'
    }
  ]

  const handleTransportSelect = (transportType) => {
    navigate(transportType.route)
  }

  return (
    <div className="content">
      <div className="container">
        <div className="card card-pad">
          <div className="header-section">
            <h2 className="title">🚛 Выберите тип перевозки</h2>
            <div className="subtitle">Выберите наиболее подходящий вид транспорта для вашего груза</div>
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
                    <h4>Основные возможности:</h4>
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
                    Выбрать {transport.title.split(' ')[1]}
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="info-section">
            <h3>ℹ️ Как выбрать подходящий вид транспорта?</h3>
            <div className="info-grid">
              <div className="info-item">
                <h4>🚛 Автомобильный транспорт</h4>
                <p>Идеален для быстрой доставки по России и СНГ. Подходит для грузов до 20 тонн.</p>
              </div>
              <div className="info-item">
                <h4>🚂 Железнодорожный транспорт</h4>
                <p>Экономичен для больших объёмов. Отлично подходит для контейнерных перевозок.</p>
              </div>
              <div className="info-item">
                <h4>🚢 Морской транспорт</h4>
                <p>Самый экономичный для международных перевозок. Подходит для больших партий.</p>
              </div>
              <div className="info-item">
                <h4>✈️ Воздушный транспорт</h4>
                <p>Самый быстрый способ доставки. Идеален для срочных и ценных грузов.</p>
              </div>
              <div className="info-item">
                <h4>🚢🚂✈️🚛 Мультимодальный</h4>
                <p>Оптимальное сочетание видов транспорта для сложных международных маршрутов.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TransportSelectorPage
