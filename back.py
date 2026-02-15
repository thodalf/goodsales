"""
Backend API FastAPI pour Deals Finder
Expose les endpoints pour récupérer les bonnes affaires
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import asyncio
import aiohttp
from datetime import datetime, timedelta
import json
from pathlib import Path
import hashlib

app = FastAPI(title="Deals Finder API", version="1.0.0")

# Configuration CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache en mémoire (en production : Redis)
cache = {}
CACHE_DURATION = timedelta(minutes=30)

# Modèles Pydantic
class Product(BaseModel):
    id: int
    title: str
    platform: str
    priceAverage: float
    priceSale: float
    discount: int
    location: str
    category: str
    seller: str
    postedHoursAgo: int
    emoji: str
    color: str
    url: Optional[str] = None
    image_url: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    location: Optional[str] = None
    platform: Optional[str] = None
    min_discount: int = 40
    max_results: int = 50

class StatsResponse(BaseModel):
    total_products: int
    good_deals_count: int
    average_discount: float
    total_savings: float
    platforms: Dict[str, int]
    categories: Dict[str, int]

# Base de données simulée (en production : PostgreSQL/MongoDB)
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
PRODUCTS_FILE = DATA_DIR / "products.json"

def load_products() -> List[Dict]:
    """Charge les produits depuis le fichier JSON"""
    if PRODUCTS_FILE.exists():
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_products(products: List[Dict]):
    """Sauvegarde les produits dans le fichier JSON"""
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

async def scrape_leboncoin(query: str, max_results: int = 20) -> List[Dict]:
    """
    Scrape Leboncoin (simulation pour la démo)
    En production : utiliser le scraper réel
    """
    print(f"🔍 Scraping Leboncoin pour: {query}")
    
    # Simulation de données (remplacer par le vrai scraper)
    products = []
    
    # Produits de base avec leurs prix moyens
    product_templates = {
        'iphone': {'avgPrice': 850, 'category': 'Téléphonie', 'emoji': '📱'},
        'macbook': {'avgPrice': 1600, 'category': 'Informatique', 'emoji': '💻'},
        'ps5': {'avgPrice': 450, 'category': 'Jeux vidéo', 'emoji': '🎮'},
        'jordan': {'avgPrice': 150, 'category': 'Chaussures', 'emoji': '👟'},
        'canapé': {'avgPrice': 700, 'category': 'Mobilier', 'emoji': '🛋️'},
    }
    
    # Trouver le template correspondant
    template = None
    for key, value in product_templates.items():
        if key in query.lower():
            template = value
            break
    
    if not template:
        template = {'avgPrice': 500, 'category': 'Divers', 'emoji': '📦'}
    
    # Générer des annonces avec variation de prix
    import random
    locations = ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Bordeaux', 'Nice']
    
    for i in range(max_results):
        # 30% de chance d'être une bonne affaire
        is_deal = random.random() < 0.3
        price_ratio = random.uniform(0.3, 0.6) if is_deal else random.uniform(0.75, 0.95)
        
        price = round(template['avgPrice'] * price_ratio)
        discount = round(((template['avgPrice'] - price) / template['avgPrice']) * 100)
        
        if discount < 40:  # On ne garde que les bonnes affaires
            continue
            
        products.append({
            'title': f"{query.title()} - Excellent état",
            'platform': 'leboncoin',
            'priceAverage': template['avgPrice'],
            'priceSale': price,
            'discount': discount,
            'location': random.choice(locations),
            'category': template['category'],
            'seller': f"User{random.randint(1000, 9999)}",
            'postedHoursAgo': random.randint(1, 48),
            'emoji': template['emoji'],
            'color': '#ff6e14',
            'url': f"https://www.leboncoin.fr/ad/{random.randint(1000000000, 9999999999)}"
        })
    
    await asyncio.sleep(0.5)  # Simulation du temps de scraping
    return products

async def scrape_vinted(query: str, max_results: int = 20) -> List[Dict]:
    """
    Scrape Vinted (simulation pour la démo)
    En production : utiliser le scraper réel ou l'API Vinted
    """
    print(f"🔍 Scraping Vinted pour: {query}")
    
    # Simulation similaire à Leboncoin
    products = []
    
    product_templates = {
        'nike': {'avgPrice': 120, 'category': 'Chaussures', 'emoji': '👟'},
        'zara': {'avgPrice': 80, 'category': 'Vêtements', 'emoji': '👔'},
        'sac': {'avgPrice': 200, 'category': 'Mode', 'emoji': '👜'},
        'pull': {'avgPrice': 60, 'category': 'Vêtements', 'emoji': '🧥'},
    }
    
    template = None
    for key, value in product_templates.items():
        if key in query.lower():
            template = value
            break
    
    if not template:
        template = {'avgPrice': 100, 'category': 'Mode', 'emoji': '👕'}
    
    import random
    locations = ['Paris', 'Lyon', 'Marseille', 'Lille', 'Nantes']
    
    for i in range(max_results):
        is_deal = random.random() < 0.35
        price_ratio = random.uniform(0.25, 0.55) if is_deal else random.uniform(0.75, 0.95)
        
        price = round(template['avgPrice'] * price_ratio)
        discount = round(((template['avgPrice'] - price) / template['avgPrice']) * 100)
        
        if discount < 40:
            continue
            
        products.append({
            'title': f"{query.title()} - Très bon état",
            'platform': 'vinted',
            'priceAverage': template['avgPrice'],
            'priceSale': price,
            'discount': discount,
            'location': random.choice(locations),
            'category': template['category'],
            'seller': f"VintedUser{random.randint(100, 999)}",
            'postedHoursAgo': random.randint(1, 72),
            'emoji': template['emoji'],
            'color': '#09b1ba',
            'url': f"https://www.vinted.fr/items/{random.randint(1000000, 9999999)}"
        })
    
    await asyncio.sleep(0.5)
    return products

async def scrape_all_platforms(query: str, platform: Optional[str] = None) -> List[Dict]:
    """
    Scrape toutes les plateformes ou une plateforme spécifique
    """
    tasks = []
    
    if platform is None or platform == 'all' or platform == 'leboncoin':
        tasks.append(scrape_leboncoin(query, max_results=25))
    
    if platform is None or platform == 'all' or platform == 'vinted':
        tasks.append(scrape_vinted(query, max_results=25))
    
    results = await asyncio.gather(*tasks)
    
    # Combiner et trier les résultats
    all_products = []
    product_id = 1
    
    for result in results:
        for product in result:
            product['id'] = product_id
            all_products.append(product)
            product_id += 1
    
    # Trier par discount décroissant
    all_products.sort(key=lambda x: x['discount'], reverse=True)
    
    return all_products

def get_cache_key(query: str, location: Optional[str], platform: Optional[str]) -> str:
    """Génère une clé de cache unique"""
    key = f"{query}_{location}_{platform}"
    return hashlib.md5(key.encode()).hexdigest()

# Endpoints de l'API

@app.get("/")
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "Deals Finder API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/api/search?query=...",
            "products": "/api/products",
            "stats": "/api/stats",
            "refresh": "/api/refresh?query=..."
        }
    }

@app.get("/api/products", response_model=List[Product])
async def get_products(
    query: Optional[str] = None,
    location: Optional[str] = None,
    category: Optional[str] = None,
    platform: Optional[str] = None,
    min_discount: int = Query(40, ge=0, le=100),
    max_results: int = Query(50, ge=1, le=200)
):
    """
    Récupère la liste des produits (bonnes affaires uniquement)
    """
    # Charger les produits existants
    products = load_products()
    
    # Filtrer selon les critères
    filtered = products
    
    if query:
        filtered = [p for p in filtered if query.lower() in p['title'].lower()]
    
    if location and location != 'all':
        filtered = [p for p in filtered if p['location'] == location]
    
    if category and category != 'all':
        filtered = [p for p in filtered if p['category'] == category]
    
    if platform and platform != 'all':
        filtered = [p for p in filtered if p['platform'] == platform]
    
    if min_discount:
        filtered = [p for p in filtered if p['discount'] >= min_discount]
    
    return filtered[:max_results]

@app.post("/api/search")
async def search_products(
    search_request: SearchRequest,
    background_tasks: BackgroundTasks
):
    """
    Lance une recherche et retourne les résultats
    Cache les résultats pendant 30 minutes
    """
    cache_key = get_cache_key(
        search_request.query,
        search_request.location,
        search_request.platform
    )
    
    # Vérifier le cache
    if cache_key in cache:
        cached_data, cached_time = cache[cache_key]
        if datetime.now() - cached_time < CACHE_DURATION:
            print(f"✅ Cache hit pour: {search_request.query}")
            return {
                "status": "success",
                "cached": True,
                "products": cached_data,
                "count": len(cached_data)
            }
    
    # Lancer le scraping
    print(f"🚀 Nouveau scraping pour: {search_request.query}")
    products = await scrape_all_platforms(
        search_request.query,
        search_request.platform
    )
    
    # Filtrer selon les critères
    if search_request.location and search_request.location != 'all':
        products = [p for p in products if p['location'] == search_request.location]
    
    products = [p for p in products if p['discount'] >= search_request.min_discount]
    products = products[:search_request.max_results]
    
    # Sauvegarder dans le cache
    cache[cache_key] = (products, datetime.now())
    
    # Sauvegarder dans la base de données (en arrière-plan)
    background_tasks.add_task(save_products, products)
    
    return {
        "status": "success",
        "cached": False,
        "products": products,
        "count": len(products),
        "scraped_at": datetime.now().isoformat()
    }

@app.get("/api/refresh")
async def refresh_data(
    query: str,
    platform: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    """
    Force le rafraîchissement des données (ignore le cache)
    """
    print(f"🔄 Refresh forcé pour: {query}")
    
    # Invalider le cache
    cache_key = get_cache_key(query, None, platform)
    if cache_key in cache:
        del cache[cache_key]
    
    # Lancer le scraping
    products = await scrape_all_platforms(query, platform)
    
    # Sauvegarder
    if background_tasks:
        background_tasks.add_task(save_products, products)
    else:
        save_products(products)
    
    return {
        "status": "success",
        "message": "Données rafraîchies",
        "count": len(products),
        "products": products
    }

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """
    Retourne les statistiques globales
    """
    products = load_products()
    
    if not products:
        return StatsResponse(
            total_products=0,
            good_deals_count=0,
            average_discount=0,
            total_savings=0,
            platforms={},
            categories={}
        )
    
    # Calculer les stats
    total_savings = sum(p['priceAverage'] - p['priceSale'] for p in products)
    avg_discount = sum(p['discount'] for p in products) / len(products)
    
    # Compter par plateforme
    platforms = {}
    for p in products:
        platforms[p['platform']] = platforms.get(p['platform'], 0) + 1
    
    # Compter par catégorie
    categories = {}
    for p in products:
        categories[p['category']] = categories.get(p['category'], 0) + 1
    
    return StatsResponse(
        total_products=len(products),
        good_deals_count=len([p for p in products if p['discount'] >= 50]),
        average_discount=round(avg_discount, 1),
        total_savings=round(total_savings, 2),
        platforms=platforms,
        categories=categories
    )

@app.get("/api/locations")
async def get_locations():
    """
    Retourne la liste des localisations disponibles
    """
    products = load_products()
    locations = sorted(list(set(p['location'] for p in products)))
    return {"locations": locations}

@app.get("/api/categories")
async def get_categories():
    """
    Retourne la liste des catégories disponibles
    """
    products = load_products()
    categories = sorted(list(set(p['category'] for p in products)))
    return {"categories": categories}

@app.get("/api/health")
async def health_check():
    """
    Vérification de santé de l'API
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cache_size": len(cache)
    }

if __name__ == "__main__":
    import uvicorn
    
    print("""
╔══════════════════════════════════════════╗
║   🚀 Deals Finder API Server             ║
║   Port: 8000                             ║
║   Docs: http://localhost:8000/docs       ║
╚══════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)