#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud-synkronisering för utgiftshanteraren
REST API för synkronisering mellan enheter
"""

import requests
import json
import hashlib
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3
import os
from dataclasses import dataclass, asdict
from enum import Enum

class SyncStatus(Enum):
    PENDING = "pending"
    SYNCED = "synced"
    CONFLICT = "conflict"
    ERROR = "error"

@dataclass
class SyncItem:
    """Representerar ett synkroniseringsobjekt"""
    id: str
    table_name: str
    record_id: int
    data: Dict
    timestamp: datetime
    device_id: str
    status: SyncStatus
    hash: str = ""

class CloudSyncManager:
    """Hanterar cloud-synkronisering"""
    
    def __init__(self, api_url: str = "https://api.expense-manager.com", 
                 device_id: str = None, api_key: str = None):
        self.api_url = api_url
        self.device_id = device_id or self.generate_device_id()
        self.api_key = api_key
        self.sync_interval = 300  # 5 minuter
        self.last_sync = None
        self.sync_thread = None
        self.is_syncing = False
        self.setup_local_sync_db()
    
    def generate_device_id(self) -> str:
        """Genererar unikt enhets-ID"""
        import uuid
        return str(uuid.uuid4())
    
    def setup_local_sync_db(self):
        """Sätter upp lokal synkroniseringsdatabas"""
        try:
            with sqlite3.connect("sync.db") as conn:
                cursor = conn.cursor()
                
                # Skapa synkroniseringslogg
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sync_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sync_id TEXT UNIQUE,
                        table_name TEXT NOT NULL,
                        record_id INTEGER NOT NULL,
                        data TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        device_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        hash TEXT NOT NULL,
                        server_timestamp DATETIME,
                        conflict_resolved BOOLEAN DEFAULT FALSE
                    )
                ''')
                
                # Skapa index för snabbare sökningar
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_sync_status 
                    ON sync_log(status)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_sync_table_record 
                    ON sync_log(table_name, record_id)
                ''')
                
                conn.commit()
            
        except Exception as e:
            print(f"Fel vid uppsättning av synkroniseringsdatabas: {e}")
    
    def start_auto_sync(self):
        """Startar automatisk synkronisering"""
        if self.sync_thread and self.sync_thread.is_alive():
            return
        
        self.sync_thread = threading.Thread(target=self.auto_sync_loop, daemon=True)
        self.sync_thread.start()
        print("Automatisk synkronisering startad")
    
    def stop_auto_sync(self):
        """Stoppar automatisk synkronisering"""
        self.is_syncing = False
        print("Automatisk synkronisering stoppad")
    
    def auto_sync_loop(self):
        """Huvudloop för automatisk synkronisering"""
        while self.is_syncing:
            try:
                self.sync_all()
                time.sleep(self.sync_interval)
            except Exception as e:
                print(f"Fel vid automatisk synkronisering: {e}")
                time.sleep(60)  # Vänta 1 minut vid fel
    
    def sync_all(self) -> Dict:
        """Synkroniserar all data"""
        if not self.api_key:
            return {"success": False, "error": "Ingen API-nyckel konfigurerad"}
        
        try:
            # Hämta lokala ändringar
            local_changes = self.get_local_changes()
            
            # Hämta serverändringar
            server_changes = self.get_server_changes()
            
            # Lös konflikter
            conflicts = self.resolve_conflicts(local_changes, server_changes)
            
            # Skicka lokala ändringar till server
            upload_result = self.upload_changes(local_changes)
            
            # Ladda ner serverändringar
            download_result = self.download_changes(server_changes)
            
            # Uppdatera synkroniseringsstatus
            self.update_sync_status()
            
            return {
                "success": True,
                "uploaded": len(local_changes),
                "downloaded": len(server_changes),
                "conflicts": len(conflicts),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_local_changes(self) -> List[SyncItem]:
        """Hämtar lokala ändringar som behöver synkas"""
        try:
            with sqlite3.connect("sync.db") as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT sync_id, table_name, record_id, data, timestamp, 
                           device_id, status, hash
                    FROM sync_log 
                    WHERE status IN (?, ?)
                    ORDER BY timestamp ASC
                ''', (SyncStatus.PENDING.value, SyncStatus.ERROR.value))
                
                changes = []
                for row in cursor.fetchall():
                    sync_item = SyncItem(
                        id=row[0],
                        table_name=row[1],
                        record_id=row[2],
                        data=json.loads(row[3]),
                        timestamp=datetime.fromisoformat(row[4]),
                        device_id=row[5],
                        status=SyncStatus(row[6]),
                        hash=row[7]
                    )
                    changes.append(sync_item)
                
                return changes
            
        except Exception as e:
            print(f"Fel vid hämtning av lokala ändringar: {e}")
            return []
    
    def get_server_changes(self) -> List[SyncItem]:
        """Hämtar ändringar från servern"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "device_id": self.device_id,
                "last_sync": self.last_sync.isoformat() if self.last_sync else None
            }
            
            response = requests.get(
                f"{self.api_url}/api/v1/sync/changes",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                changes = []
                
                for item_data in data.get("changes", []):
                    sync_item = SyncItem(
                        id=item_data["id"],
                        table_name=item_data["table_name"],
                        record_id=item_data["record_id"],
                        data=item_data["data"],
                        timestamp=datetime.fromisoformat(item_data["timestamp"]),
                        device_id=item_data["device_id"],
                        status=SyncStatus(item_data["status"]),
                        hash=item_data["hash"]
                    )
                    changes.append(sync_item)
                
                return changes
            else:
                print(f"Fel vid hämtning av serverändringar: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Fel vid hämtning av serverändringar: {e}")
            return []
    
    def resolve_conflicts(self, local_changes: List[SyncItem], 
                         server_changes: List[SyncItem]) -> List[Dict]:
        """Löser konflikter mellan lokala och serverändringar"""
        conflicts = []
        
        # Skapa mappning av ändringar per tabell och record
        local_map = {}
        for change in local_changes:
            key = (change.table_name, change.record_id)
            local_map[key] = change
        
        server_map = {}
        for change in server_changes:
            key = (change.table_name, change.record_id)
            server_map[key] = change
        
        # Hitta konflikter
        for key in set(local_map.keys()) & set(server_map.keys()):
            local_change = local_map[key]
            server_change = server_map[key]
            
            if local_change.hash != server_change.hash:
                conflict = {
                    "table_name": key[0],
                    "record_id": key[1],
                    "local": local_change,
                    "server": server_change,
                    "resolution": "manual"  # Kräver manuell lösning
                }
                conflicts.append(conflict)
        
        return conflicts
    
    def upload_changes(self, changes: List[SyncItem]) -> Dict:
        """Skickar lokala ändringar till servern"""
        if not changes:
            return {"success": True, "uploaded": 0}
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "device_id": self.device_id,
                "changes": [asdict(change) for change in changes]
            }
            
            response = requests.post(
                f"{self.api_url}/api/v1/sync/upload",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Uppdatera lokal synkroniseringsstatus
                self.mark_changes_synced([change.id for change in changes])
                
                return {
                    "success": True,
                    "uploaded": len(changes),
                    "server_timestamp": result.get("timestamp")
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "uploaded": 0
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "uploaded": 0
            }
    
    def download_changes(self, changes: List[SyncItem]) -> Dict:
        """Laddar ner serverändringar till lokal databas"""
        if not changes:
            return {"success": True, "downloaded": 0}
        
        try:
            # Här skulle vi normalt uppdatera den lokala databasen
            # För nu simulerar vi bara nedladdningen
            
            downloaded_count = 0
            for change in changes:
                if self.apply_server_change(change):
                    downloaded_count += 1
            
            return {
                "success": True,
                "downloaded": downloaded_count
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "downloaded": 0
            }
    
    def apply_server_change(self, change: SyncItem) -> bool:
        """Applicerar en serverändring till lokal databas"""
        try:
            # Här skulle vi normalt uppdatera den lokala databasen
            # För nu loggar vi bara ändringen
            
            with sqlite3.connect("sync.db") as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO sync_log 
                    (sync_id, table_name, record_id, data, timestamp, 
                     device_id, status, hash, server_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    change.id,
                    change.table_name,
                    change.record_id,
                    json.dumps(change.data),
                    change.timestamp.isoformat(),
                    change.device_id,
                    SyncStatus.SYNCED.value,
                    change.hash,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
            
            return True
            
        except Exception as e:
            print(f"Fel vid applicering av serverändring: {e}")
            return False
    
    def mark_changes_synced(self, sync_ids: List[str]):
        """Markerar ändringar som synkroniserade"""
        try:
            with sqlite3.connect("sync.db") as conn:
                cursor = conn.cursor()
                
                for sync_id in sync_ids:
                    cursor.execute('''
                        UPDATE sync_log 
                        SET status = ?, server_timestamp = ?
                        WHERE sync_id = ?
                    ''', (SyncStatus.SYNCED.value, datetime.now().isoformat(), sync_id))
                
                conn.commit()
            
        except Exception as e:
            print(f"Fel vid markering av synkroniserade ändringar: {e}")
    
    def update_sync_status(self):
        """Uppdaterar synkroniseringsstatus"""
        self.last_sync = datetime.now()
    
    def add_sync_item(self, table_name: str, record_id: int, data: Dict) -> str:
        """Lägger till ett synkroniseringsobjekt"""
        try:
            sync_id = f"{self.device_id}_{int(time.time() * 1000)}"
            data_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
            
            with sqlite3.connect("sync.db") as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO sync_log 
                    (sync_id, table_name, record_id, data, timestamp, 
                     device_id, status, hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    sync_id,
                    table_name,
                    record_id,
                    json.dumps(data),
                    datetime.now().isoformat(),
                    self.device_id,
                    SyncStatus.PENDING.value,
                    data_hash
                ))
                
                conn.commit()
            
            return sync_id
            
        except Exception as e:
            print(f"Fel vid tillägg av synkroniseringsobjekt: {e}")
            return ""
    
    def get_sync_status(self) -> Dict:
        """Returnerar synkroniseringsstatus"""
        try:
            with sqlite3.connect("sync.db") as conn:
                cursor = conn.cursor()
                
                # Räkna olika status
                cursor.execute('''
                    SELECT status, COUNT(*) FROM sync_log 
                    GROUP BY status
                ''')
            
            status_counts = dict(cursor.fetchall())
            
            # Hämta senaste synkronisering
            cursor.execute('''
                SELECT MAX(timestamp) FROM sync_log 
                WHERE status = ?
            ''', (SyncStatus.SYNCED.value,))
            
            last_sync_result = cursor.fetchone()
            last_sync = last_sync_result[0] if last_sync_result[0] else None
            
            conn.close()
            
            return {
                "device_id": self.device_id,
                "auto_sync_enabled": self.is_syncing,
                "last_sync": last_sync,
                "pending_changes": status_counts.get(SyncStatus.PENDING.value, 0),
                "synced_changes": status_counts.get(SyncStatus.SYNCED.value, 0),
                "conflict_changes": status_counts.get(SyncStatus.CONFLICT.value, 0),
                "error_changes": status_counts.get(SyncStatus.ERROR.value, 0),
                "total_changes": sum(status_counts.values())
            }
            
        except Exception as e:
            print(f"Fel vid hämtning av synkroniseringsstatus: {e}")
            return {}

class CloudAPI:
    """Simulerad cloud API för testning"""
    
    def __init__(self):
        self.data = {}
        self.changes = []
    
    def upload_changes(self, device_id: str, changes: List[Dict]) -> Dict:
        """Simulerar uppladdning av ändringar"""
        uploaded_count = 0
        
        for change in changes:
            change_id = f"{device_id}_{int(time.time() * 1000)}"
            change["id"] = change_id
            change["server_timestamp"] = datetime.now().isoformat()
            
            self.changes.append(change)
            uploaded_count += 1
        
        return {
            "success": True,
            "uploaded": uploaded_count,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_changes(self, device_id: str, last_sync: str = None) -> Dict:
        """Simulerar hämtning av ändringar"""
        # Filtrera ändringar från andra enheter
        other_changes = [
            change for change in self.changes
            if change["device_id"] != device_id
        ]
        
        return {
            "success": True,
            "changes": other_changes,
            "timestamp": datetime.now().isoformat()
        }

# Hjälpfunktioner för GUI-integration
def create_sync_widget(parent):
    """Skapar en widget för synkroniseringshantering"""
    frame = ttk.LabelFrame(parent, text="Cloud-synkronisering", padding=10)
    
    # Status
    status_frame = ttk.Frame(frame)
    status_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
    status_var = tk.StringVar(value="Ej konfigurerad")
    status_label = ttk.Label(status_frame, textvariable=status_var, font=("Arial", 10, "bold"))
    status_label.pack(side=tk.LEFT, padx=(5, 0))
    
    # Knappar
    button_frame = ttk.Frame(frame)
    button_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Button(button_frame, text="Synka nu", 
               command=lambda: sync_now(status_var)).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(button_frame, text="Aktivera auto-sync", 
               command=lambda: toggle_auto_sync(status_var)).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="Visa status", 
               command=lambda: show_sync_status()).pack(side=tk.LEFT, padx=5)
    
    # Statistik
    stats_frame = ttk.LabelFrame(frame, text="Synkroniseringsstatistik", padding=5)
    stats_frame.pack(fill=tk.X)
    
    stats_text = tk.Text(stats_frame, height=6, wrap=tk.WORD)
    stats_scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=stats_text.yview)
    stats_text.configure(yscrollcommand=stats_scrollbar.set)
    
    stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    return frame

def sync_now(status_var):
    """Utför manuell synkronisering"""
    status_var.set("Synkar...")
    # Här skulle vi normalt anropa sync_all()
    # För nu simulerar vi bara
    import threading
    
    def sync_task():
        time.sleep(2)  # Simulera synkronisering
        status_var.set("Synkroniserad")
    
    threading.Thread(target=sync_task, daemon=True).start()

def toggle_auto_sync(status_var):
    """Växlar automatisk synkronisering"""
    current_status = status_var.get()
    if "Aktiverad" in current_status:
        status_var.set("Auto-sync inaktiverad")
    else:
        status_var.set("Auto-sync aktiverad")

def show_sync_status():
    """Visar synkroniseringsstatus"""
    # Här skulle vi normalt visa detaljerad status
    print("Synkroniseringsstatus: Ej implementerad i denna version")