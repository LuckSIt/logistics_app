"""
Сервис для работы с архивом тарифов
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from .. import models
from ..schemas import TransportType


class TariffArchiveService:
    """Сервис для управления архивом тарифов"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def archive_tariff(self, tariff: models.Tariff, reason: str = "Создание нового тарифа") -> models.TariffArchive:
        """
        Архивирует тариф, создавая копию в архиве
        
        Args:
            tariff: Тариф для архивирования
            reason: Причина архивирования
            
        Returns:
            Архивированный тариф
        """
        # Создаем архивную копию тарифа
        archived_tariff = models.TariffArchive(
            original_tariff_id=tariff.id,
            supplier_id=tariff.supplier_id,
            transport_type=tariff.transport_type,
            basis=tariff.basis,
            origin_country=tariff.origin_country,
            origin_city=tariff.origin_city,
            border_point=tariff.border_point,
            destination_country=tariff.destination_country,
            destination_city=tariff.destination_city,
            vehicle_type=tariff.vehicle_type,
            price_rub=tariff.price_rub,
            price_usd=tariff.price_usd,
            validity_date=tariff.validity_date,
            currency_conversion=tariff.currency_conversion,
            transit_time_days=tariff.transit_time_days,
            source_file=tariff.source_file,
            transit_port=tariff.transit_port,
            departure_station=tariff.departure_station,
            arrival_station=tariff.arrival_station,
            rail_tariff_rub=tariff.rail_tariff_rub,
            cbx_cost=tariff.cbx_cost,
            terminal_handling_cost=tariff.terminal_handling_cost,
            auto_pickup_cost=tariff.auto_pickup_cost,
            security_cost=tariff.security_cost,
            precarriage_cost=tariff.precarriage_cost,
            archive_reason=reason,
            is_active=True,
            created_by_user_id=tariff.created_by_user_id
        )
        
        self.db.add(archived_tariff)
        self.db.commit()
        self.db.refresh(archived_tariff)
        
        return archived_tariff
    
    def get_archived_tariffs(
        self,
        transport_type: Optional[TransportType] = None,
        basis: Optional[str] = None,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None,
        vehicle_type: Optional[str] = None,
        supplier_id: Optional[int] = None,
        is_active: bool = True
    ) -> List[models.TariffArchive]:
        """
        Получает архивные тарифы по критериям
        
        Args:
            transport_type: Тип транспорта
            basis: Базис поставки
            origin_city: Город отправления
            destination_city: Город назначения
            vehicle_type: Тип транспортной единицы
            supplier_id: ID поставщика
            is_active: Активен ли тариф
            
        Returns:
            Список архивных тарифов
        """
        query = self.db.query(models.TariffArchive).filter(
            models.TariffArchive.is_active == is_active
        )
        
        if transport_type:
            query = query.filter(models.TariffArchive.transport_type == transport_type)
        if basis:
            query = query.filter(models.TariffArchive.basis == basis)
        if origin_city:
            query = query.filter(models.TariffArchive.origin_city == origin_city)
        if destination_city:
            query = query.filter(models.TariffArchive.destination_city == destination_city)
        if vehicle_type:
            query = query.filter(models.TariffArchive.vehicle_type == vehicle_type)
        if supplier_id:
            query = query.filter(models.TariffArchive.supplier_id == supplier_id)
        
        return query.order_by(models.TariffArchive.archived_at.desc()).all()
    
    def get_archived_tariff_by_id(self, archive_id: int) -> Optional[models.TariffArchive]:
        """Получает архивный тариф по ID"""
        return self.db.query(models.TariffArchive).filter(
            models.TariffArchive.id == archive_id,
            models.TariffArchive.is_active == True
        ).first()
    
    def deactivate_archived_tariff(self, archive_id: int) -> bool:
        """Деактивирует архивный тариф"""
        archived_tariff = self.get_archived_tariff_by_id(archive_id)
        if archived_tariff:
            archived_tariff.is_active = False
            self.db.commit()
            return True
        return False
    
    def get_latest_archived_tariff(
        self,
        transport_type: TransportType,
        basis: str,
        origin_city: str,
        destination_city: str,
        vehicle_type: Optional[str] = None,
        supplier_id: Optional[int] = None
    ) -> Optional[models.TariffArchive]:
        """
        Получает последний архивный тариф по критериям
        
        Args:
            transport_type: Тип транспорта
            basis: Базис поставки
            origin_city: Город отправления
            destination_city: Город назначения
            vehicle_type: Тип транспортной единицы
            supplier_id: ID поставщика
            
        Returns:
            Последний архивный тариф или None
        """
        query = self.db.query(models.TariffArchive).filter(
            models.TariffArchive.transport_type == transport_type,
            models.TariffArchive.basis == basis,
            models.TariffArchive.origin_city == origin_city,
            models.TariffArchive.destination_city == destination_city,
            models.TariffArchive.is_active == True
        )
        
        if vehicle_type:
            query = query.filter(models.TariffArchive.vehicle_type == vehicle_type)
        if supplier_id:
            query = query.filter(models.TariffArchive.supplier_id == supplier_id)
        
        return query.order_by(models.TariffArchive.archived_at.desc()).first()
    
    def archive_tariffs_batch(self, tariffs: List[models.Tariff], reason: str = "Массовое архивирование") -> List[models.TariffArchive]:
        """
        Архивирует несколько тарифов одновременно
        
        Args:
            tariffs: Список тарифов для архивирования
            reason: Причина архивирования
            
        Returns:
            Список архивных тарифов
        """
        archived_tariffs = []
        
        for tariff in tariffs:
            archived_tariff = self.archive_tariff(tariff, reason)
            archived_tariffs.append(archived_tariff)
        
        return archived_tariffs
