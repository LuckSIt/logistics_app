import os
import logging
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7677223747:AAHNicNT5GoYmgXp3lo3zJNEnaChzadkrzk")

if not BOT_TOKEN or ":" not in BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set or invalid. Set env var BOT_TOKEN with your BotFather token.")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=["start"]) 
async def start(message: types.Message):
    welcome_text = """
🚛 Здравствуйте! Это бот Верес-Тариф.

Доступные команды:
/find - поиск тарифов
/calculate - расчёт стоимости доставки
/getkp - получить коммерческое предложение
/upload - загрузка тарифов (только для сотрудников)
/help - справка

Для расчёта стоимости отправьте данные в формате:
Тип транспорта, Базис, Город отправления, Город назначения, Вес (кг), Объём (м³)

Пример: авто, EXW, Москва, Санкт-Петербург, 1000, 5.5
    """
    await message.answer(welcome_text)


@dp.message_handler(commands=["help"]) 
async def help_cmd(message: types.Message):
    help_text = """
📋 Справка по командам:

/find - поиск тарифов по параметрам
/calculate - полный расчёт стоимости доставки
/getkp - генерация коммерческого предложения
/upload - загрузка файлов с тарифами (сотрудники)

📝 Форматы данных:

Поиск тарифов:
тип_транспорта, базис, город_отправления, город_назначения

Расчёт стоимости:
тип_транспорта, базис, город_отправления, город_назначения, вес_кг, объём_м³, наименование_груза

Типы транспорта: auto, rail, sea, multimodal, air
Базисы: EXW, FCA, FOB, CFR, CIF, CIP, CPT, DAP, DDP
    """
    await message.answer(help_text)


@dp.message_handler(commands=["find"]) 
async def find(message: types.Message):
    await message.answer("🔍 Отправьте параметры для поиска тарифов в формате:\nтип_транспорта, базис, город_отправления, город_назначения\n\nПример: auto, EXW, Москва, Санкт-Петербург")


@dp.message_handler(commands=["calculate"]) 
async def calculate(message: types.Message):
    await message.answer("🧮 Отправьте данные для расчёта в формате:\nтип_транспорта, базис, город_отправления, город_назначения, вес_кг, объём_м³, наименование_груза\n\nПример: auto, EXW, Москва, Санкт-Петербург, 1000, 5.5, Оборудование")


@dp.message_handler(lambda m: "," in m.text and m.text.count(",") >= 3)
async def handle_calculation_params(message: types.Message):
    try:
        parts = [p.strip() for p in message.text.split(",")]
        
        if len(parts) >= 4:
            # Поиск тарифов
            if len(parts) == 4:
                transport, basis, origin, dest = parts
                payload = {
                    "transport_type": transport.lower(),
                    "basis": basis.upper(),
                    "origin_city": origin,
                    "destination_city": dest,
                }
                endpoint = "/calculate/calculate"
            else:
                # Полный расчёт
                transport, basis, origin, dest, weight, volume, cargo_name = parts[:7]
                payload = {
                    "cargo_kind": "general",
                    "transport_type": transport.lower(),
                    "basis": basis.upper(),
                    "origin_city": origin,
                    "destination_city": dest,
                    "weight_kg": float(weight) if weight.replace('.', '').isdigit() else None,
                    "volume_m3": float(volume) if volume.replace('.', '').isdigit() else None,
                    "cargo_name": cargo_name,
                }
                endpoint = "/calculate/calculate"
            
            resp = requests.post(f"{API_BASE}{endpoint}", json=payload, timeout=30)
            if not resp.ok:
                await message.answer(f"❌ Ошибка при расчёте: {resp.status_code}")
                return
            
            data = resp.json()
            if not data:
                await message.answer("🔍 Тарифы не найдены для указанных параметров")
                return
            
            # Формируем ответ
            result_text = "📊 Результаты расчёта:\n\n"
            for i, tariff in enumerate(data[:5], 1):
                price = tariff.get('final_price_rub', 'по запросу')
                supplier = tariff.get('supplier_name', 'Неизвестно')
                validity = tariff.get('validity_date', 'Не указана')
                
                result_text += f"{i}. {supplier}\n"
                result_text += f"   💰 Стоимость: {price} ₽\n"
                result_text += f"   📅 Валидность: {validity}\n\n"
            
            # Кнопка для генерации КП
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("📄 Скачать КП", callback_data="generate_kp"))
            
            await message.answer(result_text, reply_markup=keyboard)
            
    except Exception as e:
        logging.error(f"Error in calculation: {e}")
        await message.answer("❌ Ошибка обработки запроса. Проверьте формат данных.")


