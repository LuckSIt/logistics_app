from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
import models, schemas
from services.security import get_current_user, can_choose_transport, can_download_kp
from services import cbr
from services.tariff_archive import TariffArchiveService

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=List[schemas.CalculateOption])
def calculate_quote(request: schemas.CalculateRequest, current: models.User = Depends(can_choose_transport), db: Session = Depends(get_db)):
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Запрос на расчет: transport_type={request.transport_type}, basis={request.basis}, origin_city={request.origin_city}, destination_city={request.destination_city}")
    
    query = db.query(models.Tariff).filter(
        models.Tariff.transport_type == request.transport_type,
    )
    if request.basis:
        query = query.filter(models.Tariff.basis == request.basis)
    if request.origin_city:
        query = query.filter(models.Tariff.origin_city == request.origin_city)
    if request.destination_city:
        query = query.filter(models.Tariff.destination_city == request.destination_city)
    if request.vehicle_type:
        query = query.filter(models.Tariff.vehicle_type == request.vehicle_type)
    if request.suppliers:
        query = query.filter(models.Tariff.supplier_id.in_(request.suppliers))

    tariffs = query.all()
    logger.info(f"Найдено активных тарифов: {len(tariffs)}")
    
    # Если активных тарифов мало, ищем в архиве
    archive_service = TariffArchiveService(db)
    archived_tariffs = []
    
    if len(tariffs) < 3:  # Если активных тарифов меньше 3, ищем в архиве
        logger.info("Ищем дополнительные тарифы в архиве...")
        archived_tariffs = archive_service.get_archived_tariffs(
            transport_type=request.transport_type,
            basis=request.basis,
            origin_city=request.origin_city,
            destination_city=request.destination_city,
            vehicle_type=request.vehicle_type,
            supplier_id=request.suppliers[0] if request.suppliers else None
        )
        logger.info(f"Найдено архивных тарифов: {len(archived_tariffs)}")
    
    # Проверим все тарифы в базе для отладки
    all_tariffs = db.query(models.Tariff).all()
    logger.info(f"Всего активных тарифов в базе: {len(all_tariffs)}")
    if all_tariffs:
        sample_tariff = all_tariffs[0]
        logger.info(f"Пример тарифа: transport_type={sample_tariff.transport_type}, basis={sample_tariff.basis}, origin_city={sample_tariff.origin_city}, destination_city={sample_tariff.destination_city}")
    
    suppliers = {s.id: s for s in db.query(models.Supplier).all()}

    discounts = db.query(models.Discount).filter(models.Discount.user_id == current.id).all()
    discount_map = {(d.supplier_id): float(d.discount_percent or 0.0) for d in discounts}

    results: List[schemas.CalculateOption] = []
    
    # Обрабатываем активные тарифы
    for t in tariffs:
        supplier = suppliers.get(t.supplier_id)
        if not supplier:
            continue

        # Базовый расчёт в зависимости от типа транспорта
        base_usd = float(t.price_usd) if t.price_usd is not None else None
        base_rub = float(t.price_rub) if t.price_rub is not None else None
        
        # Конвертация валют если необходимо
        if base_usd is not None and base_rub is None:
            try:
                rate = cbr.get_usd_rate()
                base_rub = base_usd * rate
            except Exception as e:
                base_rub = base_usd * 95.0  # Fallback курс
        elif base_rub is None:
            continue

        # Расчёт дополнительных затрат согласно ТЗ
        aux_costs = calculate_auxiliary_costs(request, t, db)
        
        # Итоговая стоимость в зависимости от типа транспорта
        if request.transport_type == models.TransportType.auto:
            # Автомобильная доставка: базовая стоимость + автовывоз
            final_price_rub = base_rub + aux_costs.get('auto_pickup', 0)
            
        elif request.transport_type == models.TransportType.rail:
            # ЖД доставка: USD + СВХ + автовывоз
            rail_tariff_rub = t.rail_tariff_rub or base_rub
            cbx_cost = aux_costs.get('cbx_cost', 0)
            auto_pickup = aux_costs.get('auto_pickup', 0)
            final_price_rub = rail_tariff_rub + cbx_cost + auto_pickup
            
        elif request.transport_type == models.TransportType.multimodal:
            # Мультимодальная доставка: USD + СВХ + автовывоз
            multimodal_tariff_rub = t.rail_tariff_rub or base_rub
            cbx_cost = aux_costs.get('cbx_cost', 0)
            auto_pickup = aux_costs.get('auto_pickup', 0)
            final_price_rub = multimodal_tariff_rub + cbx_cost + auto_pickup
            
        elif request.transport_type == models.TransportType.sea:
            # Морская доставка: USD + СВХ + автовывоз
            sea_tariff_rub = base_rub
            cbx_cost = aux_costs.get('cbx_cost', 0)
            auto_pickup = aux_costs.get('auto_pickup', 0)
            final_price_rub = sea_tariff_rub + cbx_cost + auto_pickup
            
        else:  # air
            final_price_rub = base_rub

        # Применение наценок и скидок
        markup_percent = float(supplier.markup_percent or 0.0)
        markup_fixed = float(supplier.markup_fixed or 0.0)
        discount_percent = discount_map.get(supplier.id, 0.0)

        price_with_markup = final_price_rub * (1.0 + markup_percent / 100.0) + markup_fixed
        final = price_with_markup * (1.0 - discount_percent / 100.0)

        # Получение дополнительной информации для КП
        border_point = t.border_point or request.border_point
        svh_name = get_svh_name(request.destination_city, db)
        arrival_station = t.arrival_station

        results.append(
            schemas.CalculateOption(
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                price_rub=round(final_price_rub, 2),
                price_usd=base_usd,
                markup_percent=markup_percent,
                markup_fixed=markup_fixed,
                discount_percent=discount_percent,
                final_price_rub=round(final, 2),
                validity_date=t.validity_date,
                border_point=border_point,
                svh_name=svh_name,
                arrival_station=arrival_station,
                transit_time_days=t.transit_time_days,
                # Дополнительные поля для детализации
                rail_tariff_rub=t.rail_tariff_rub,
                cbx_cost=aux_costs.get('cbx_cost', 0),
                auto_pickup_cost=aux_costs.get('auto_pickup', 0),
                terminal_handling_cost=aux_costs.get('terminal_handling', 0),
                security_cost=t.security_cost,
                precarriage_cost=aux_costs.get('precarriage', 0),
            )
        )

    # Обрабатываем архивные тарифы (если активных мало)
    for archived_tariff in archived_tariffs[:5]:  # Берем только первые 5 архивных тарифов
        supplier = suppliers.get(archived_tariff.supplier_id)
        if not supplier:
            continue

        # Базовый расчёт для архивного тарифа
        base_usd = float(archived_tariff.price_usd) if archived_tariff.price_usd is not None else None
        base_rub = float(archived_tariff.price_rub) if archived_tariff.price_rub is not None else None
        
        # Конвертация валют если необходимо
        if base_usd is not None and base_rub is None:
            try:
                rate = cbr.get_usd_rate()
                base_rub = base_usd * rate
            except Exception as e:
                base_rub = base_usd * 95.0  # Fallback курс
        elif base_rub is None:
            continue

        # Расчёт дополнительных затрат для архивного тарифа
        aux_costs = calculate_auxiliary_costs_for_archived(request, archived_tariff, db)
        
        # Итоговая стоимость в зависимости от типа транспорта
        if request.transport_type == models.TransportType.auto:
            final_price_rub = base_rub + aux_costs.get('auto_pickup', 0)
        elif request.transport_type == models.TransportType.rail:
            final_price_rub = base_rub + aux_costs.get('terminal_handling', 0)
        elif request.transport_type == models.TransportType.sea:
            final_price_rub = base_rub + aux_costs.get('cbx_cost', 0) + aux_costs.get('terminal_handling', 0)
        elif request.transport_type == models.TransportType.air:
            final_price_rub = base_rub + aux_costs.get('terminal_handling', 0)
        else:  # multimodal
            final_price_rub = base_rub + aux_costs.get('cbx_cost', 0) + aux_costs.get('terminal_handling', 0) + aux_costs.get('auto_pickup', 0)

        # Применяем наценки и скидки
        markup_percent = float(supplier.markup_percent or 0.0)
        markup_fixed = float(supplier.markup_fixed or 0.0)
        discount_percent = discount_map.get(supplier.id, 0.0)
        
        final = final_price_rub * (1 + markup_percent / 100) + markup_fixed
        final = final * (1 - discount_percent / 100)

        # Дополнительные поля
        border_point = archived_tariff.border_point or request.border_point
        svh_name = None
        arrival_station = archived_tariff.arrival_station

        results.append(
            schemas.CalculateOption(
                supplier_id=supplier.id,
                supplier_name=f"{supplier.name} (архив)",
                price_rub=round(final_price_rub, 2),
                price_usd=base_usd,
                markup_percent=markup_percent,
                markup_fixed=markup_fixed,
                discount_percent=discount_percent,
                final_price_rub=round(final, 2),
                validity_date=archived_tariff.validity_date,
                border_point=border_point,
                svh_name=svh_name,
                arrival_station=arrival_station,
                transit_time_days=archived_tariff.transit_time_days,
                # Дополнительные поля для детализации
                rail_tariff_rub=archived_tariff.rail_tariff_rub,
                cbx_cost=aux_costs.get('cbx_cost', 0),
                auto_pickup_cost=aux_costs.get('auto_pickup', 0),
                terminal_handling_cost=aux_costs.get('terminal_handling', 0),
                security_cost=archived_tariff.security_cost,
                precarriage_cost=aux_costs.get('precarriage', 0),
            )
        )

    # Удаляем дубликаты (часто активный и архивный тариф совпадают)
    unique: List[schemas.CalculateOption] = []
    seen = set()
    for opt in results:
        key = (
            opt.supplier_id,
            round(opt.final_price_rub or 0, 2),
            round(opt.price_usd or 0, 2) if opt.price_usd is not None else 0,
            opt.border_point or "",
            opt.arrival_station or "",
            request.transport_type.value,
            request.basis or "",
            request.origin_city or "",
            request.destination_city or "",
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(opt)

    unique.sort(key=lambda x: x.final_price_rub)
    return unique


def calculate_auxiliary_costs_for_archived(request: schemas.CalculateRequest, archived_tariff: models.TariffArchive, db: Session) -> dict:
    """Расчёт вспомогательных затрат для архивных тарифов"""
    costs = {}
    
    # СВХ (таблица auxiliary_svh)
    svh_records = db.query(models.AuxiliarySVH).filter(
        models.AuxiliarySVH.city == (request.destination_city or archived_tariff.destination_city)
    ).all()
    if svh_records:
        costs['cbx_cost'] = min([float(svh.handling_cost) for svh in svh_records])
    
    # Терминальная обработка - используем данные из архива
    if archived_tariff.terminal_handling_cost:
        costs['terminal_handling'] = float(archived_tariff.terminal_handling_cost)
    
    # Автовывоз - используем данные из архива
    if archived_tariff.auto_pickup_cost:
        costs['auto_pickup'] = float(archived_tariff.auto_pickup_cost)
    
    # Прекерридж - используем данные из архива
    if archived_tariff.precarriage_cost:
        costs['precarriage'] = float(archived_tariff.precarriage_cost)
    
    return costs


def calculate_auxiliary_costs(request: schemas.CalculateRequest, tariff: models.Tariff, db: Session) -> dict:
    """Расчёт вспомогательных затрат согласно таблицам из ТЗ"""
    costs = {}
    
    # СВХ (таблица auxiliary_svh)
    svh_records = db.query(models.AuxiliarySVH).filter(
        models.AuxiliarySVH.city == (request.destination_city or tariff.destination_city)
    ).all()
    if svh_records:
        costs['cbx_cost'] = min([float(svh.handling_cost) for svh in svh_records])
    
    # Автовывоз (таблица auxiliary_trucking)
    trucking_records = db.query(models.AuxiliaryTrucking).filter(
        models.AuxiliaryTrucking.destination_city == (request.destination_city or tariff.destination_city)
    ).all()
    if trucking_records:
        svh_by_id = {s.id: s for s in db.query(models.AuxiliarySVH).all()}
        totals = []
        for trucking in trucking_records:
            svh = svh_by_id.get(trucking.svh_id)
            svh_cost = float(svh.handling_cost) if svh else 0.0
            total = (float(trucking.base_rate or 0) + 
                    float(trucking.per_km_rate or 0) * float(trucking.km_from_svh or 0) + 
                    svh_cost)
            totals.append(total)
        if totals:
            costs['auto_pickup'] = min(totals)
    
    # Прекерридж ЖД (таблица auxiliary_precarriage_rail)
    if request.transport_type == models.TransportType.rail:
        precarriage_rail = db.query(models.AuxiliaryPrecarriageRail).filter(
            models.AuxiliaryPrecarriageRail.origin_city == (request.origin_city or tariff.origin_city)
        ).all()
        if precarriage_rail:
            totals = []
            for pr in precarriage_rail:
                total = (float(pr.base_rate or 0) + 
                        float(pr.per_km_rate or 0) * float(pr.km_from_station or 0) + 
                        float(pr.local_charges or 0))
                totals.append(total)
            if totals:
                costs['precarriage'] = min(totals)
    
    # Прекерридж море и мультимодальные (таблица auxiliary_precarriage_sea)
    if request.transport_type in [models.TransportType.sea, models.TransportType.multimodal]:
        precarriage_sea = db.query(models.AuxiliaryPrecarriageSea).filter(
            models.AuxiliaryPrecarriageSea.origin_city == (request.origin_city or tariff.origin_city)
        ).all()
        if precarriage_sea:
            totals = []
            for ps in precarriage_sea:
                total = (float(ps.base_rate or 0) + 
                        float(ps.per_km_rate or 0) * float(ps.km_from_port or 0) + 
                        float(ps.thc_port or 0))
                totals.append(total)
            if totals:
                costs['precarriage'] = min(totals)
    
    # Терминальная обработка
    if tariff.terminal_handling_cost:
        costs['terminal_handling'] = float(tariff.terminal_handling_cost)
    
    return costs


def get_svh_name(city: str, db: Session) -> str:
    """Получение названия СВХ для города"""
    if not city:
        return None
    svh = db.query(models.AuxiliarySVH).filter(models.AuxiliarySVH.city == city).first()
    return svh.name if svh else None


@router.post("/calculate/mass")
def calculate_mass(request: schemas.CalculateMassRequest, current: models.User = Depends(can_choose_transport), db: Session = Depends(get_db)):
    all_results = []
    for r in request.requests:
        all_results.append(calculate_quote(r, current, db))
    return all_results


