#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Huvudfil för utgiftshanteraren - Fas 3
Integrerar alla förbättringar från Fas 1, 2 och 3
"""

import sys
import os
import json
from datetime import datetime

def check_dependencies():
    """Kontrollerar att alla beroenden är installerade"""
    missing = []

    # Grundläggande beroenden
    try:
        import tkinter
    except ImportError:
        missing.append("tkinter")

    try:
        import sqlite3
    except ImportError:
        missing.append("sqlite3")

    try:
        import requests
    except ImportError:
        missing.append("requests")

    # Fas 1 beroenden
    try:
        import pandas
    except ImportError:
        missing.append("pandas (för Excel-export)")

    try:
        import reportlab
    except ImportError:
        missing.append("reportlab (för PDF-export)")

    # Fas 2 beroenden
    try:
        import matplotlib
    except ImportError:
        missing.append("matplotlib (för grafer)")

    try:
        import numpy
    except ImportError:
        missing.append("numpy (för grafer)")

    try:
        import schedule
    except ImportError:
        missing.append("schedule (för automatisk backup)")

    # Fas 3 beroenden
    try:
        import scikit_learn
    except ImportError:
        missing.append("scikit-learn (för AI-funktioner)")

    try:
        import scipy
    except ImportError:
        missing.append("scipy (för AI-funktioner)")

    return missing

def show_welcome_screen():
    """Visar välkomstskärm"""
    print("=" * 80)
    print("VÄLKOMMEN TILL UTGIFTSHANTERAREN - FAS 3")
    print("=" * 80)
    print()
    print("En avancerad applikation för att hantera utgifter och splitta dem mellan gruppdeltagare.")
    print()
    print("FUNKTIONER PER FAS:")
    print()
    print("FAS 1 - Förbättrad GUI och Export:")
    print("  • Förbättrad GUI med tema-stöd (ljus/mörk)")
    print("  • Sortering och filtrering av data")
    print("  • Snackbar-meddelanden och statusrad")
    print("  • Tangentbordskort (Ctrl+N, Ctrl+E, Ctrl+P)")
    print("  • Dubbelklick-redigering")
    print("  • Export till Excel (.xlsx), PDF, CSV och JSON")
    print()
    print("FAS 2 - Statistik, Backup och Offline-valuta:")
    print("  • Statistik och grafer med matplotlib")
    print("  • Schemalagd säkerhetskopiering")
    print("  • Offline-valutakonvertering med caching")
    print("  • Backup-verifiering och komprimering")
    print()
    print("FAS 3 - Cloud-synkronisering, AI och Avancerad rapportering:")
    print("  • Cloud-synkronisering med REST API")
    print("  • AI-baserade rekommendationer och förutsägelser")
    print("  • Avancerad rapportering med anpassningsbara mallar")
    print("  • Konfliktlösning för synkronisering")
    print("  • Maskininlärning för utgiftsanalys")
    print()
    print("=" * 80)

def show_menu():
    """Visar huvudmeny"""
    print("\nVÄLJ ALTERNATIV:")
    print("1. Komplett GUI (Fas 3 - rekommenderat)")
    print("2. Förbättrad GUI (Fas 1)")
    print("3. Terminal-läge")
    print("4. Testa funktioner")
    print("5. Systemstatus")
    print("6. Installera beroenden")
    print("7. Avsluta")
    print()

def test_functions():
    """Testar olika funktioner"""
    print("\nTESTAR FUNKTIONER...")
    print("=" * 50)
    
    # Testa grundläggande funktioner
    print("1. Testar grundläggande funktioner...")
    try:
        from database import DatabaseManager
        from expense_manager import CurrencyConverter
        print("   ✓ Databas och valutakonverterare OK")
    except Exception as e:
        print(f"   ✗ Fel: {e}")
    
    # Testa Fas 1 funktioner
    print("2. Testar Fas 1 funktioner...")
    try:
        from export_functions import ExportManager
        print("   ✓ Export-funktioner OK")
    except Exception as e:
        print(f"   ✗ Fel: {e}")
    
    # Testa Fas 2 funktioner
    print("3. Testar Fas 2 funktioner...")
    try:
        from statistics_charts import ExpenseStatistics
        print("   ✓ Statistik och grafer OK")
    except Exception as e:
        print(f"   ✗ Fel: {e}")
    
    try:
        from backup_scheduler import BackupManager
        print("   ✓ Backup-hantering OK")
    except Exception as e:
        print(f"   ✗ Fel: {e}")
    
    try:
        from offline_currency import OfflineCurrencyConverter
        print("   ✓ Offline-valuta OK")
    except Exception as e:
        print(f"   ✗ Fel: {e}")
    
    # Testa Fas 3 funktioner
    print("4. Testar Fas 3 funktioner...")
    try:
        from cloud_sync import CloudSyncManager
        print("   ✓ Cloud-synkronisering OK")
    except Exception as e:
        print(f"   ✗ Fel: {e}")
    
    try:
        from ai_recommendations import AIRecommendationEngine
        print("   ✓ AI-rekommendationer OK")
    except Exception as e:
        print(f"   ✗ Fel: {e}")
    
    try:
        from advanced_reporting import AdvancedReportingEngine
        print("   ✓ Avancerad rapportering OK")
    except Exception as e:
        print(f"   ✗ Fel: {e}")
    
    print("\nTestning slutförd!")

def show_system_status():
    """Visar systemstatus"""
    print("\nSYSTEMSTATUS:")
    print("=" * 50)
    
    # Kontrollera beroenden
    missing = check_dependencies()
    if missing:
        print("❌ Saknade beroenden:")
        for dep in missing:
            print(f"   - {dep}")
    else:
        print("✅ Alla beroenden installerade")
    
    # Kontrollera filer
    print("\nFiler:")
    required_files = [
        "database.py",
        "expense_manager.py", 
        "gui_improved.py",
        "export_functions.py",
        "statistics_charts.py",
        "backup_scheduler.py",
        "offline_currency.py",
        "cloud_sync.py",
        "ai_recommendations.py",
        "advanced_reporting.py",
        "gui_fas3_complete.py"
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (saknas)")
    
    # Kontrollera databas
    print("\nDatabas:")
    if os.path.exists("expense_manager.db"):
        print("   ✅ expense_manager.db finns")
    else:
        print("   ⚠️  expense_manager.db saknas (skapas automatiskt)")
    
    # Kontrollera inställningar
    print("\nInställningar:")
    if os.path.exists("settings.json"):
        print("   ✅ settings.json finns")
    else:
        print("   ⚠️  settings.json saknas (skapas automatiskt)")

def install_dependencies():
    """Installerar beroenden"""
    print("\nINSTALLERAR BEROENDEN...")
    print("=" * 50)
    
    # Kontrollera om vi är i en virtuell miljö
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Varning: Du kör inte i en virtuell miljö")
        print("Rekommenderat: python3 -m venv venv && source venv/bin/activate")
        print()
    
    # Installera från requirements_fas3.txt
    if os.path.exists("requirements_fas3.txt"):
        print("Installerar från requirements_fas3.txt...")
        os.system("pip install -r requirements_fas3.txt")
    else:
        print("❌ requirements_fas3.txt saknas")
        return
    
    print("\n✅ Installation slutförd!")
    print("Kör 'python main_fas3.py' igen för att starta applikationen.")

def run_complete_gui():
    """Kör komplett GUI (Fas 3)"""
    try:
        from gui_fas3_complete import CompleteExpenseManagerGUI
        print("Startar komplett GUI (Fas 3)...")
        app = CompleteExpenseManagerGUI()
        app.run()
    except Exception as e:
        print(f"Fel vid start av komplett GUI: {e}")
        print("Kontrollera att alla beroenden är installerade.")

def run_improved_gui():
    """Kör förbättrad GUI (Fas 1)"""
    try:
        from gui_improved import ImprovedExpenseManagerGUI
        print("Startar förbättrad GUI (Fas 1)...")
        app = ImprovedExpenseManagerGUI()
        app.run()
    except Exception as e:
        print(f"Fel vid start av förbättrad GUI: {e}")

def run_terminal_mode():
    """Kör terminal-läge"""
    try:
        from expense_manager import ExpenseManager
        print("Startar terminal-läge...")
        manager = ExpenseManager()
        manager.run()
    except Exception as e:
        print(f"Fel vid start av terminal-läge: {e}")

def main():
    """Huvudfunktion"""
    # Visa välkomstskärm
    show_welcome_screen()
    
    while True:
        try:
            show_menu()
            choice = input("Ange ditt val (1-7): ").strip()
            
            if choice == "1":
                run_complete_gui()
                break
            elif choice == "2":
                run_improved_gui()
                break
            elif choice == "3":
                run_terminal_mode()
                break
            elif choice == "4":
                test_functions()
            elif choice == "5":
                show_system_status()
            elif choice == "6":
                install_dependencies()
            elif choice == "7":
                print("\nTack för att du använde utgiftshanteraren!")
                break
            else:
                print("Ogiltigt val. Försök igen.")
                
        except KeyboardInterrupt:
            print("\n\nAvslutar...")
            break
        except Exception as e:
            print(f"Ett oväntat fel uppstod: {e}")

if __name__ == "__main__":
    main()