@dp.callback_query_handler(lambda c: c.data == "generate_kp")
async def generate_kp_callback(callback_query: types.CallbackQuery):
    await callback_query.answer("📄 Генерация КП...")
    await callback_query.message.answer("📄 Для генерации коммерческого предложения используйте команду /getkp с параметрами расчёта")


@dp.message_handler(commands=["getkp"]) 
async def getkp(message: types.Message):
    await message.answer("📄 Для генерации коммерческого предложения отправьте данные в формате:\nтип_транспорта, базис, город_отправления, город_назначения, вес_кг, объём_м³, наименование_груза\n\nКП будет сгенерировано в формате PDF")


@dp.message_handler(commands=["upload"]) 
async def upload(message: types.Message):
    await message.answer("📤 Для загрузки тарифов отправьте файл (Excel, PDF, Word, изображение) и укажите ID поставщика в подписи к файлу.\n\nПример подписи: supplier_id: 1")


@dp.message_handler(content_types=[types.ContentTypes.DOCUMENT, types.ContentTypes.PHOTO])
async def handle_upload(message: types.Message):
    try:
        # Извлекаем supplier_id из подписи
        supplier_id = 1
        if message.caption:
            caption_lower = message.caption.lower()
            if "supplier_id:" in caption_lower:
                try:
                    supplier_id = int(caption_lower.split("supplier_id:")[1].strip().split()[0])
                except (ValueError, IndexError):
                    pass
        
        # Получаем файл
        if message.document:
            file_id = message.document.file_id
            file_name = message.document.file_name
        elif message.photo:
            file_id = message.photo[-1].file_id
            file_name = f"photo_{file_id}.jpg"
        else:
            await message.answer("❌ Неподдерживаемый тип файла")
            return
        
        # Скачиваем файл
        file = await bot.get_file(file_id)
        file_path = file.file_path
        url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        
        # Отправляем файл в API
        with requests.get(url, stream=True) as file_response:
            files = {"file": (file_name, file_response.content)}
            data = {"supplier_id": str(supplier_id)}
            
            resp = requests.post(f"{API_BASE}/tariffs/upload", data=data, files=files, timeout=60)
            
            if resp.ok:
                result = resp.json()
                if isinstance(result, list) and result:
                    await message.answer(f"✅ Файл успешно обработан!\n📊 Распознано записей: {len(result)}")
                else:
                    await message.answer("✅ Файл загружен, но данные не распознаны. Проверьте формат файла.")
            else:
                await message.answer(f"❌ Ошибка обработки файла: {resp.status_code}")
                
    except Exception as e:
        logging.error(f"Error in file upload: {e}")
        await message.answer("❌ Ошибка загрузки файла. Попробуйте позже.")


@dp.message_handler(commands=["status"])
async def status(message: types.Message):
    try:
        resp = requests.get(f"{API_BASE}/", timeout=5)
        if resp.ok:
            await message.answer("✅ Сервер работает нормально")
        else:
            await message.answer("⚠️ Сервер недоступен")
    except:
        await message.answer("❌ Сервер недоступен")


if __name__ == "__main__":
    logging.info("Starting Telegram bot...")
    executor.start_polling(dp, skip_updates=True)


