#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Huvudfil för utgiftshanteraren - Fas 2
Integrerar alla förbättringar från Fas 1 och Fas 2
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
    
    return missing

def show_welcome_screen():
    """Visar välkomstskärm för Fas 2"""
    print("=" * 80)
    print("    UTGIFTSHANTERARE - KOMPLETT VERSION (FAS 2)")
    print("=" * 80)
    print()
    print("Förbättringar i denna version:")
    print()
    print("FAS 1:")
    print("✓ Förbättrad GUI med tema-stöd")
    print("✓ Sortering och filtrering av data")
    print("✓ Export-funktioner (Excel, PDF, CSV)")
    print("✓ Bättre felhantering och loggning")
    print("✓ Förbättrad prestanda")
    print("✓ Snackbar-meddelanden")
    print("✓ Snabbstart (Ctrl+N, Ctrl+P, Ctrl+E)")
    print()
    print("FAS 2:")
    print("✓ Statistik och grafer med matplotlib")
    print("✓ Schemalagd säkerhetskopiering")
    print("✓ Offline-läge för valutakurser")
    print("✓ Avancerad UX-förbättringar")
    print("✓ Backup-hantering med GUI")
    print("✓ Valutakonvertering med offline-stöd")
    print("✓ Automatisk datauppdatering")
    print()
    print("=" * 80)

def main():
    """Huvudfunktion för komplett utgiftshanterare"""
    show_welcome_screen()
    
    # Kontrollera beroenden
    missing_deps = check_dependencies()
    if missing_deps:
        print("Varning: Följande beroenden saknas:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nInstallera med: pip install -r requirements_fas2.txt")
        print()
    
    print("Välj läge:")
    print("1. Komplett GUI (Fas 2 - rekommenderat)")
    print("2. Förbättrad GUI (Fas 1)")
    print("3. Terminal-läge")
    print("4. Testa funktioner")
    print("5. Systemstatus")
    print("6. Avsluta")
    print()
    
    while True:
        try:
            choice = input("Välj alternativ (1-6): ").strip()
            
            if choice == "1":
                print("Startar komplett GUI (Fas 2)...")
                try:
                    from gui_fas2_complete import main as complete_gui_main
                    complete_gui_main()
                except ImportError as e:
                    print(f"Fel: Kunde inte starta komplett GUI: {e}")
                    print("Kontrollera att alla beroenden är installerade.")
                except Exception as e:
                    print(f"Fel vid start av komplett GUI: {e}")
                break
                
            elif choice == "2":
                print("Startar förbättrad GUI (Fas 1)...")
                try:
                    from gui_improved import main as improved_gui_main
                    improved_gui_main()
                except ImportError as e:
                    print(f"Fel: Kunde inte starta förbättrad GUI: {e}")
                    print("Kontrollera att tkinter är installerat.")
                except Exception as e:
                    print(f"Fel vid start av förbättrad GUI: {e}")
                break
                
            elif choice == "3":
                print("Startar terminal-läge...")
                try:
                    from expense_manager import main as terminal_main
                    terminal_main()
                except Exception as e:
                    print(f"Fel vid start av terminal-läge: {e}")
                break
                
            elif choice == "4":
                print("Kör tester...")
                try:
                    # Testa databas
                    from database import DatabaseManager
                    db = DatabaseManager("test_fas2.db")
                    group_id = db.create_group("Test Grupp Fas 2")
                    print("✓ Databas fungerar")
                    
                    # Testa offline-valuta
                    from offline_currency import OfflineCurrencyConverter
                    converter = OfflineCurrencyConverter()
                    rate = converter.get_exchange_rate("SEK", "USD")
                    print(f"✓ Offline-valuta fungerar (SEK->USD: {rate})")
                    
                    # Testa statistik
                    from statistics_charts import ExpenseStatistics
                    stats = ExpenseStatistics(db)
                    print("✓ Statistik och grafer tillgängliga")
                    
                    # Testa backup
                    from backup_scheduler import BackupManager
                    backup_mgr = BackupManager("test_backup.db")
                    print("✓ Backup-system tillgängligt")
                    
                    # Testa export-funktioner
                    try:
                        from export_functions import ExportManager
                        export_mgr = ExportManager(db)
                        print("✓ Export-funktioner tillgängliga")
                    except ImportError:
                        print("⚠ Export-funktioner kräver ytterligare paket")
                    
                    # Rensa testdata
                    db.delete_group(group_id)
                    print("✓ Alla tester godkända!")
                    
                except Exception as e:
                    print(f"❌ Test misslyckades: {e}")
                break
                
            elif choice == "5":
                print("Systemstatus:")
                print("=" * 50)
                
                # Kontrollera beroenden
                deps = check_dependencies()
                if deps:
                    print("❌ Saknade beroenden:")
                    for dep in deps:
                        print(f"   - {dep}")
                else:
                    print("✅ Alla beroenden installerade")
                
                # Kontrollera moduler
                modules = [
                    ("Database", "database"),
                    ("Offline Currency", "offline_currency"),
                    ("Statistics", "statistics_charts"),
                    ("Backup", "backup_scheduler"),
                    ("Export", "export_functions")
                ]
                
                for name, module in modules:
                    try:
                        __import__(module)
                        print(f"✅ {name} modul tillgänglig")
                    except ImportError:
                        print(f"❌ {name} modul saknas")
                
                print("=" * 50)
                break
                
            elif choice == "6":
                print("Avslutar programmet...")
                break
                
            else:
                print("Ogiltigt val. Försök igen.")
                
        except KeyboardInterrupt:
            print("\nAvslutar programmet...")
            break
        except Exception as e:
            print(f"Ett oväntat fel uppstod: {e}")

