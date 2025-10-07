"""
Модуль для работы с шаблонами коммерческих предложений
"""

from typing import Dict, Any, Optional
from datetime import date, datetime
from services.pricing import calc_air_costs, volumetric_weight, format_number, coerce_days, calc_sum_rub, build_formula
import re

class KPTemplateManager:
    """Менеджер шаблонов коммерческих предложений"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Загружаем шаблоны из Excel-файла"""
        
        # Шаблоны для автомобильных перевозок (точные формы КП)
        auto_templates = {
            'EXW': """Автомобильная доставка генерального груза, базис EXW

Автомобильную доставку груза, стоимость которой составит {price}.
Расчёт: ({generic_rub_formula}).
В стоимость включено:
- подача транспорта под погрузку Отправителю;
- 24 часа на погрузку и таможенное оформление экспорта;
- оформление экспортной декларации;
- транспортировка в {vehicle_type} груза по маршруту {origin_address}-{border_point}-{destination_address};
- 48 часов на разгрузку груза и таможенное оформление импорта;
- доставка груза конечному Получателю.

Простой составляет 150$/сутки
Срок доставки составляет {transit_time_days} дней с момента забора груза.
Ставка валидна до {validity_date}

Ждем комментарии к предложению!""",

            'FCA': """Автомобильная доставка генерального груза, базис FCA

Автомобильную доставку груза, стоимость которой составит {price}.
Расчёт: ({generic_rub_formula}).
В стоимость включено:
- подача транспорта под погрузку Отправителю;
- 24 часа на погрузку и таможенное оформление экспорта;
- транспортировка в {vehicle_type} груза по маршруту {origin_address}-{border_point}-{destination_address};
- 48 часов на разгрузку груза и таможенное оформление импорта;
- доставка груза конечному Получателю.

Простой составляет 150$/сутки
Конвертация
Срок доставки составляет {transit_time_days} дней с момента забора груза.
Ставка валидна до {validity_date}

Ждем комментарии к предложению!"""
        }
        
        # Шаблоны для мультимодальных перевозок (точные формы КП)
        multimodal_templates = {
            'EXW': """Мультимодальная доставка генерального груза, базис EXW

Мультимодальную доставку по стоимости {price_usd} USD + {price_rub} руб ({generic_rub_formula}) за транспортировку груза EXW {origin_address}-{transit_port}-{destination_address}.
В стоимость включено:
- выдача порожнего контейнера;
- предоставление порожнего контейнера {vehicle_type} под затарку по адресу {origin_address};
- автомобильная перевозка контейнера от отправителя до порта отправления;
- экспортное оформление груза;
- терминальные расходы в порту отправления;
- погрузка контейнера на борт судна;
- морской фрахт груза;
- внутрипортовые расходы в порту назначения;
- экспедирование в порту назначения;
- терминальная обработка груза на станции отправления;
- поставка контейнера на платформу;
- тариф железнодорожной доставки;

Раскредитация контейнера и терминальная обработка на станции {arrival_station} составит {cbx_cost} руб
- автомобильный вывоз контейнера Получателю по адресу {destination_address} составит {auto_pickup_cost} руб

В стоимость включено:
- вывоз контейнера автомобильным транспортом Получателю;
- возврат порожнего контейнера на сток.

Транзитный срок по мультимодальной доставке – {transit_time_days} дней с даты отправления из порта, общий транзитный срок – ({transit_time_days}+2+{auto_pickup_days}).
Валидность ставки: до {validity_date}
При оплате в рублях дополнительно оплачивается конвертация {currency_conversion} процентов""",

            'FCA': """Мультимодальная доставка генерального груза, базис FCA

Мультимодальную доставку по стоимости {price_usd} USD + {price_rub} руб ({generic_rub_formula}) за транспортировку груза FCA {origin_address}-{transit_port}-{destination_address}.
В стоимость включено:
- выдача порожнего контейнера;
- предоставление порожнего контейнера {vehicle_type} под затарку по адресу {origin_address};
- автомобильная перевозка контейнера от отправителя до порта отправления;
- терминальные расходы в порту отправления;
- погрузка контейнера на борт судна;
- морской фрахт груза;
- внутрипортовые расходы в порту назначения;
- экспедирование в порту назначения;
- терминальная обработка груза на станции отправления;
- поставка контейнера на платформу;
- тариф железнодорожной доставки;

Раскредитация контейнера и терминальная обработка на станции {arrival_station} составит {cbx_cost} руб
- автомобильный вывоз контейнера Получателю по адресу {destination_address} составит {auto_pickup_cost} руб

В стоимость включено:
- вывоз контейнера автомобильным транспортом Получателю;
- возврат порожнего контейнера на сток.

Транзитный срок по мультимодальной доставке – {transit_time_days} дней с даты отправления из порта, общий транзитный срок – ({transit_time_days}+2+{auto_pickup_days}).
Валидность ставки: до {validity_date}
При оплате в рублях дополнительно оплачивается конвертация {currency_conversion} процентов""",

            'FOB': """Мультимодальная доставка генерального груза, базис FOB

Мультимодальную доставку по стоимости {price_usd} USD + {price_rub} руб ({generic_rub_formula}) за транспортировку груза FOB {origin_address}-{transit_port}-{destination_address}.
В стоимость включено:
- выдача порожнего контейнера;
- морской фрахт груза;
- внутрипортовые расходы в порту назначения;
- экспедирование в порту назначения;
- терминальная обработка груза на станции отправления;
- поставка контейнера на платформу;
- тариф железнодорожной доставки;

Раскредитация контейнера и терминальная обработка на станции {arrival_station} составит {cbx_cost} руб
- автомобильный вывоз контейнера Получателю по адресу {destination_address} составит {auto_pickup_cost} руб

В стоимость включено:
- вывоз контейнера автомобильным транспортом Получателю;
- возврат порожнего контейнера на сток.

Транзитный срок по мультимодальной доставке – {transit_time_days} дней с даты отправления из порта, общий транзитный срок – ({transit_time_days}+2+{auto_pickup_days}).
Валидность ставки: до {validity_date}
При оплате в рублях дополнительно оплачивается конвертация {currency_conversion} процентов"""
        }
        
        # Шаблоны для железнодорожных перевозок (точные формы КП)
        rail_templates = {
            'EXW': """Железнодорожная доставка генерального груза, базис EXW

Согласно текущего запроса есть предложение по стоимости {price_usd} USD за транспортировку груза EXW {origin_address}-{arrival_station}-{destination_address}.
В стоимость включено:
- выдача порожнего контейнера;
- экспортное оформление груза;
- предоставление порожнего контейнера {vehicle_type} под затарку по адресу {origin_address};
- автомобильная перевозка контейнера от отправителя до железнодорожной станции отправления;
- терминальные расходы на станции отправления;
- погрузка контейнера на площадку;
- тариф и ставка по железнодорожной доставке;
- терминальная обработка груза на станции прибытия.

Раскредитация контейнера и терминальная обработка на станции {arrival_station} составит {cbx_cost} руб
- автомобильный вывоз контейнера Получателю по адресу {destination_address} составит {auto_pickup_cost} руб

Транзитный срок по жд доставке – {transit_time_days} дней с даты отправления поезда, общий транзитный срок – ({transit_time_days}+2+{auto_pickup_days}).
Валидность ставки: до {validity_date}""",

            'FCA': """Железнодорожная доставка генерального груза, базис FCA

Согласно текущего запроса есть предложение по стоимости {price_usd} USD за транспортировку груза FCA {origin_address}-{arrival_station}-{destination_address}.
В стоимость включено:
- выдача порожнего контейнера;
- предоставление порожнего контейнера {vehicle_type} под затарку по адресу {origin_address};
- автомобильная перевозка контейнера от отправителя до железнодорожной станции отправления;
- терминальные расходы на станции отправления;
- погрузка контейнера на площадку;
- тариф и ставка по железнодорожной доставке;
- терминальная обработка груза на станции прибытия.

Раскредитация контейнера и терминальная обработка на станции {arrival_station} составит {cbx_cost} руб
- автомобильный вывоз контейнера Получателю по адресу {destination_address} составит {auto_pickup_cost} руб

Транзитный срок по жд доставке – {transit_time_days} дней с даты отправления поезда, общий транзитный срок – ({transit_time_days}+2+{auto_pickup_days}).
Валидность ставки: до {validity_date}
При оплате в рублях дополнительно оплачивается конвертация {currency_conversion} процентов""",

            'FOB': """Железнодорожная доставка генерального груза, базис FOB

Согласно текущего запроса есть предложение по стоимости {price_usd} USD за транспортировку груза FOB {origin_address}-{arrival_station}-{destination_address}.
В стоимость включено:
- предоставление порожнего контейнера {vehicle_type} под затарку по адресу {origin_address};
- тариф и ставка по железнодорожной доставке;
- терминальная обработка груза на станции прибытия.

Раскредитация контейнера и терминальная обработка на станции {arrival_station} составит {cbx_cost} руб
- автомобильный вывоз контейнера Получателю по адресу {destination_address} составит {auto_pickup_cost} руб

Транзитный срок по жд доставке – {transit_time_days} дней с даты отправления поезда, общий транзитный срок – ({transit_time_days}+2+{auto_pickup_days}).
Валидность ставки: до {validity_date}
При оплате в рублях дополнительно оплачивается конвертация {currency_conversion} процентов"""
        }
        
        # Шаблоны для авиаперевозок
        air_templates = {
            'EXW': """Благодарим Вас за обращение и просим рассмотреть наше предложение по доставке, согласно текущего запроса:
Базис поставки: {basis}
Адрес отправления: {origin_address}
Адрес доставки: {destination_address}
Наименование груза: {cargo_name}
Вес: {weight_kg} кг
Габариты: {volume_m3} м³
Тип доставки: авиа

Предлагаем рассмотреть авиа доставку, стоимость которой на текущий момент составляет {air_cost_usd} USD ({air_usd_formula}) и {rub_cost_rub} рублей ({rub_rub_formula}).
В стоимость включено:
- Pre-carriage {origin_city} - {departure_airport};
- погрузочно-разгрузочные работы в аэропорту {departure_airport};
- терминальная обработка в аэропорту {departure_airport};
- размещение груза в аэропорту {departure_airport};
- выпуск авиа накладной (AWB);
- экспортное оформление груза;
- x-ray сканирование груза;
- Авиа фрахт {departure_airport} - {arrival_airport} из расчета объемного веса (больший вес между {weight_kg} кг и {volume_m3} м³ × 167 = {volumetric_weight} кг);
- погрузо-разгрузочные работы в аэропорту {arrival_airport};
- терминальная обработка в аэропорту {arrival_airport};
- автомобильная доставка груза Получателю (если доставка до двери) по адресу {destination_address}

Транзитный срок по авиа доставке – {transit_time_days} дней с даты вылета.
Валидность ставки до {validity_date}

Ждем комментарии к нашему предложению и надеемся на плодотворное сотрудничество!""",

            'FCA': """Благодарим Вас за обращение и просим рассмотреть наше предложение по доставке, согласно текущего запроса:
Базис поставки: {basis}
Адрес отправления: {origin_address}
Адрес доставки: {destination_address}
Наименование груза: {cargo_name}
Вес: {weight_kg} кг
Габариты: {volume_m3} м³
Тип доставки: авиа

Предлагаем рассмотреть авиа доставку, стоимость которой на текущий момент составляет {air_cost_usd} USD ({air_usd_formula}) и {rub_cost_rub} рублей ({rub_rub_formula}).
В стоимость включено:
- Pre-carriage {origin_city} - {departure_airport};
- погрузочно-разгрузочные работы в аэропорту {departure_airport};
- терминальная обработка в аэропорту {departure_airport};
- размещение груза в аэропорту {departure_airport};
- выпуск авиа накладной (AWB);
- x-ray сканирование груза;
- Авиа фрахт {departure_airport} - {arrival_airport} из расчета объемного веса (больший вес между {weight_kg} кг и {volume_m3} м³ × 167 = {volumetric_weight} кг);
- погрузо-разгрузочные работы в аэропорту {arrival_airport};
- терминальная обработка в аэропорту {arrival_airport};
- автомобильная доставка груза Получателю (если доставка до двери) по адресу {destination_address}

Транзитный срок по авиа доставке – {transit_time_days} дней с даты вылета.
Валидность ставки до {validity_date}

Ждем комментарии к нашему предложению и надеемся на плодотворное сотрудничество!"""
        }
        
        # Шаблоны для морских перевозок
        sea_templates = {
            'EXW': """Благодарим Вас за обращение и просим рассмотреть наше предложение по доставке, согласно текущего запроса:
Базис поставки: {basis}
Адрес отправления: {origin_address}
Адрес доставки: {destination_address}
Наименование груза: {cargo_name}
Вес: {weight_kg} кг
Габариты: {volume_m3} м³
Тип контейнера: {vehicle_type}
Тип доставки: морская

Предлагаем рассмотреть морскую доставку по стоимости {price_usd} USD и {price_rub} рублей ({generic_rub_formula}) за транспортировку груза {origin_address} – {destination_address} в контейнере {vehicle_type} весом до {weight_kg} кг объемом до {volume_m3} м³

В стоимость включено:
- выдача порожнего контейнера {vehicle_type};
- предоставление порожнего контейнера {vehicle_type} под затарку по адресу {origin_address};
- автомобильная перевозка контейнера от отправителя до порта {transit_port};
- экспортное оформление груза;
- терминальные расходы в порту отправления {transit_port};
- погрузка контейнера {vehicle_type} на борт судна;
- морской фрахт груза {transit_port}-{arrival_port};
- внутрипортовые расходы в порту назначения;
- экспедирование в порту прибытия {arrival_port};
- выгрузка контейнера с борта судна;
- вывоз контейнера автомобильным транспортом Получателю по адресу: {destination_address};
- возврат порожнего контейнера на сток.

Транзитный срок морской доставки – {transit_time_days} дней с даты выхода судна.
Валидность ставки до {validity_date}

Ждем комментарии к нашему предложению и надеемся на плодотворное сотрудничество!""",

            'FCA': """Благодарим Вас за обращение и просим рассмотреть наше предложение по доставке, согласно текущего запроса:
Базис поставки: {basis}
Адрес отправления: {origin_address}
Адрес доставки: {destination_address}
Наименование груза: {cargo_name}
Вес: {weight_kg} кг
Габариты: {volume_m3} м³
Тип контейнера: {vehicle_type}
Тип доставки: морская

Предлагаем рассмотреть морскую доставку по стоимости {price_usd} USD и {price_rub} рублей ({generic_rub_formula}) за транспортировку груза {origin_address} – {destination_address} в контейнере {vehicle_type} весом до {weight_kg} кг объемом до {volume_m3} м³

В стоимость включено:
- выдача порожнего контейнера {vehicle_type};
- предоставление порожнего контейнера {vehicle_type} под затарку по адресу {origin_address};
- автомобильная перевозка контейнера от отправителя до порта {transit_port};
- терминальные расходы в порту отправления {transit_port};
- погрузка контейнера {vehicle_type} на борт судна;
- морской фрахт груза {transit_port}-{arrival_port};
- внутрипортовые расходы в порту назначения;
- экспедирование в порту прибытия {arrival_port};
- выгрузка контейнера с борта судна;
- вывоз контейнера автомобильным транспортом Получателю по адресу: {destination_address};
- возврат порожнего контейнера на сток.

Транзитный срок морской доставки – {transit_time_days} дней с даты выхода судна.
Валидность ставки до {validity_date}

Ждем комментарии к нашему предложению и надеемся на плодотворное сотрудничество!""",

            'FOB': """Благодарим Вас за обращение и просим рассмотреть наше предложение по доставке, согласно текущего запроса:
Базис поставки: {basis}
Адрес отправления: {origin_address}
Адрес доставки: {destination_address}
Наименование груза: {cargo_name}
Вес: {weight_kg} кг
Габариты: {volume_m3} м³
Тип контейнера: {vehicle_type}
Тип доставки: морская

Предлагаем рассмотреть морскую доставку по стоимости {price_usd} USD и {price_rub} рублей ({generic_rub_formula}) за транспортировку груза {transit_port} – {destination_address} в контейнере {vehicle_type} весом до {weight_kg} кг объемом до {volume_m3} м³

В стоимость включено:
- выдача порожнего контейнера {vehicle_type};
- морской фрахт груза {transit_port}-{arrival_port};
- внутрипортовые расходы в порту назначения;
- экспедирование в порту прибытия {arrival_port};
- выгрузка контейнера с борта судна;
- вывоз контейнера автомобильным транспортом Получателю по адресу: {destination_address};
- возврат порожнего контейнера на сток.

Транзитный срок морской доставки – {transit_time_days} дней с даты выхода судна.
Валидность ставки до {validity_date}

Ждем комментарии к нашему предложению и надеемся на плодотворное сотрудничество!"""
        }
        
        return {
            'auto': auto_templates,
            'multimodal': multimodal_templates,
            'rail': rail_templates,
            'air': air_templates,
            'sea': sea_templates
        }
    
    def get_template(self, transport_type: str, basis: str) -> Optional[str]:
        """Получаем шаблон по типу транспорта и базису"""
        transport_type = transport_type.lower()
        
        if transport_type not in self.templates:
            return None
        
        return self.templates[transport_type].get(basis.upper())
    
    def format_template(self, template: str, data: Dict[str, Any]) -> str:
        """Форматируем шаблон с данными"""
        try:
            return template.format(**data)
        except KeyError as e:
            # Если не хватает переменной, заменяем на пустую строку
            missing_var = str(e).strip("'")
            return template.replace(f"{{{missing_var}}}", "")
        except Exception as e:
            print(f"Ошибка форматирования шаблона: {e}")
            return template
    
    def generate_kp_text(self, transport_type: str, basis: str, request_data: Dict[str, Any], option_data: Dict[str, Any]) -> str:
        """Генерируем текст КП на основе шаблона"""
        
        # Получаем шаблон
        template = self.get_template(transport_type, basis)
        if not template:
            return f"Шаблон для {transport_type} с базисом {basis} не найден"
        
        # Подготавливаем данные для подстановки
        # Базовые исходные данные (с минимальной пост-обработкой)
        data = {
            # Данные из запроса
            'basis': request_data.get('basis', ''),
            'origin_address': f"{request_data.get('origin_country', '')} {request_data.get('origin_city', '')}".strip(),
            'destination_address': f"{request_data.get('destination_country', '')} {request_data.get('destination_city', '')}".strip(),
            'origin_city': request_data.get('origin_city', ''),
            'destination_city': request_data.get('destination_city', ''),
            'cargo_name': request_data.get('cargo_name', ''),
            'weight_kg': format_number(request_data.get('weight_kg')),
            'volume_m3': format_number(request_data.get('volume_m3')),
            'vehicle_type': request_data.get('vehicle_type', ''),
            
            # Данные из тарифа
            'price': self._format_price(option_data),
            'price_usd': self._format_price_usd(option_data),
            'price_rub': self._format_price_rub(option_data),
            'transit_time_days': option_data.get('transit_time_days', ''),
            'validity_date': option_data.get('validity_date', ''),
            'border_point': option_data.get('border_point', ''),
            'svh_name': option_data.get('svh_name', ''),
            'arrival_station': option_data.get('arrival_station', ''),
            'departure_station': option_data.get('departure_station', ''),
            'transit_port': option_data.get('transit_port', ''),
            'arrival_port': option_data.get('arrival_port', ''),
            'departure_airport': option_data.get('departure_airport', ''),
            'arrival_airport': option_data.get('arrival_airport', ''),
            
            # Дополнительные данные
            'precarriage_cost': format_number(option_data.get('precarriage_cost')),
            'air_tariff': format_number(option_data.get('air_tariff')),
            'terminal_handling_cost': format_number(option_data.get('terminal_handling_cost')),
            'auto_pickup_cost': format_number(option_data.get('auto_pickup_cost')),
            'security_cost': format_number(option_data.get('security_cost')),
            
            # Дополнительные поля для морских перевозок
            'cbx_cost': format_number(option_data.get('cbx_cost')),
            'rail_tariff_rub': format_number(option_data.get('rail_tariff_rub')),
        }

        # Валидность и транзитные сроки: заменяем None на пустое
        def _fmt_date(v: Any) -> str:
            if isinstance(v, (date, datetime)):
                return v.strftime('%d.%m.%Y')
            return str(v) if v not in (None, '', 'None') else ''

        # Расчеты для авиа (используются в шаблоне air)
        vw = volumetric_weight(request_data.get('weight_kg'), request_data.get('volume_m3'))
        air_calc = calc_air_costs(
            weight_kg=request_data.get('weight_kg'),
            volume_m3=request_data.get('volume_m3'),
            precarriage_cost=option_data.get('precarriage_cost'),
            air_tariff=option_data.get('air_tariff'),
            terminal_handling_cost=option_data.get('terminal_handling_cost'),
            auto_pickup_cost=option_data.get('auto_pickup_cost'),
        )

        data.update({
            'volumetric_weight': format_number(air_calc['volumetric_weight']),
            'air_cost_usd': format_number(air_calc['air_cost_usd']) if air_calc['air_cost_usd'] > 0 else "по запросу",
            'rub_cost_rub': format_number(air_calc['rub_cost_rub']) if air_calc['rub_cost_rub'] > 0 else "по запросу",
            # Формульные представления (могут быть пустыми, если нет слагаемых)
            'air_usd_formula': air_calc['air_usd_formula'],
            'rub_rub_formula': air_calc['rub_rub_formula'],
            'transit_time_days': coerce_days(option_data.get('transit_time_days') or request_data.get('transit_time_days')),
            'validity_date': _fmt_date(option_data.get('validity_date') or request_data.get('validity_date')),
        })

        # Генерация общих формул для других типов (если есть компоненты)
        # Пример: RUB = cbx_cost + auto_pickup_cost + rail_tariff_rub
        generic_parts = [
            option_data.get('cbx_cost'),
            option_data.get('terminal_handling_cost'),
            option_data.get('auto_pickup_cost'),
            option_data.get('rail_tariff_rub'),
        ]
        rub_total = calc_sum_rub(*generic_parts) or option_data.get('price_rub')
        data.update({
            'generic_rub_formula': build_formula(generic_parts, rub_total)
        })
        
        text = self.format_template(template, data)
        return self._clean_text(text)

    def _clean_text(self, text: str) -> str:
        """Убирает артефакты: None, двойные пробелы, пустые скобки."""
        import re
        if not text:
            return text
        # Убираем None
        text = text.replace("None", "")
        # Пустые скобки () и варианты с пробелами/знаками
        text = re.sub(r"\(\s*\)", "", text)
        text = re.sub(r"\(\s*[+×x]\s*\)", "", text)
        # Сдваивание пробелов
        text = re.sub(r"\s{2,}", " ", text)
        # Пустые числовые единицы
        text = re.sub(r"\s+(USD|руб(\.|лей)?)\b", lambda m: "" if re.search(r"(\(|=|:)\s*$", text[:m.start()]) else " " + m.group(1), text)
        # Убираем хвосты вроде 'по адресу '
        text = re.sub(r"по адресу\s+\n", "\n", text)
        return text
    
    def _format_price(self, option_data: Dict[str, Any]) -> str:
        """Форматируем цену для отображения"""
        price_rub = option_data.get('final_price_rub') or option_data.get('price_rub')
        price_usd = option_data.get('price_usd')
        
        if price_rub and price_usd:
            return f"{float(price_rub):,.0f} ₽ ({float(price_usd):,.0f} USD)"
        elif price_rub:
            return f"{float(price_rub):,.0f} ₽"
        elif price_usd:
            return f"{float(price_usd):,.0f} USD"
        else:
            return "по запросу"
    
    def _format_price_usd(self, option_data: Dict[str, Any]) -> str:
        """Форматируем цену в USD"""
        price_usd = option_data.get('price_usd')
        if price_usd:
            return f"{float(price_usd):,.0f}"
        return "по запросу"
    
    def _format_price_rub(self, option_data: Dict[str, Any]) -> str:
        """Форматируем цену в рублях"""
        price_rub = option_data.get('final_price_rub') or option_data.get('price_rub')
        if price_rub:
            return f"{float(price_rub):,.0f}"
        return "по запросу"


# Создаем глобальный экземпляр менеджера шаблонов
kp_template_manager = KPTemplateManager()

