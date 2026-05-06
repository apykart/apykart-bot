#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     █████╗ ██████╗ ██╗   ██╗██╗  ██╗ █████╗ ██████╗ ████████╗     ║
║    ██╔══██╗██╔══██╗╚██╗ ██╔╝██║ ██╔╝██╔══██╗██╔══██╗╚══██╔══╝     ║
║    ███████║██████╔╝ ╚████╔╝ █████╔╝ ███████║██████╔╝   ██║        ║
║    ██╔══██║██╔═══╝   ╚██╔╝  ██╔═██╗ ██╔══██║██╔══██╗   ██║        ║
║    ██║  ██║██║        ██║   ██║  ██╗██║  ██║██║  ██║   ██║        ║
║    ╚═╝  ╚═╝╚═╝        ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝        ║
║                                                                  ║
║              APYKART FULLY AUTOMATED BOT v9.0                    ║
║     Auto Discover | Auto Search | Auto Send | Auto Everything    ║
╚══════════════════════════════════════════════════════════════════╝
"""

from telethon import TelegramClient, events, Button, functions, errors
import asyncio
import random
import sqlite3
import re
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
from bs4 import BeautifulSoup
import traceback

# ============================================
# CONFIGURATION
# ============================================

@dataclass
class Config:
    # Telegram API Credentials
    api_id: int = 39028284
    api_hash: str = "118a1ab2ca7e9c9b3b3e70cc4a72d70a"
    bot_token: str = "8707772379:AAFbQyKNbcDql-cPqEj0wxGs_ZkZsJIo2tw"
    
    # ApyKart Links
    website: str = "https://apykart.vercel.app"
    api_url: str = "https://apykart.vercel.app/api/products"
    products_page: str = "https://apykart.vercel.app/products"
    app_link: str = "https://apykart.vercel.app/download"
    seller_link: str = "https://apykart.vercel.app/seller"
    
    # Bot Settings
    message_gap_seconds: int = 90
    search_gap_seconds: int = 30
    cycle_hours: int = 3
    max_groups_per_search: int = 30
    max_products_per_cycle: int = 10
    
    # Auto Discovery Settings
    auto_discover_keywords: bool = True
    keywords_update_interval: int = 6  # hours
    max_keywords: int = 100
    
    # Features
    enable_marketing: bool = True
    enable_auto_restart: bool = True
    enable_background_service: bool = True
    
    # Database
    db_path: str = "apykart_v9.db"
    log_level: str = "INFO"
    
    # Auto Restart
    auto_restart_hours: int = 24


# ============================================
# BASE SEARCH KEYWORDS (Starting point)
# ============================================

BASE_SEARCH_QUERIES = [
    "online shopping india", "shopping group india", "buy sell india",
    "shopping lovers india", "shopping haul india", "fashion shopping india",
    "electronics deals", "mobile accessories", "gadgets lovers",
    "tech shopping india", "gadget deals india", "electronics shopping",
    "deal of the day", "coupon offers india", "flipkart amazon deals",
    "best deals india", "sale alert india", "discount offers india",
    "doston ke saath", "free shopping deals", "cashback offers",
    "product review india", "shopping community india", "new products india",
]

# ============================================
# MESSAGE TEMPLATES
# ============================================

MESSAGE_TEMPLATES = [
    """🛍️ NEW PRODUCT ALERT - ApyKart 🛍️

✨ Product: {product_name}
💰 Price: {product_price}
🔗 Buy Now: {product_link}

📲 Download App: {app_link}
🌐 Website: {website}

✅ Free Shipping on ₹499+
💵 COD Available
🔄 7-Day Easy Returns

🎁 Use Code: WELCOME20 for 20% OFF""",

    """🎯 JUST ARRIVED at ApyKart 🎯

🛍️ Product: {product_name}
💵 Price: {product_price}
🔗 Link: {product_link}

📱 Get App: {app_link}
🌐 Website: {website}

✨ Free Shipping on ₹499+
💵 Pay with COD
🎁 Welcome Code: WELCOME20""",

    """🔥 FLASH SALE at ApyKart 🔥

📱 Product: {product_name}
💵 Price: {product_price}
👉 Link: {product_link}

📲 App Exclusive: {app_link}
🛍️ Shop More: {website}/products

⏰ Limited Period Offer
🚚 Free Shipping | COD Available""",

    """💝 BEST PRICE ALERT 💝

✨ Product: {product_name}
💰 Price: {product_price}
🔗 Link: {product_link}

📱 Download App: {app_link}
🎁 Extra 10% OFF on App

✅ COD Available | Free Shipping ₹499+""",

    """📦 SELL ON APYKART 📦

