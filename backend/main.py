import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import users  # импортируем router
from backend.routers import auth, contractors, files, quotes, tariffs, reference, offers, currency, requests_history, discounts, text_extraction, auto_tariff, llm_parser
from backend.database import Base, engine
from backend import models

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backend.log')
    ]
)

# Ensure required directories exist
os.makedirs(os.path.join(os.path.dirname(__file__), "..", "uploaded_files"), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "..", "generated_docs"), exist_ok=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Верес-Тариф")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(contractors.router, prefix="/suppliers", tags=["Suppliers"])
app.include_router(files.router, prefix="/tariffs", tags=["Tariffs"])
app.include_router(tariffs.router, prefix="/tariffs", tags=["Tariffs"])
app.include_router(quotes.router, prefix="/calculate", tags=["Calculate"])
app.include_router(offers.router, prefix="/offers", tags=["Offers"])
app.include_router(reference.router, prefix="/reference", tags=["Reference"])
app.include_router(currency.router, prefix="/currency", tags=["Currency"])
app.include_router(requests_history.router, prefix="/requests", tags=["Requests"])
app.include_router(discounts.router, prefix="/discounts", tags=["Discounts"])
app.include_router(text_extraction.router, prefix="/text-extraction", tags=["Text Extraction"])
app.include_router(auto_tariff.router, prefix="/auto-tariff", tags=["Auto Tariff"])
app.include_router(llm_parser.router, prefix="/llm-parser", tags=["LLM Parser"])


@app.get("/")
def root():
    return {"message": "Верес-Тариф backend работает"}
