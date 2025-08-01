#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testfil för databasen
"""

import sys
import os

# Lägg till projektmappen i Python-sökvägen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager

def test_database():
    """Testar databasfunktioner"""
    print("=" * 50)
    print("TESTING DATABASE")
    print("=" * 50)
    
    try:
        # Skapa databasmanager
        db = DatabaseManager("test.db")
        print("✓ Databasmanager skapad")
        
        # Testa grupphantering
        import time
        group_id = db.create_group(f"Test Grupp {int(time.time())}")
        print(f"✓ Skapade grupp med ID: {group_id}")
        
        groups = db.get_all_groups()
        print(f"✓ Hämtade {len(groups)} grupper")
        
        # Testa deltagarhantering
        participant_id = db.add_participant(group_id, "Anna", "anna@test.com")
        print(f"✓ Lade till deltagare med ID: {participant_id}")
        
        participants = db.get_participants(group_id)
        print(f"✓ Hämtade {len(participants)} deltagare")
        
        # Testa utgiftshantering
        expense_id = db.add_expense(
            group_id, 
            "Lunch", 
            100.0, 
            "SEK", 
            "Anna", 
            "Mat",
            splits=[{"participant": "Anna", "share": 1.0}]
        )
        print(f"✓ Lade till utgift med ID: {expense_id}")
        
        expenses = db.get_expenses(group_id)
        print(f"✓ Hämtade {len(expenses)} utgifter")
        
        # Testa statistik
        stats = db.get_group_statistics(group_id)
        print(f"✓ Hämtade statistik: {stats}")
        
        # Testa saldon
        balances = db.get_participant_balances(group_id)
        print(f"✓ Beräknade saldon: {balances}")
        
        # Rensa testdata
        db.delete_group(group_id)
        print("✓ Rensade testdata")
        
        print("\n" + "=" * 50)
        print("ALLA DATABASTEST GENOMFÖRDA FRAMGÅNGSRIKT!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nFel under databastestning: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database()