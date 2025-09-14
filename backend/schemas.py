from pydantic import BaseModel, EmailStr, validator
from enum import Enum
from typing import Optional, List, Any, Union
from datetime import date, datetime


class UserRole(str, Enum):
    admin = "admin"
    employee = "employee"
    forwarder = "forwarder"
    client = "client"


class TransportType(str, Enum):
    auto = "auto"
    rail = "rail"
    multimodal = "multimodal"
    sea = "sea"
    air = "air"


class CargoType(str, Enum):
    general = "general"
    consolidated = "consolidated"


class UserRegister(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    responsible_person: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    responsible_person: Optional[str] = None


class UserUpdate(BaseModel):
    role: Optional[UserRole] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    company_name: Optional[str] = None
    responsible_person: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    role: UserRole
    full_name: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    company_name: Optional[str]
    responsible_person: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DiscountOut(BaseModel):
    id: int
    user_id: int
    supplier_id: int
    discount_percent: float

    class Config:
        from_attributes = True


class RequestOut(BaseModel):
    id: int
    user_id: int
    request_data: dict
    created_at: datetime

    class Config:
        from_attributes = True


class CommercialOfferOut(BaseModel):
    id: int
    user_id: int
    request_id: Optional[int] = None
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True


class TariffArchiveOut(BaseModel):
    id: int
    original_tariff_id: int
    supplier_id: int
    transport_type: TransportType
    basis: str
    origin_country: Optional[str] = None
    origin_city: Optional[str] = None
    border_point: Optional[str] = None
    destination_country: Optional[str] = None
    destination_city: Optional[str] = None
    vehicle_type: Optional[str] = None
    price_rub: Optional[float] = None
    price_usd: Optional[float] = None
    validity_date: Optional[date] = None
    currency_conversion: Optional[float] = None
    transit_time_days: Optional[int] = None
    source_file: Optional[str] = None
    transit_port: Optional[str] = None
    departure_station: Optional[str] = None
    arrival_station: Optional[str] = None
    rail_tariff_rub: Optional[float] = None
    cbx_cost: Optional[float] = None
    terminal_handling_cost: Optional[float] = None
    auto_pickup_cost: Optional[float] = None
    security_cost: Optional[float] = None
    precarriage_cost: Optional[float] = None
    archived_at: datetime
    archive_reason: Optional[str] = None
    is_active: bool
    created_by_user_id: Optional[int] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    markup_percent: float = 0.0
    markup_fixed: float = 0.0
    template_type: Optional[str] = None


class SupplierOut(SupplierCreate):
    id: int

    class Config:
        from_attributes = True


class SupplierMarkupUpdate(BaseModel):
    markup_percent: Optional[float] = None
    markup_fixed: Optional[float] = None


class TariffIn(BaseModel):
    supplier_id: int
    transport_type: TransportType
    basis: str
    origin_country: Optional[str] = None
    origin_city: Optional[str] = None
    border_point: Optional[str] = None
    destination_country: Optional[str] = None
    destination_city: Optional[str] = None
    vehicle_type: Optional[str] = None
    price_rub: Optional[float] = None
    price_usd: Optional[float] = None
    validity_date: Optional[Union[date, str]] = None
    currency_conversion: Optional[float] = None
    transit_time_days: Optional[Union[int, float]] = None
    source_file: Optional[str] = None
    # Дополнительные поля для мультимодальных перевозок
    transit_port: Optional[str] = None
    departure_station: Optional[str] = None
    arrival_station: Optional[str] = None
    rail_tariff_rub: Optional[float] = None
    cbx_cost: Optional[float] = None
    terminal_handling_cost: Optional[float] = None
    auto_pickup_cost: Optional[float] = None
    security_cost: Optional[float] = None
    precarriage_cost: Optional[float] = None
    
    @validator('validity_date', pre=True)
    def parse_validity_date(cls, v):
        if v is None or isinstance(v, date):
            return v
        
        if isinstance(v, str):
            try:
                from datetime import datetime
                # Пробуем разные форматы даты
                for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        return datetime.strptime(v, fmt).date()
                    except ValueError:
                        continue
                # Если не удалось распарсить, возвращаем None
                return None
            except Exception:
                return None
        
        return v


class TariffOut(TariffIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ParsedTariffData(BaseModel):
    """Единый формат данных для парсинга тарифов"""
    transport_type: str = "auto"
    basis: str = "EXW"
    origin_country: str = ""
    origin_city: str = ""
    destination_country: str = ""
    destination_city: str = ""
    vehicle_type: str = ""
    price_rub: Optional[float] = None
    price_usd: Optional[float] = None
    validity_date: str = "дд.мм.гггг"
    transit_time_days: Optional[Union[int, float]] = None
    # Дополнительные поля
    transit_port: Optional[str] = None
    departure_station: Optional[str] = None
    arrival_station: Optional[str] = None
    rail_tariff_rub: Optional[float] = None
    cbx_cost: Optional[float] = None
    terminal_handling_cost: Optional[float] = None
    auto_pickup_cost: Optional[float] = None
    security_cost: Optional[float] = None
    precarriage_cost: Optional[float] = None

    @classmethod
    def from_dict(cls, data: dict):
        """Создает объект из словаря с обработкой пустых значений"""
        # Обрабатываем числовые поля
        price_rub = data.get("price_rub")
        if price_rub == "" or price_rub is None:
            price_rub = None
        elif isinstance(price_rub, str):
            try:
                price_rub = float(price_rub) if price_rub.strip() else None
            except (ValueError, AttributeError):
                price_rub = None
        
        price_usd = data.get("price_usd")
        if price_usd == "" or price_usd is None:
            price_usd = None
        elif isinstance(price_usd, str):
            try:
                price_usd = float(price_usd) if price_usd.strip() else None
            except (ValueError, AttributeError):
                price_usd = None
        
        transit_time_days = data.get("transit_time_days")
        if transit_time_days == "" or transit_time_days is None:
            transit_time_days = None
        elif isinstance(transit_time_days, str):
            try:
                transit_time_days = int(float(transit_time_days)) if transit_time_days.strip() else None
            except (ValueError, AttributeError):
                transit_time_days = None
        
        # Обрабатываем дополнительные числовые поля
        rail_tariff_rub = data.get("rail_tariff_rub")
        if rail_tariff_rub == "" or rail_tariff_rub is None:
            rail_tariff_rub = None
        elif isinstance(rail_tariff_rub, str):
            try:
                rail_tariff_rub = float(rail_tariff_rub) if rail_tariff_rub.strip() else None
            except (ValueError, AttributeError):
                rail_tariff_rub = None
        
        cbx_cost = data.get("cbx_cost")
        if cbx_cost == "" or cbx_cost is None:
            cbx_cost = None
        elif isinstance(cbx_cost, str):
            try:
                cbx_cost = float(cbx_cost) if cbx_cost.strip() else None
            except (ValueError, AttributeError):
                cbx_cost = None
        
        terminal_handling_cost = data.get("terminal_handling_cost")
        if terminal_handling_cost == "" or terminal_handling_cost is None:
            terminal_handling_cost = None
        elif isinstance(terminal_handling_cost, str):
            try:
                terminal_handling_cost = float(terminal_handling_cost) if terminal_handling_cost.strip() else None
            except (ValueError, AttributeError):
                terminal_handling_cost = None
        
        auto_pickup_cost = data.get("auto_pickup_cost")
        if auto_pickup_cost == "" or auto_pickup_cost is None:
            auto_pickup_cost = None
        elif isinstance(auto_pickup_cost, str):
            try:
                auto_pickup_cost = float(auto_pickup_cost) if auto_pickup_cost.strip() else None
            except (ValueError, AttributeError):
                auto_pickup_cost = None
        
        security_cost = data.get("security_cost")
        if security_cost == "" or security_cost is None:
            security_cost = None
        elif isinstance(security_cost, str):
            try:
                security_cost = float(security_cost) if security_cost.strip() else None
            except (ValueError, AttributeError):
                security_cost = None
        
        precarriage_cost = data.get("precarriage_cost")
        if precarriage_cost == "" or precarriage_cost is None:
            precarriage_cost = None
        elif isinstance(precarriage_cost, str):
            try:
                precarriage_cost = float(precarriage_cost) if precarriage_cost.strip() else None
            except (ValueError, AttributeError):
                precarriage_cost = None
        
        return cls(
            transport_type=data.get("transport_type", "auto"),
            basis=data.get("basis", "EXW"),
            origin_country=data.get("origin_country", ""),
            origin_city=data.get("origin_city", ""),
            destination_country=data.get("destination_country", ""),
            destination_city=data.get("destination_city", ""),
            vehicle_type=data.get("vehicle_type", ""),
            price_rub=price_rub,
            price_usd=price_usd,
            validity_date=data.get("validity_date", "дд.мм.гггг"),
            transit_time_days=transit_time_days,
            transit_port=data.get("transit_port"),
            departure_station=data.get("departure_station"),
            arrival_station=data.get("arrival_station"),
            rail_tariff_rub=rail_tariff_rub,
            cbx_cost=cbx_cost,
            terminal_handling_cost=terminal_handling_cost,
            auto_pickup_cost=auto_pickup_cost,
            security_cost=security_cost,
            precarriage_cost=precarriage_cost
        )

    class Config:
        from_attributes = True


class DiscountCreate(BaseModel):
    user_id: int
    supplier_id: int
    discount_percent: float


class DiscountUpdate(BaseModel):
    discount_percent: Optional[float] = None


class DiscountOut(DiscountCreate):
    id: int

    class Config:
        from_attributes = True


class SVHCreate(BaseModel):
    city: str
    name: str
    handling_cost: float


class SVHOut(SVHCreate):
    id: int

    class Config:
        from_attributes = True


class TruckingCreate(BaseModel):
    destination_city: str
    svh_id: int
    km_from_svh: float
    base_rate: float
    per_km_rate: float
    total_rate: Optional[float] = None


class TruckingOut(TruckingCreate):
    id: int

    class Config:
        from_attributes = True


class PrecarriageRailCreate(BaseModel):
    origin_city: str
    station: str
    km_from_station: float
    base_rate: float
    per_km_rate: float
    local_charges: Optional[float] = None
    total_rate: Optional[float] = None


class PrecarriageRailOut(PrecarriageRailCreate):
    id: int

    class Config:
        from_attributes = True


class PrecarriageSeaCreate(BaseModel):
    origin_city: str
    port: str
    km_from_port: float
    base_rate: float
    per_km_rate: float
    thc_port: Optional[float] = None
    total_rate: Optional[float] = None


class PrecarriageSeaOut(PrecarriageSeaCreate):
    id: int

    class Config:
        from_attributes = True


class RequestIn(BaseModel):
    request_data: Any


class RequestOut(RequestIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class OfferGenerateRequest(BaseModel):
    request: Any = None


class OfferOut(BaseModel):
    id: int
    user_id: int
    request_id: Optional[int] = None
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True


class CalculateRequest(BaseModel):
    cargo_kind: Optional[CargoType] = CargoType.general
    transport_type: TransportType
    basis: str
    origin_country: Optional[str] = None
    origin_city: Optional[str] = None
    destination_country: Optional[str] = None
    destination_city: Optional[str] = None
    vehicle_type: Optional[str] = None
    cargo_name: Optional[str] = None
    weight_kg: Optional[float] = None
    volume_m3: Optional[float] = None
    hs_code: Optional[str] = None
    border_point: Optional[str] = None
    customs_point: Optional[str] = None
    ready_date: Optional[str] = None
    shipments_count: Optional[int] = None
    special_conditions: Optional[str] = None
    suppliers: Optional[List[int]] = None


class CalculateOption(BaseModel):
    supplier_id: int
    supplier_name: str
    price_rub: float
    price_usd: Optional[float] = None
    markup_percent: float
    markup_fixed: float
    discount_percent: float
    final_price_rub: float
    validity_date: Optional[date] = None
    border_point: Optional[str] = None
    svh_name: Optional[str] = None
    arrival_station: Optional[str] = None
    departure_station: Optional[str] = None
    transit_time_days: Optional[Union[int, float]] = None
    # Дополнительные поля для детализации
    rail_tariff_rub: Optional[float] = None
    cbx_cost: Optional[float] = None
    auto_pickup_cost: Optional[float] = None
    terminal_handling_cost: Optional[float] = None
    security_cost: Optional[float] = None
    precarriage_cost: Optional[float] = None
    # Поля для авиаперевозок
    departure_airport: Optional[str] = None
    arrival_airport: Optional[str] = None
    air_tariff: Optional[float] = None
    # Поля для морских перевозок
    transit_port: Optional[str] = None
    arrival_port: Optional[str] = None


class CalculateMassRequest(BaseModel):
    requests: List[CalculateRequest]


class CurrencyRateCreate(BaseModel):
    currency_code: str
    rate: float
    date: date


class CurrencyRateOut(CurrencyRateCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