✨ Seller Benefits:
• Free Registration
• Zero Commission (3 Months)
• Pan India Delivery
• Weekly Payouts
• Seller Dashboard
• 24/7 Support

🔗 Register Now: {seller_link}

🛒 Shop: {website}/products
📱 App: {app_link}

🚀 5000+ Sellers Already Joined""",

    """📱 DOWNLOAD APYKART APP 📱

✨ App Benefits:
• Extra 10% OFF on first order
• Early access to sales
• Faster checkout
• Exclusive app offers
• Push notifications

📲 Download Now: {app_link}

🛍️ Website: {website}
🎁 Code: WELCOME20""",
]


# ============================================
# DATABASE MANAGER (Enhanced)
# ============================================

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def _create_tables(self):
        # Groups table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_groups (
                group_id TEXT PRIMARY KEY,
                group_name TEXT,
                members INTEGER DEFAULT 0,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Products table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_products (
                product_id TEXT PRIMARY KEY,
                product_name TEXT,
                product_link TEXT,
                product_price TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Keywords table (for auto discovery)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                keyword TEXT PRIMARY KEY,
                source TEXT,
                search_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                referrer_id INTEGER,
                coins INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Referrals table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                user_id INTEGER PRIMARY KEY,
                total_referrals INTEGER DEFAULT 0,
                earned_credits INTEGER DEFAULT 0
            )
        ''')
        
        # Statistics table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_number INTEGER,
                products_found INTEGER,
                groups_found INTEGER,
                messages_sent INTEGER,
                keywords_used INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    # ========== Group Methods ==========
    def is_group_sent(self, group_id: str) -> bool:
        self.cursor.execute("SELECT 1 FROM sent_groups WHERE group_id = ?", (group_id,))
        return self.cursor.fetchone() is not None
    
    def add_sent_group(self, group_id: str, group_name: str, members: int = 0):
        self.cursor.execute(
            "INSERT OR IGNORE INTO sent_groups (group_id, group_name, members) VALUES (?, ?, ?)",
            (group_id, group_name, members)
        )
        self.conn.commit()
    
    def get_total_groups(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM sent_groups")
        return self.cursor.fetchone()[0]
    
    # ========== Product Methods ==========
    def is_product_sent(self, product_link: str) -> bool:
        self.cursor.execute("SELECT 1 FROM sent_products WHERE product_link = ?", (product_link,))
        return self.cursor.fetchone() is not None
    
    def add_sent_product(self, product_link: str, product_name: str, product_price: str):
        product_id = str(hash(product_link))
        self.cursor.execute(
            "INSERT OR IGNORE INTO sent_products (product_id, product_name, product_link, product_price) VALUES (?, ?, ?, ?)",
            (product_id, product_name, product_link, product_price)
        )
        self.conn.commit()
    
    def get_total_products(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM sent_products")
        return self.cursor.fetchone()[0]
    
    # ========== Keyword Methods (Auto Discovery) ==========
    def add_keyword(self, keyword: str, source: str = "discovery"):
        self.cursor.execute(
            "INSERT OR IGNORE INTO keywords (keyword, source) VALUES (?, ?)",
            (keyword.lower(), source)
        )
        self.conn.commit()
    
    def add_keywords_batch(self, keywords: List[str], source: str = "discovery"):
        for keyword in keywords:
            self.add_keyword(keyword, source)
    
    def get_untapped_keywords(self, limit: int = 30) -> List[str]:
        self.cursor.execute(
            "SELECT keyword FROM keywords WHERE search_count = 0 ORDER BY created_at LIMIT ?",
            (limit,)
        )
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_best_performing_keywords(self, limit: int = 20) -> List[str]:
        self.cursor.execute(
            "SELECT keyword FROM keywords WHERE success_count > 0 ORDER BY success_count DESC LIMIT ?",
            (limit,)
        )
        return [row[0] for row in self.cursor.fetchall()]
    
    def update_keyword_usage(self, keyword: str, success: bool = False):
        if success:
            self.cursor.execute(
                "UPDATE keywords SET search_count = search_count + 1, success_count = success_count + 1, last_used = CURRENT_TIMESTAMP WHERE keyword = ?",
                (keyword.lower(),)
            )
        else:
            self.cursor.execute(
                "UPDATE keywords SET search_count = search_count + 1, last_used = CURRENT_TIMESTAMP WHERE keyword = ?",
                (keyword.lower(),)
            )
        self.conn.commit()
    
    def get_all_active_keywords(self, limit: int = 50) -> List[str]:
        """Get keywords that haven't been used recently"""
        self.cursor.execute(
            "SELECT keyword FROM keywords WHERE last_used IS NULL OR last_used < datetime('now', '-7 days') ORDER BY success_count DESC LIMIT ?",
            (limit,)
        )
        return [row[0] for row in self.cursor.fetchall()]
    
    # ========== User Methods ==========
    def add_user(self, user_id: int, username: str, first_name: str = "", last_name: str = "", referrer_id: int = None):
        self.cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, referrer_id) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, first_name, last_name, referrer_id)
        )
        if referrer_id:
            self.cursor.execute(
                "UPDATE referrals SET total_referrals = total_referrals + 1, earned_credits = earned_credits + 50 WHERE user_id = ?",
                (referrer_id,)
            )
            self.cursor.execute(
                "INSERT OR IGNORE INTO referrals (user_id, total_referrals, earned_credits) VALUES (?, 0, 0)",
                (referrer_id,)
            )
        self.cursor.execute(
            "INSERT OR IGNORE INTO referrals (user_id, total_referrals, earned_credits) VALUES (?, 0, 0)",
            (user_id,)
        )
        self.conn.commit()
    
    def get_user_stats(self, user_id: int) -> tuple:
        self.cursor.execute("SELECT total_referrals, earned_credits FROM referrals WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result if result else (0, 0)
    
    def get_total_users(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM users")
        return self.cursor.fetchone()[0]
    
    def get_total_referrals(self) -> int:
        self.cursor.execute("SELECT COALESCE(SUM(total_referrals), 0) FROM referrals")
        return self.cursor.fetchone()[0]
    
    # ========== Statistics ==========
    def add_statistics(self, cycle: int, products: int, groups: int, messages: int, keywords: int):
        self.cursor.execute(
            "INSERT INTO bot_stats (cycle_number, products_found, groups_found, messages_sent, keywords_used) VALUES (?, ?, ?, ?, ?)",
            (cycle, products, groups, messages, keywords)
        )
        self.conn.commit()
    
    def get_total_messages_sent(self) -> int:
        self.cursor.execute("SELECT COALESCE(SUM(messages_sent), 0) FROM bot_stats")
        return self.cursor.fetchone()[0]
    
    def close(self):
        if self.conn:
            self.conn.close()


# ============================================
# KEYWORD DISCOVERER (Auto Learn)
# ============================================

class KeywordDiscoverer:
    def __init__(self, db: DatabaseManager, logger: 'Logger'):
        self.db = db
        self.logger = logger
        
        # Seed keywords (starting point)
        self.seed_keywords = [
            "shopping", "deals", "offers", "discount", "sale",
            "electronics", "fashion", "mobile", "gadgets", 
            "online shopping", "coupon", "cashback", "free shipping",
            "trending", "bestseller", "new arrivals", "festival sale",
            "diwali offers", "summer sale", "winter collection",
            "affordable", "premium", "budget shopping"
        ]
    
    def get_new_keywords_from_groups(self, group_titles: List[str]) -> List[str]:
        """Extract potential new keywords from group titles"""
        new_keywords = set()
        
        for title in group_titles:
            # Extract words from title
            words = re.findall(r'\b\w+\b', title.lower())
            for word in words:
                if len(word) > 3 and word not in self.seed_keywords:
                    new_keywords.add(word)
            
            # Extract phrases (2-3 words)
            phrases = re.findall(r'\b\w+\s+\w+\b', title.lower())
            for phrase in phrases:
                if len(phrase) > 5:
                    new_keywords.add(phrase)
        
        return list(new_keywords)
    
    def get_new_keywords_from_searches(self, search_results: List[Dict]) -> List[str]:
        """Extract keywords from search results"""
        new_keywords = set()
        
        for result in search_results:
            if 'keyword' in result:
                related_words = result['keyword'].split()
                for word in related_words:
                    if len(word) > 3:
                        new_keywords.add(word)
        
        return list(new_keywords)
    
    def get_smart_suggestions(self) -> List[str]:
        """Generate smart keyword suggestions based on trends"""
        suggestions = [
            # Time-based keywords
            f"{self.get_season()} sale",
            f"{self.get_season()} offers",
            "flash sale",
            "limited period offer",
            "today only",
            "last chance",
            "clearance sale",
            
            # Category-based
            "best prices",
            "lowest price guarantee",
            "price drop",
            "price alert",
            
            # Action-based
            "grab the deal",
            "shop now",
            "limited stock",
            "hurry up"
        ]
        return suggestions
    
    def get_season(self) -> str:
        """Get current season for keyword suggestions"""
        month = datetime.now().month
        if month in [1, 2, 12]:
            return "winter"
        elif month in [3, 4, 5]:
            return "summer"
        elif month in [6, 7, 8, 9]:
            return "monsoon"
        else:
            return "festival"


# ============================================
# LOGGER
# ============================================

class Logger:
    def __init__(self, level: str = "INFO"):
        self.level = level
        self.start_time = datetime.now()
    
    def info(self, msg: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ℹ️ {msg}")
    
    def success(self, msg: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {msg}")
    
    def error(self, msg: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ {msg}")
    
    def warning(self, msg: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ {msg}")
    
    def debug(self, msg: str):
        if self.level == "DEBUG":
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 {msg}")
    
    def banner(self, title: str):
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)
    
    def separator(self):
        print("-"*70)


# ============================================
# PRODUCT FETCHER
# ============================================

class ProductFetcher:
    def __init__(self, db: DatabaseManager, logger: Logger, config: Config):
        self.db = db
        self.logger = logger
        self.config = config
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_from_api(self) -> Optional[List[Dict]]:
        try:
            async with self.session.get(self.config.api_url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    products = []
                    for item in data:
                        products.append({
                            'name': item.get('name', 'Product'),
                            'price': item.get('price', 'Check Website'),
                            'link': item.get('url') or item.get('link', self.config.website),
                        })
                    self.logger.success(f"Fetched {len(products)} products via API")
                    return products
        except Exception as e:
            self.logger.debug(f"API fetch failed: {e}")
        return None
    
    async def fetch_from_html(self) -> Optional[List[Dict]]:
        try:
            async with self.session.get(self.config.products_page, timeout=15) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                products = []
                # Generic product detection
                for element in soup.find_all(['div', 'article', 'li']):
                    if element.get('class') and any('product' in str(c).lower() for c in element.get('class', [])):
                        name_elem = element.find(['h3', 'h4', 'h2'])
                        price_elem = element.find(['span', 'div'], string=re.compile(r'₹|\d+'))
                        link_elem = element.find('a', href=True)
                        
                        if name_elem and link_elem:
                            name = name_elem.text.strip()[:100]
                            price = price_elem.text.strip()[:50] if price_elem else "Check Website"
                            link = link_elem['href']
                            if not link.startswith('http'):
                                link = self.config.website + link
                            
                            products.append({'name': name, 'price': price, 'link': link})
                            
                            if len(products) >= self.config.max_products_per_cycle:
                                break
                        
        except Exception as e:
            self.logger.debug(f"HTML fetch failed: {e}")
        return None
    
    def get_fallback_products(self) -> List[Dict]:
        return [
            {"name": "Wireless Bluetooth Headphones", "price": "₹999", "link": f"{self.config.website}/product/headphones"},
            {"name": "Smart Watch", "price": "₹1999", "link": f"{self.config.website}/product/smartwatch"},
            {"name": "Power Bank 20000mAh", "price": "₹899", "link": f"{self.config.website}/product/powerbank"},
            {"name": "Noise Cancelling Earbuds", "price": "₹1499", "link": f"{self.config.website}/product/earbuds"},
            {"name": "Bluetooth Speaker", "price": "₹1299", "link": f"{self.config.website}/product/speaker"},
            {"name": "Phone Back Cover", "price": "₹199", "link": f"{self.config.website}/product/cover"},
            {"name": "Fast Charging Cable", "price": "₹149", "link": f"{self.config.website}/product/cable"},
            {"name": "Selfie Ring Light", "price": "₹399", "link": f"{self.config.website}/product/ringlight"},
            {"name": "Gaming Mouse", "price": "₹599", "link": f"{self.config.website}/product/mouse"},
            {"name": "Keyboard Combo", "price": "₹899", "link": f"{self.config.website}/product/keyboard"},
        ]
    
    async def get_new_products(self) -> List[Dict]:
        self.logger.info("Fetching products...")
        
        products = await self.fetch_from_api()
        if not products:
            products = await self.fetch_from_html()
        if not products:
            self.logger.warning("Using fallback products")
            products = self.get_fallback_products()
        
        new_products = []
        for product in products:
            if not self.db.is_product_sent(product['link']):
                new_products.append(product)
        
        self.logger.info(f"Found {len(products)} total, {len(new_products)} new")
        return new_products


# ============================================
# SMART GROUP SEARCHER (With Auto Keywords)
# ============================================

class SmartGroupSearcher:
    def __init__(self, client: TelegramClient, db: DatabaseManager, logger: Logger, config: Config):
        self.client = client
        self.db = db
        self.logger = logger
        self.config = config
        self.keyword_discoverer = KeywordDiscoverer(db, logger)
    
    async def search_with_keywords(self, keywords: List[str]) -> List[Dict]:
        """Search groups using multiple keywords"""
        found_groups = []
        
        for keyword in keywords:
            try:
                result = await self.client(functions.contacts.SearchRequest(
                    q=keyword,
                    limit=self.config.max_groups_per_search
                ))
                
                for chat in result.chats:
                    if hasattr(chat, 'username') and chat.username:
                        group_id = f"@{chat.username}"
                        
                        if not self.db.is_group_sent(group_id):
                            found_groups.append({
                                'id': group_id,
                                'name': getattr(chat, 'title', group_id),
                                'members': getattr(chat, 'participants_count', 0),
                                'keyword': keyword
                            })
                            self.db.update_keyword_usage(keyword, True)
                        else:
                            self.db.update_keyword_usage(keyword, False)
                
                await asyncio.sleep(self.config.search_gap_seconds)
                
            except Exception as e:
                self.logger.debug(f"Search error for '{keyword}': {e}")
        
        return found_groups
    
    async def discover_and_search(self) -> Tuple[List[Dict], List[str]]:
        """Discover new keywords and search with them"""
        # Get untapped keywords from database
        untapped = self.db.get_untapped_keywords(25)
        
        # Get best performing keywords
        best = self.db.get_best_performing_keywords(10)
        
        # Get fresh keywords from discovery
        fresh = self.keyword_discoverer.get_smart_suggestions()
        
        # Combine all sources
        all_keywords = list(set(untapped + best + fresh + BASE_SEARCH_QUERIES))[:self.config.max_keywords]
        
        self.logger.info(f"Searching with {len(all_keywords)} keywords")
        
        # Search with all keywords
        groups = await self.search_with_keywords(all_keywords)
        
        return groups, all_keywords
    
    async def extract_keywords_from_groups(self, groups: List[Dict]) -> List[str]:
        """Extract potential new keywords from found groups"""
        group_titles = [g['name'] for g in groups]
        new_keywords = self.keyword_discoverer.get_new_keywords_from_groups(group_titles)
        
        # Add to database
        for kw in new_keywords[:20]:
            self.db.add_keyword(kw, "group_extraction")
        
        return new_keywords


# ============================================
# MESSAGE SENDER
# ============================================

class MessageSender:
    def __init__(self, client: TelegramClient, db: DatabaseManager, logger: Logger, config: Config):
        self.client = client
        self.db = db
        self.logger = logger
        self.config = config
    
    def get_message(self, product: Dict) -> str:
        template = random.choice(MESSAGE_TEMPLATES)
        return template.format(
            product_name=product['name'],
            product_price=product['price'],
            product_link=product['link'],
            app_link=self.config.app_link,
            website=self.config.website,
            seller_link=self.config.seller_link
        )
    
    async def send_to_group(self, group: Dict, message: str) -> bool:
        try:
            await self.client.send_message(group['id'], message)
            self.db.add_sent_group(group['id'], group['name'], group['members'])
            self.logger.success(f"Sent to: {group['name'][:40]}")
            return True
            
        except errors.FloodWaitError as e:
            self.logger.warning(f"Flood wait: {e.seconds}s")
            await asyncio.sleep(e.seconds)
            return False
            
        except errors.ChatWriteForbiddenError:
            self.logger.warning(f"No permission: {group['name'][:40]}")
            return False
            
        except Exception as e:
            self.logger.debug(f"Send failed: {e}")
            return False
    
    async def send_product_to_groups(self, product: Dict, groups: List[Dict]) -> int:
        message = self.get_message(product)
        sent_count = 0
        
        for group in groups:
            if await self.send_to_group(group, message):
                sent_count += 1
            await asyncio.sleep(self.config.message_gap_seconds)
        
        return sent_count


# ============================================
# BOT HANDLERS
# ============================================

class BotHandlers:
    def __init__(self, client: TelegramClient, db: DatabaseManager, logger: Logger, config: Config):
        self.client = client
        self.db = db
        self.logger = logger
        self.config = config
        self._register_handlers()
    
    def _register_handlers(self):
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            await self.handle_start(event)
        
        @self.client.on(events.NewMessage(pattern='/status'))
        async def status_handler(event):
            await self.handle_status(event)
        
        @self.client.on(events.NewMessage(pattern='/stats'))
        async def stats_handler(event):
            await self.handle_stats(event)
        
        @self.client.on(events.NewMessage(pattern='/refer'))
        async def refer_handler(event):
            await self.handle_refer(event)
        
        @self.client.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            await self.handle_help(event)
        
        @self.client.on(events.NewMessage)
        async def auto_reply_handler(event):
            await self.handle_auto_reply(event)
    
    async def handle_start(self, event):
        user_id = event.sender_id
        username = event.sender.username or ""
        first_name = event.sender.first_name or ""
        
        args = event.message.text.split()
        referrer_id = None
        if len(args) > 1 and args[1].isdigit():
            referrer_id = int(args[1])
        
        self.db.add_user(user_id, username, first_name, "", referrer_id)
        
        await event.reply(
            f"🛍️ Welcome to ApyKart, {first_name}! 🛍️\n\n"
            f"India's new shopping destination 🇮🇳\n\n"
            f"✨ What we offer:\n"
            f"• Latest products at best prices\n"
            f"• Free shipping on ₹499+\n"
            f"• COD available\n"
            f"• 7-day easy returns\n\n"
            f"📱 App: {self.config.app_link}\n"
            f"🛒 Shop: {self.config.products_page}\n\n"
            f"🎁 Use Code: WELCOME20 for 20% OFF!\n\n"
            f"💝 Refer and Earn: /refer",
            buttons=[
                [Button.url("🛒 Shop Now", self.config.products_page)],
                [Button.url("📱 Download App", self.config.app_link)],
                [Button.url("📦 Sell on ApyKart", self.config.seller_link)]
            ]
        )
    
    async def handle_status(self, event):
        groups = self.db.get_total_groups()
        products = self.db.get_total_products()
        users = self.db.get_total_users()
        messages = self.db.get_total_messages_sent()
        
        await event.reply(
            f"📊 ApyKart Bot Status 📊\n\n"
            f"🤖 Status: 🟢 ONLINE\n"
            f"📤 Groups targeted: {groups}\n"
            f"📦 Products sent: {products}\n"
            f"👥 Total users: {users}\n"
            f"💬 Total messages: {messages}\n"
            f"🔄 Auto marketing: Active\n"
            f"🔍 Auto keyword discovery: Active\n"
            f"🌐 Website: {self.config.website}\n\n"
            f"⏰ Last update: {datetime.now().strftime('%H:%M:%S')}"
        )
    
    async def handle_stats(self, event):
        groups = self.db.get_total_groups()
        products = self.db.get_total_products()
        users = self.db.get_total_users()
        referrals = self.db.get_total_referrals()
        messages = self.db.get_total_messages_sent()
        
        await event.reply(
            f"📈 Detailed Statistics 📈\n\n"
            f"📊 Marketing:\n"
            f"├─ Groups Messaged: {groups}\n"
            f"├─ Products Sent: {products}\n"
            f"├─ Total Messages: {messages}\n\n"
            f"👥 Users:\n"
            f"├─ Total Users: {users}\n"
            f"├─ Total Referrals: {referrals}\n"
            f"├─ Credits Given: ₹{referrals * 50}\n\n"
            f"🎯 Conversion Rate: {round((referrals/max(users,1))*100, 1)}%\n"
            f"🤖 Bot Uptime: 24x7"
        )
    
    async def handle_refer(self, event):
        user_id = event.sender_id
        bot_username = (await self.client.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        
        total, earned = self.db.get_user_stats(user_id)
        
        await event.reply(
            f"🔗 Your ApyKart Referral Link 🔗\n\n"
            f"{ref_link}\n\n"
            f"📊 Your Stats:\n"
            f"├─ Friends Joined: {total}\n"
            f"├─ Credits Earned: ₹{earned}\n"
            f"└─ Status: Active ✅\n\n"
            f"Share this link with friends!\n"
            f"Each friend gives you ₹50 credit!"
        )
    
    async def handle_help(self, event):
        await event.reply(
            f"📚 ApyKart Bot Commands 📚\n\n"
            f"/start - Welcome & Menu\n"
            f"/status - Bot Status\n"
            f"/stats - Detailed Stats\n"
            f"/refer - Referral Link\n"
            f"/help - This Guide\n\n"
            f"🛍️ Quick Links:\n"
            f"Shop: {self.config.products_page}\n"
            f"App: {self.config.app_link}"
        )
    
    async def handle_auto_reply(self, event):
        if not event.message.text:
            return
        
        text = event.message.text.lower()
        
        if 'apykart' in text:
            await event.reply(f"🛍️ ApyKart 🛍️\n\nShop: {self.config.products_page}\nApp: {self.config.app_link}\n🎁 Code: WELCOME20")
        elif any(word in text for word in ['offer', 'discount', 'coupon', 'deal']):
            await event.reply(f"🎉 Current Offers 🎉\n\n• 20% OFF: WELCOME20\n• Free Shipping on ₹499+\n• COD Available\n\n👉 {self.config.products_page}")
        elif any(word in text for word in ['seller', 'vendor', 'sell']):
            await event.reply(f"📦 Sell on ApyKart 📦\n\nFree Registration\nZero Commission (3 months)\n\n👉 {self.config.seller_link}")
        elif any(word in text for word in ['app', 'download']):
            await event.reply(f"📱 Download App 📱\n\n{self.config.app_link}\n\n✨ App Exclusive Offers")


# ============================================
# AUTO MARKETING ENGINE (Enhanced)
# ============================================

class AutoMarketingEngine:
    def __init__(self, client: TelegramClient, db: DatabaseManager, logger: Logger, config: Config):
        self.client = client
        self.db = db
        self.logger = logger
        self.config = config
        self.product_fetcher = ProductFetcher(db, logger, config)
        self.group_searcher = SmartGroupSearcher(client, db, logger, config)
        self.message_sender = MessageSender(client, db, logger, config)
        self.cycle = 1
        self.is_running = True
    
    async def run_cycle(self) -> Dict:
        cycle_start = datetime.now()
        
        self.logger.separator()
        self.logger.info(f"🚀 STARTING CYCLE #{self.cycle}")
        self.logger.separator()
        
        # Step 1: Fetch products
        self.logger.info("📦 Step 1: Fetching products...")
        products = await self.product_fetcher.get_new_products()
        
        if not products:
            self.logger.warning("No new products found")
            return {'products': 0, 'groups': 0, 'messages': 0, 'keywords': 0}
        
        # Step 2: Discover keywords and search groups
        self.logger.info("🔍 Step 2: Discovering keywords & searching groups...")
        groups, keywords_used = await self.group_searcher.discover_and_search()
        self.logger.success(f"Found {len(groups)} new groups using {len(keywords_used)} keywords")
        
        # Step 3: Extract new keywords from found groups
        if groups:
            new_keywords = await self.group_searcher.extract_keywords_from_groups(groups)
            self.logger.info(f"📝 Extracted {len(new_keywords)} potential new keywords")
        
        if not groups:
            self.logger.warning("No new groups found")
            return {'products': len(products), 'groups': 0, 'messages': 0, 'keywords': len(keywords_used)}
        
        # Step 4: Send messages
        self.logger.info("📤 Step 3: Sending messages...")
        total_messages = 0
        
        for product in products:
            self.logger.info(f"  Sending: {product['name'][:40]}...")
            messages_sent = await self.message_sender.send_product_to_groups(product, groups)
            total_messages += messages_sent
            
            self.db.add_sent_product(product['link'], product['name'], product['price'])
            
            if len(products) > 1:
                await asyncio.sleep(60)
        
        # Save statistics
        self.db.add_statistics(self.cycle, len(products), len(groups), total_messages, len(keywords_used))
        
        cycle_duration = (datetime.now() - cycle_start).seconds
        
        return {
            'products': len(products),
            'groups': len(groups),
            'messages': total_messages,
            'keywords': len(keywords_used),
            'duration': cycle_duration
        }
    
    async def run_forever(self):
        self.logger.banner("🤖 APYKART FULLY AUTOMATED ENGINE v9.0")
        self.logger.info(f"🌐 Website: {self.config.website}")
        self.logger.info(f"🔄 Cycle interval: {self.config.cycle_hours} hours")
        self.logger.info(f"🔍 Auto keyword discovery: ACTIVE")
        self.logger.info(f"📦 Max products per cycle: {self.config.max_products_per_cycle}")
        self.logger.separator()
        
        while self.is_running:
            try:
                results = await self.run_cycle()
                
                self.logger.separator()
                self.logger.banner(f"📊 CYCLE #{self.cycle} SUMMARY")
                self.logger.info(f"  ├─ Products found: {results['products']}")
                self.logger.info(f"  ├─ Groups found: {results['groups']}")
                self.logger.info(f"  ├─ Messages sent: {results['messages']}")
                self.logger.info(f"  ├─ Keywords used: {results['keywords']}")
                self.logger.info(f"  ├─ Duration: {results['duration']}s")
                self.logger.info(f"  └─ Total groups to date: {self.db.get_total_groups()}")
                self.logger.separator()
                
                self.cycle += 1
                
                if self.is_running:
                    self.logger.info(f"⏰ Next cycle in {self.config.cycle_hours} hours...")
                    await asyncio.sleep(self.config.cycle_hours * 3600)
                    
            except Exception as e:
                self.logger.error(f"Cycle failed: {e}")
                self.logger.debug(traceback.format_exc())
                await asyncio.sleep(300)
    
    def stop(self):
        self.is_running = False


# ============================================
# AUTO RESTART MANAGER
# ============================================

class AutoRestartManager:
    def __init__(self, logger: Logger, config: Config):
        self.logger = logger
        self.config = config
        self.is_running = True
        self.last_restart = datetime.now()
    
    async def restart_bot(self):
        self.logger.info("🔄 Auto-restarting bot...")
        self.last_restart = datetime.now()
        python = sys.executable
        script = os.path.abspath(__file__)
        os.execv(python, [python, script])
    
    async def monitor_and_restart(self):
        self.logger.info("🔄 Auto-Restart Manager Started!")
        self.logger.info(f"⏰ Restart every {self.config.auto_restart_hours} hours")
        
        while self.is_running:
            try:
                hours_since = (datetime.now() - self.last_restart).total_seconds() / 3600
                if hours_since >= self.config.auto_restart_hours:
                    await self.restart_bot()
                    break
                await asyncio.sleep(3600)
            except Exception as e:
                self.logger.error(f"Restart monitor error: {e}")
                await asyncio.sleep(300)
    
    def stop(self):
        self.is_running = False


# ============================================
# BACKGROUND SERVICE SETUP
# ============================================

def setup_background_service():
    try:
        termux_path = "/data/data/com.termux/files/usr/bin"
        if os.path.exists(termux_path):
            boot_dir = os.path.expanduser("~/.termux/boot")
            os.makedirs(boot_dir, exist_ok=True)
            
            boot_script = f"""#!/data/data/com.termux/files/usr/bin/bash
sleep 10
cd ~
nohup python3 apykart_ultimate_v9.py > bot.log 2>&1 &
"""
            boot_file = os.path.join(boot_dir, "start_apykart_bot")
            with open(boot_file, "w") as f:
                f.write(boot_script)
            os.chmod(boot_file, 0o755)
            print("✅ Background service configured")
            return True
    except Exception as e:
        print(f"⚠️ Background service failed: {e}")
        return False


# ============================================
# MAIN BOT CLASS
# ============================================

class ApyKartUltimateBot:
    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger(config.log_level)
        self.db = DatabaseManager(config.db_path)
        self.client = None
        self.marketing_engine = None
        self.restart_manager = None
        self.handlers = None
    
    async def start(self):
        self.logger.banner("🛍️ APYKART FULLY AUTOMATED BOT v9.0")
        self.logger.info("Auto Discovery | Auto Search | Auto Send | Auto Everything")
        
        try:
            self.client = await TelegramClient(
                'apykart_v9',
                self.config.api_id,
                self.config.api_hash
            ).start(bot_token=self.config.bot_token)
            self.logger.success(f"Bot Connected: @{(await self.client.get_me()).username}")
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return
        
        # Initialize components
        self.marketing_engine = AutoMarketingEngine(self.client, self.db, self.logger, self.config)
        self.restart_manager = AutoRestartManager(self.logger, self.config)
        self.handlers = BotHandlers(self.client, self.db, self.logger, self.config)
        
        # Start services
        asyncio.create_task(self.marketing_engine.run_forever())
        asyncio.create_task(self.restart_manager.monitor_and_restart())
        
        if self.config.enable_background_service:
            setup_background_service()
            self.logger.info("📌 Background Service: CONFIGURED")
        
        self.logger.separator()
        self.logger.success("🤖 BOT IS FULLY OPERATIONAL!")
        self.logger.info("📌 Features Active:")
        self.logger.info("   ✅ Auto Keyword Discovery")
        self.logger.info("   ✅ Smart Group Search")
        self.logger.info("   ✅ Auto Product Fetch")
        self.logger.info("   ✅ Auto Message Send")
        self.logger.info("   ✅ Auto Restart (24h)")
        self.logger.info("   ✅ Background Service")
        self.logger.separator()
        
        # Show current stats
        stats = f"""
📊 Current Statistics:
├─ Groups Targeted: {self.db.get_total_groups()}
├─ Products Sent: {self.db.get_total_products()}
├─ Total Users: {self.db.get_total_users()}
├─ Total Referrals: {self.db.get_total_referrals()}
└─ Total Messages: {self.db.get_total_messages_sent()}
"""
        self.logger.info(stats)
        
        await self.client.run_until_disconnected()
    
    async def stop(self):
        if self.marketing_engine:
            self.marketing_engine.stop()
        if self.restart_manager:
            self.restart_manager.stop()
        if self.client:
            await self.client.disconnect()
        self.db.close()
        self.logger.success("Bot stopped")


# ============================================
# MAIN ENTRY POINT
# ============================================

async def main():
    config = Config()
    bot = ApyKartUltimateBot(config)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        await bot.stop()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