def show_help():
    """Visar hjälpinformation för Fas 2"""
    help_text = """
UTGIFTSHANTERARE - HJÄLP (FAS 2)

Förbättringar i version 2.0:
- Förbättrad GUI med tema-stöd (ljust/mörkt)
- Sortering: Klicka på kolumnrubriker
- Filtrering: Använd sökfält och filter
- Export: Excel, PDF, CSV med formatering
- Snackbar-meddelanden för feedback
- Snabbstart: Ctrl+N, Ctrl+P, Ctrl+E

Nya funktioner i Fas 2:
- Statistik och grafer med matplotlib
- Schemalagd säkerhetskopiering
- Offline-läge för valutakurser
- Backup-hantering med GUI
- Valutakonvertering med offline-stöd
- Automatisk datauppdatering

Snabbstart:
1. Välj "Komplett GUI (Fas 2)"
2. Skapa en grupp (Ctrl+N)
3. Lägg till deltagare (Ctrl+P)
4. Lägg till utgifter (Ctrl+E)
5. Visa saldon och överföringar
6. Utforska grafer och statistik

Grafer:
- Översiktsgraf: Total översikt
- Månadstrend: Utveckling över tid
- Deltagaranalys: Detaljerad analys
- Kategorianalys: Kategorifördelning

Backup:
- Automatisk backup var 24:e timme
- Manuell backup när som helst
- Verifiering av backup-integritet
- Återställning från backup

Valuta:
- Offline-stöd med fallback-kurser
- Lokal caching av kurser
- Automatisk uppdatering
- Konvertering mellan valutor

Tips:
- Dubbelklicka på objekt för att redigera
- Använd sökfältet för att filtrera
- Exportera data via menyn "Fil"
- Byt tema via menyn "Visa"
- Utforska grafer i "Grafer"-flik
- Hantera backup i "Backup"-flik
- Konvertera valutor i "Valuta"-flik

Felsökning:
- Kontrollera att alla beroenden är installerade
- Se loggfiler för detaljerad felinformation
- Använd backup-funktionen regelbundet
- Kontrollera systemstatus för diagnostik
    """
    print(help_text)

if __name__ == "__main__":
    # Lägg till hjälpkommando
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        show_help()
    else:
        main()