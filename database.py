#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Databasmodul för utgiftshanteraren
Använder SQLite för persistent lagring
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os

class DatabaseManager:
    """Hanterar databasoperationer för utgiftshanteraren"""
    
    def __init__(self, db_path: str = "expense_manager.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initierar databasen med nödvändiga tabeller"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Skapa tabeller
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE,
                    UNIQUE(group_id, name)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    paid_by TEXT NOT NULL,
                    category TEXT,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expense_splits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_id INTEGER NOT NULL,
                    participant_name TEXT NOT NULL,
                    share REAL NOT NULL,
                    FOREIGN KEY (expense_id) REFERENCES expenses (id) ON DELETE CASCADE
                )
            ''')
            
            # Skapa index för bättre prestanda
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_expenses_group_id ON expenses (group_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_participants_group_id ON participants (group_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_splits_expense_id ON expense_splits (expense_id)')
            
            conn.commit()
    
    def create_group(self, name: str) -> int:
        """Skapar en ny grupp och returnerar grupp-ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO groups (name) VALUES (?)', (name,))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_groups(self) -> List[Dict]:
        """Hämtar alla grupper"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT g.id, g.name, g.created_at,
                       COUNT(DISTINCT p.id) as participant_count,
                       COUNT(DISTINCT e.id) as expense_count
                FROM groups g
                LEFT JOIN participants p ON g.id = p.group_id
                LEFT JOIN expenses e ON g.id = e.group_id
                GROUP BY g.id
                ORDER BY g.name
            ''')
            
            groups = []
            for row in cursor.fetchall():
                groups.append({
                    'id': row[0],
                    'name': row[1],
                    'created_at': row[2],
                    'participant_count': row[3],
                    'expense_count': row[4]
                })
            return groups
    
    def get_group_by_id(self, group_id: int) -> Optional[Dict]:
        """Hämtar en grupp med ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, created_at FROM groups WHERE id = ?', (group_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'created_at': row[2]
                }
            return None
    
    def update_group(self, group_id: int, name: str) -> bool:
        """Uppdaterar en grupp"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE groups SET name = ? WHERE id = ?', (name, group_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_group(self, group_id: int) -> bool:
        """Tar bort en grupp och alla relaterade data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM groups WHERE id = ?', (group_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def add_participant(self, group_id: int, name: str, email: str = "") -> int:
        """Lägger till en deltagare i en grupp"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO participants (group_id, name, email) VALUES (?, ?, ?)',
                (group_id, name, email)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_participants(self, group_id: int) -> List[Dict]:
        """Hämtar alla deltagare i en grupp"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, name, email, created_at FROM participants WHERE group_id = ? ORDER BY name',
                (group_id,)
            )
            
            participants = []
            for row in cursor.fetchall():
                participants.append({
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'created_at': row[3]
                })
            return participants
    
    def update_participant(self, participant_id: int, name: str, email: str = "") -> bool:
        """Uppdaterar en deltagare"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE participants SET name = ?, email = ? WHERE id = ?',
                (name, email, participant_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_participant(self, participant_id: int) -> bool:
        """Tar bort en deltagare"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM participants WHERE id = ?', (participant_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def add_expense(self, group_id: int, description: str, amount: float, 
                   currency: str, paid_by: str, category: str = "", 
                   date: datetime = None, splits: List[Dict] = None) -> int:
        """Lägger till en utgift med delningar"""
        if date is None:
            date = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Lägg till utgiften
            cursor.execute('''
                INSERT INTO expenses (group_id, description, amount, currency, paid_by, category, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (group_id, description, amount, currency, paid_by, category, date.isoformat()))
            
            expense_id = cursor.lastrowid
            
            # Lägg till delningar
            if splits:
                for split in splits:
                    cursor.execute('''
                        INSERT INTO expense_splits (expense_id, participant_name, share)
                        VALUES (?, ?, ?)
                    ''', (expense_id, split['participant'], split['share']))
            
            conn.commit()
            return expense_id
    
    def get_expenses(self, group_id: int) -> List[Dict]:
        """Hämtar alla utgifter för en grupp med deras delningar"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.id, e.description, e.amount, e.currency, e.paid_by, 
                       e.category, e.date
                FROM expenses e
                WHERE e.group_id = ?
                ORDER BY e.date DESC
            ''', (group_id,))
            
            expenses = []
            for row in cursor.fetchall():
                expense = {
                    'id': row[0],
                    'description': row[1],
                    'amount': row[2],
                    'currency': row[3],
                    'paid_by': row[4],
                    'category': row[5],
                    'date': row[6],
                    'splits': []
                }
                
                # Hämta delningar för denna utgift
                cursor.execute('''
                    SELECT participant_name, share
                    FROM expense_splits
                    WHERE expense_id = ?
                    ORDER BY participant_name
                ''', (expense['id'],))
                
                for split_row in cursor.fetchall():
                    expense['splits'].append({
                        'participant': split_row[0],
                        'share': split_row[1]
                    })
                
                expenses.append(expense)
            
            return expenses
    
    def update_expense(self, expense_id: int, description: str, amount: float,
                      currency: str, paid_by: str, category: str = "",
                      splits: List[Dict] = None) -> bool:
        """Uppdaterar en utgift"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Uppdatera utgiften
            cursor.execute('''
                UPDATE expenses 
                SET description = ?, amount = ?, currency = ?, paid_by = ?, category = ?
                WHERE id = ?
            ''', (description, amount, currency, paid_by, category, expense_id))
            
            # Ta bort gamla delningar
            cursor.execute('DELETE FROM expense_splits WHERE expense_id = ?', (expense_id,))
            
            # Lägg till nya delningar
            if splits:
                for split in splits:
                    cursor.execute('''
                        INSERT INTO expense_splits (expense_id, participant_name, share)
                        VALUES (?, ?, ?)
                    ''', (expense_id, split['participant'], split['share']))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_expense(self, expense_id: int) -> bool:
        """Tar bort en utgift"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_group_statistics(self, group_id: int) -> Dict:
        """Hämtar statistik för en grupp"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Antal deltagare
            cursor.execute('SELECT COUNT(*) FROM participants WHERE group_id = ?', (group_id,))
            participant_count = cursor.fetchone()[0]
            
            # Antal utgifter
            cursor.execute('SELECT COUNT(*) FROM expenses WHERE group_id = ?', (group_id,))
            expense_count = cursor.fetchone()[0]
            
            # Totala utgifter per valuta
            cursor.execute('''
                SELECT currency, SUM(amount) as total
                FROM expenses
                WHERE group_id = ?
                GROUP BY currency
            ''', (group_id,))
            
            totals_by_currency = {}
            for row in cursor.fetchall():
                totals_by_currency[row[0]] = row[1]
            
            return {
                'participant_count': participant_count,
                'expense_count': expense_count,
                'totals_by_currency': totals_by_currency
            }
    
    def get_participant_balances(self, group_id: int, currency: str = "SEK") -> List[Dict]:
        """Beräknar saldon för alla deltagare i en grupp"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Hämta alla deltagare
            participants = self.get_participants(group_id)
            balances = []
            
            for participant in participants:
                # Beräkna totalt betalat
                cursor.execute('''
                    SELECT SUM(amount) FROM expenses 
                    WHERE group_id = ? AND paid_by = ?
                ''', (group_id, participant['name']))
                total_paid = cursor.fetchone()[0] or 0
                
                # Beräkna totalt skyldigt
                cursor.execute('''
                    SELECT SUM(e.amount * es.share)
                    FROM expenses e
                    JOIN expense_splits es ON e.id = es.expense_id
                    WHERE e.group_id = ? AND es.participant_name = ?
                ''', (group_id, participant['name']))
                total_owed = cursor.fetchone()[0] or 0
                
                balance = total_paid - total_owed
                
                balances.append({
                    'name': participant['name'],
                    'total_paid': total_paid,
                    'total_owed': total_owed,
                    'balance': balance
                })
            
            return balances
    
    def backup_database(self, backup_path: str) -> bool:
        """Säkerhetskopierar databasen"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"Fel vid säkerhetskopiering: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """Återställer databasen från säkerhetskopia"""
        try:
            import shutil
            shutil.copy2(backup_path, self.db_path)
            return True
        except Exception as e:
            print(f"Fel vid återställning: {e}")
            return False