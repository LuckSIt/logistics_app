from sqlalchemy import Column, Integer, String, Enum, Float, Boolean, Date, DateTime, ForeignKey, Text, JSON as JSONType
from .database import Base
import enum
from datetime import datetime


class UserRole(str, enum.Enum):
    admin = "admin"
    employee = "employee"
    forwarder = "forwarder"
    client = "client"


class TransportType(str, enum.Enum):
    auto = "auto"
    air = "air"
    rail = "rail"
    multimodal = "multimodal"
    sea = "sea"


class CargoType(str, enum.Enum):
    general = "general"
    consolidated = "consolidated"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    company_name = Column(String, nullable=True)  # Наименование компании
    responsible_person = Column(String, nullable=True)  # Ответственное лицо
    is_active = Column(Boolean, default=True)  # Активен ли пользователь
    created_at = Column(DateTime, default=datetime.utcnow)


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    contact_person = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    markup_percent = Column(Float, default=0.0)
    markup_fixed = Column(Float, default=0.0)
    template_type = Column(String, nullable=True)  # Тип шаблона для парсинга


class Tariff(Base):
    __tablename__ = "tariffs"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), index=True, nullable=False)
    transport_type = Column(Enum(TransportType), index=True, nullable=False)
    basis = Column(String, nullable=False)
    origin_country = Column(String, nullable=True)
    origin_city = Column(String, nullable=True)
    border_point = Column(String, nullable=True)
    destination_country = Column(String, nullable=True)
    destination_city = Column(String, nullable=True)
    vehicle_type = Column(String, nullable=True)
    price_rub = Column(Float, nullable=True)
    price_usd = Column(Float, nullable=True)
    validity_date = Column(Date, nullable=True)
    currency_conversion = Column(Float, nullable=True)
    transit_time_days = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    source_file = Column(String, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)  # Кто создал тариф
    
    # Дополнительные поля для мультимодальных перевозок
    transit_port = Column(String, nullable=True)  # Транзитный порт
    departure_station = Column(String, nullable=True)  # Станция отправления
    arrival_station = Column(String, nullable=True)  # Станция прибытия
    rail_tariff_rub = Column(Float, nullable=True)  # ЖД тариф в рублях
    cbx_cost = Column(Float, nullable=True)  # Стоимость СВХ
    terminal_handling_cost = Column(Float, nullable=True)  # Стоимость терминальной обработки
    auto_pickup_cost = Column(Float, nullable=True)  # Стоимость автовывоза
    security_cost = Column(Float, nullable=True)  # Стоимость охраны
    precarriage_cost = Column(Float, nullable=True)  # Стоимость прекерридж


class TariffArchive(Base):
    __tablename__ = "tariff_archive"

    id = Column(Integer, primary_key=True, index=True)
    original_tariff_id = Column(Integer, ForeignKey("tariffs.id"), index=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), index=True, nullable=False)
    transport_type = Column(Enum(TransportType), index=True, nullable=False)
    basis = Column(String, nullable=False)
    origin_country = Column(String, nullable=True)
    origin_city = Column(String, nullable=True)
    border_point = Column(String, nullable=True)
    destination_country = Column(String, nullable=True)
    destination_city = Column(String, nullable=True)
    vehicle_type = Column(String, nullable=True)
    price_rub = Column(Float, nullable=True)
    price_usd = Column(Float, nullable=True)
    validity_date = Column(Date, nullable=True)
    currency_conversion = Column(Float, nullable=True)
    transit_time_days = Column(Integer, nullable=True)
    source_file = Column(String, nullable=True)
    
    # Дополнительные поля для мультимодальных перевозок
    transit_port = Column(String, nullable=True)
    departure_station = Column(String, nullable=True)
    arrival_station = Column(String, nullable=True)
    rail_tariff_rub = Column(Float, nullable=True)
    cbx_cost = Column(Float, nullable=True)
    terminal_handling_cost = Column(Float, nullable=True)
    auto_pickup_cost = Column(Float, nullable=True)
    security_cost = Column(Float, nullable=True)
    precarriage_cost = Column(Float, nullable=True)
    
    # Метаданные архива
    archived_at = Column(DateTime, default=datetime.utcnow)
    archive_reason = Column(String, nullable=True)  # Причина архивирования
    is_active = Column(Boolean, default=True)  # Активен ли архивный тариф
    created_by_user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)  # Кто создал тариф


class Discount(Base):
    __tablename__ = "discounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), index=True, nullable=False)
    discount_percent = Column(Float, default=0.0)


class AuxiliarySVH(Base):
    __tablename__ = "auxiliary_svh"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=False)
    name = Column(String, nullable=False)
    handling_cost = Column(Float, nullable=False)


class AuxiliaryTrucking(Base):
    __tablename__ = "auxiliary_trucking"

    id = Column(Integer, primary_key=True, index=True)
    destination_city = Column(String, nullable=False)
    svh_id = Column(Integer, ForeignKey("auxiliary_svh.id"), index=True, nullable=False)
    km_from_svh = Column(Float, nullable=False)
    base_rate = Column(Float, nullable=False)
    per_km_rate = Column(Float, nullable=False)
    total_rate = Column(Float, nullable=True)  # Вычисляемое поле


class AuxiliaryPrecarriageRail(Base):
    __tablename__ = "auxiliary_precarriage_rail"

    id = Column(Integer, primary_key=True, index=True)
    origin_city = Column(String, nullable=False)
    station = Column(String, nullable=False)
    km_from_station = Column(Float, nullable=False)
    base_rate = Column(Float, nullable=False)
    per_km_rate = Column(Float, nullable=False)
    local_charges = Column(Float, nullable=True)
    total_rate = Column(Float, nullable=True)  # Вычисляемое поле


class AuxiliaryPrecarriageSea(Base):
    __tablename__ = "auxiliary_precarriage_sea"

    id = Column(Integer, primary_key=True, index=True)
    origin_city = Column(String, nullable=False)
    port = Column(String, nullable=False)
    km_from_port = Column(Float, nullable=False)
    base_rate = Column(Float, nullable=False)
    per_km_rate = Column(Float, nullable=False)
    thc_port = Column(Float, nullable=True)  # Terminal Handling Charges
    total_rate = Column(Float, nullable=True)  # Вычисляемое поле


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    request_data = Column(JSONType, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CommercialOffer(Base):
    __tablename__ = "commercial_offers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    request_id = Column(Integer, ForeignKey("requests.id"), index=True, nullable=True)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CurrencyRate(Base):
    __tablename__ = "currency_rates"

    id = Column(Integer, primary_key=True, index=True)
    currency_code = Column(String, nullable=False)  # USD, EUR, CNY
    rate = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
