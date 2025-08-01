#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Offline-läge för valutakurser
Lokal caching och fallback-kurser
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import requests
import time

class OfflineCurrencyConverter:
    """Förbättrad valutakonverterare med offline-stöd"""
    
    def __init__(self, cache_file: str = "currency_cache.json", db_file: str = "currency_rates.db"):
        self.cache_file = cache_file
        self.db_file = db_file
        self.api_url = "https://api.exchangerate-api.com/v4/latest/"
        self.fallback_rates = self.get_fallback_rates()
        self.setup_database()
        self.load_cache()
    
    def setup_database(self):
        """Sätter upp databas för valutakurser"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Skapa tabell för valutakurser
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS currency_rates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        from_currency TEXT NOT NULL,
                        to_currency TEXT NOT NULL,
                        rate REAL NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        source TEXT DEFAULT 'api'
                    )
                ''')
                
                # Skapa index för snabbare sökningar
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_currency_pair 
                    ON currency_rates(from_currency, to_currency)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON currency_rates(timestamp)
                ''')
                
                conn.commit()
            
        except Exception as e:
            print(f"Fel vid uppsättning av valutadatabas: {e}")
    
    def get_fallback_rates(self) -> Dict:
        """Returnerar fallback-kurser för offline-läge"""
        return {
            'SEK': {
                'USD': 0.11,
                'EUR': 0.10,
                'GBP': 0.085,
                'NOK': 1.05,
                'DKK': 0.75
            },
            'USD': {
                'SEK': 9.0,
                'EUR': 0.92,
                'GBP': 0.78,
                'NOK': 9.5,
                'DKK': 6.8
            },
            'EUR': {
                'SEK': 9.8,
                'USD': 1.09,
                'GBP': 0.85,
                'NOK': 10.3,
                'DKK': 7.4
            },
            'GBP': {
                'SEK': 11.5,
                'USD': 1.28,
                'EUR': 1.18,
                'NOK': 12.1,
                'DKK': 8.7
            },
            'NOK': {
                'SEK': 0.95,
                'USD': 0.105,
                'EUR': 0.097,
                'GBP': 0.083,
                'DKK': 0.72
            },
            'DKK': {
                'SEK': 1.33,
                'USD': 0.147,
                'EUR': 0.135,
                'GBP': 0.115,
                'NOK': 1.39
            }
        }
    
    def load_cache(self):
        """Laddar cachade valutakurser"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
            else:
                self.cache = {}
        except Exception as e:
            print(f"Fel vid laddning av valutacache: {e}")
            self.cache = {}
    
    def save_cache(self):
        """Sparar cachade valutakurser"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Fel vid sparande av valutacache: {e}")
    
    def is_cache_valid(self, from_currency: str, to_currency: str, max_age_hours: int = 24) -> bool:
        """Kontrollerar om cachad kurs är giltig"""
        cache_key = f"{from_currency}_{to_currency}"
        
        if cache_key not in self.cache:
            return False
        
        cached_data = self.cache[cache_key]
        if 'timestamp' not in cached_data:
            return False
        
        try:
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            age = datetime.now() - cached_time
            return age.total_seconds() < (max_age_hours * 3600)
        except:
            return False
    
    def get_cached_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Hämtar cachad valutakurs"""
        cache_key = f"{from_currency}_{to_currency}"
        
        if cache_key in self.cache and self.is_cache_valid(from_currency, to_currency):
            return self.cache[cache_key]['rate']
        
        return None
    
    def save_rate_to_cache(self, from_currency: str, to_currency: str, rate: float):
        """Sparar valutakurs till cache"""
        cache_key = f"{from_currency}_{to_currency}"
        
        self.cache[cache_key] = {
            'rate': rate,
            'timestamp': datetime.now().isoformat(),
            'source': 'api'
        }
        
        self.save_cache()
    
    def save_rate_to_database(self, from_currency: str, to_currency: str, rate: float, source: str = 'api'):
        """Sparar valutakurs till databas"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO currency_rates (from_currency, to_currency, rate, source)
                    VALUES (?, ?, ?, ?)
                ''', (from_currency, to_currency, rate, source))
                
                conn.commit()
            
        except Exception as e:
            print(f"Fel vid sparande av valutakurs till databas: {e}")
    
    def get_rate_from_database(self, from_currency: str, to_currency: str, max_age_hours: int = 168) -> Optional[float]:
        """Hämtar valutakurs från databas"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Hämta senaste kursen inom max_age_hours
                cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
                
                cursor.execute('''
                    SELECT rate, timestamp FROM currency_rates 
                    WHERE from_currency = ? AND to_currency = ? AND timestamp > ?
                    ORDER BY timestamp DESC LIMIT 1
                ''', (from_currency, to_currency, cutoff_time.isoformat()))
                
                result = cursor.fetchone()
                
                if result:
                    return result[0]
            
        except Exception as e:
            print(f"Fel vid hämtning av valutakurs från databas: {e}")
        
        return None
    
    def fetch_rate_from_api(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Hämtar valutakurs från API"""
        try:
            url = f"{self.api_url}{from_currency}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})
                
                if to_currency in rates:
                    rate = rates[to_currency]
                    
                    # Spara till cache och databas
                    self.save_rate_to_cache(from_currency, to_currency, rate)
                    self.save_rate_to_database(from_currency, to_currency, rate)
                    
                    return rate
            
        except Exception as e:
            print(f"Fel vid hämtning från API: {e}")
        
        return None
    
    def get_fallback_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Hämtar fallback-kurs"""
        if from_currency in self.fallback_rates:
            if to_currency in self.fallback_rates[from_currency]:
                return self.fallback_rates[from_currency][to_currency]
        
        # Omvänd kurs
        if to_currency in self.fallback_rates:
            if from_currency in self.fallback_rates[to_currency]:
                return 1 / self.fallback_rates[to_currency][from_currency]
        
        return None
    
    def get_exchange_rate(self, from_currency: str, to_currency: str, force_online: bool = False) -> float:
        """Hämtar valutakurs med offline-stöd"""
        # Normalisera valutakoder
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Samma valuta
        if from_currency == to_currency:
            return 1.0
        
        # 1. Försök hämta från cache
        cached_rate = self.get_cached_rate(from_currency, to_currency)
        if cached_rate and not force_online:
            return cached_rate
        
        # 2. Försök hämta från databas
        db_rate = self.get_rate_from_database(from_currency, to_currency)
        if db_rate and not force_online:
            # Uppdatera cache med databasvärde
            self.save_rate_to_cache(from_currency, to_currency, db_rate)
            return db_rate
        
        # 3. Försök hämta från API (om online)
        if not force_online:
            api_rate = self.fetch_rate_from_api(from_currency, to_currency)
            if api_rate:
                return api_rate
        
        # 4. Använd fallback-kurs
        fallback_rate = self.get_fallback_rate(from_currency, to_currency)
        if fallback_rate:
            # Spara fallback-kurs som "offline"
            self.save_rate_to_cache(from_currency, to_currency, fallback_rate)
            self.save_rate_to_database(from_currency, to_currency, fallback_rate, 'offline')
            return fallback_rate
        
        # 5. Sista utväg - returnera 1.0
        print(f"Varning: Kunde inte hitta kurs för {from_currency} -> {to_currency}")
        return 1.0
    
    def convert_amount(self, amount: float, from_currency: str, to_currency: str, force_online: bool = False) -> float:
        """Konverterar belopp mellan valutor"""
        rate = self.get_exchange_rate(from_currency, to_currency, force_online)
        return amount * rate
    
    def get_available_currencies(self) -> List[str]:
        """Returnerar lista över tillgängliga valutor"""
        currencies = set()
        
        # Lägg till alla valutor från fallback-rates
        for from_curr in self.fallback_rates:
            currencies.add(from_curr)
            currencies.update(self.fallback_rates[from_curr].keys())
        
        # Lägg till valutor från databas
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT DISTINCT from_currency FROM currency_rates')
                for row in cursor.fetchall():
                    currencies.add(row[0])
                
                cursor.execute('SELECT DISTINCT to_currency FROM currency_rates')
                for row in cursor.fetchall():
                    currencies.add(row[0])
            
        except Exception as e:
            print(f"Fel vid hämtning av valutor från databas: {e}")
        
        return sorted(list(currencies))
    
    def update_all_rates(self) -> Dict:
        """Uppdaterar alla valutakurser från API"""
        results = {
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        base_currencies = ['SEK', 'USD', 'EUR', 'GBP']
        target_currencies = ['SEK', 'USD', 'EUR', 'GBP', 'NOK', 'DKK']
        
        for base in base_currencies:
            for target in target_currencies:
                if base != target:
                    try:
                        rate = self.fetch_rate_from_api(base, target)
                        if rate:
                            results['successful'] += 1
                        else:
                            results['failed'] += 1
                            results['errors'].append(f"Kunde inte hämta {base}->{target}")
                    except Exception as e:
                        results['failed'] += 1
                        results['errors'].append(f"Fel för {base}->{target}: {e}")
        
        return results
    
    def get_rate_history(self, from_currency: str, to_currency: str, days: int = 30) -> List[Dict]:
        """Hämtar historik för valutakurs"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                cursor.execute('''
                    SELECT rate, timestamp, source FROM currency_rates 
                    WHERE from_currency = ? AND to_currency = ? AND timestamp > ?
                    ORDER BY timestamp ASC
                ''', (from_currency, to_currency, cutoff_date.isoformat()))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'rate': row[0],
                        'timestamp': row[1],
                        'source': row[2]
                    })
                
                return history
            
        except Exception as e:
            print(f"Fel vid hämtning av kurshistorik: {e}")
            return []
    
    def cleanup_old_rates(self, days: int = 90):
        """Rensar gamla valutakurser från databas"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                
                cursor.execute('''
                    DELETE FROM currency_rates 
                    WHERE timestamp < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                print(f"Tog bort {deleted_count} gamla valutakurser")
            
        except Exception as e:
            print(f"Fel vid rensning av gamla kurser: {e}")
    
    def get_offline_status(self) -> Dict:
        """Returnerar status för offline-läge"""
        try:
            # Testa internetanslutning
            response = requests.get("https://httpbin.org/get", timeout=5)
            online = response.status_code == 200
        except:
            online = False
        
        # Kontrollera cache-status
        cache_stats = {
            'total_cached_pairs': len(self.cache),
            'valid_cached_pairs': sum(1 for key in self.cache if self.is_cache_valid(*key.split('_')))
        }
        
        # Kontrollera databas-status
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM currency_rates')
            db_count = cursor.fetchone()[0]
            conn.close()
        except:
            db_count = 0
        
        return {
            'online': online,
            'cache_stats': cache_stats,
            'database_entries': db_count,
            'fallback_available': len(self.fallback_rates) > 0
        }

# Hjälpfunktioner för GUI-integration
def create_currency_widget(parent, converter: OfflineCurrencyConverter):
    """Skapar en widget för valutakonvertering"""
    frame = ttk.LabelFrame(parent, text="Valutakonvertering", padding=10)
    
    # Input-fält
    input_frame = ttk.Frame(frame)
    input_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Label(input_frame, text="Belopp:").pack(side=tk.LEFT)
    amount_var = tk.StringVar()
    amount_entry = ttk.Entry(input_frame, textvariable=amount_var, width=15)
    amount_entry.pack(side=tk.LEFT, padx=(5, 10))
    
    ttk.Label(input_frame, text="Från:").pack(side=tk.LEFT)
    from_currency_var = tk.StringVar(value="SEK")
    from_combo = ttk.Combobox(input_frame, textvariable=from_currency_var, 
                              values=converter.get_available_currencies(), width=8)
    from_combo.pack(side=tk.LEFT, padx=(5, 10))
    
    ttk.Label(input_frame, text="Till:").pack(side=tk.LEFT)
    to_currency_var = tk.StringVar(value="USD")
    to_combo = ttk.Combobox(input_frame, textvariable=to_currency_var, 
                            values=converter.get_available_currencies(), width=8)
    to_combo.pack(side=tk.LEFT, padx=(5, 10))
    
    # Resultat
    result_frame = ttk.Frame(frame)
    result_frame.pack(fill=tk.X)
    
    result_var = tk.StringVar()
    result_label = ttk.Label(result_frame, textvariable=result_var, font=("Arial", 12, "bold"))
    result_label.pack(side=tk.LEFT)
    
    # Konvertera-knapp
    def convert():
        try:
            amount = float(amount_var.get())
            from_curr = from_currency_var.get()
            to_curr = to_currency_var.get()
            
            converted = converter.convert_amount(amount, from_curr, to_curr)
            result_var.set(f"{amount:.2f} {from_curr} = {converted:.2f} {to_curr}")
        except ValueError:
            result_var.set("Ogiltigt belopp")
        except Exception as e:
            result_var.set(f"Fel: {e}")
    
    ttk.Button(frame, text="Konvertera", command=convert).pack(pady=10)
    
    return frame

def check_offline_availability() -> bool:
    """Kontrollerar om offline-funktioner är tillgängliga"""
    try:
        import requests
        return True
    except ImportError:
        return False