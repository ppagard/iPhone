#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Huvudfil för utgiftshanteraren
Låter användaren välja mellan GUI och terminal-läge
"""

import sys
import os

def main():
    """Huvudfunktion som väljer mellan GUI och terminal-läge"""
    print("=" * 60)
    print("    UTGIFTSHANTERARE - SPLITTA KOSTNADER MELLAN GRUPPER")
    print("=" * 60)
    print()
    print("Välj läge:")
    print("1. Grafiskt gränssnitt (GUI)")
    print("2. Terminal-läge")
    print("3. Avsluta")
    print()
    
    while True:
        try:
            choice = input("Välj alternativ (1-3): ").strip()
            
            if choice == "1":
                print("Startar GUI-läge...")
                try:
                    from gui import main as gui_main
                    gui_main()
                except ImportError as e:
                    print(f"Fel: Kunde inte starta GUI: {e}")
                    print("Kontrollera att tkinter är installerat.")
                except Exception as e:
                    print(f"Fel vid start av GUI: {e}")
                break
                
            elif choice == "2":
                print("Startar terminal-läge...")
                try:
                    from expense_manager import main as terminal_main
                    terminal_main()
                except Exception as e:
                    print(f"Fel vid start av terminal-läge: {e}")
                break
                
            elif choice == "3":
                print("Avslutar programmet...")
                break
                
            else:
                print("Ogiltigt val. Försök igen.")
                
        except KeyboardInterrupt:
            print("\nAvslutar programmet...")
            break
        except Exception as e:
            print(f"Ett fel uppstod: {e}")

if __name__ == "__main__":
    main()