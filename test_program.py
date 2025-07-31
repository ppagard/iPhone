#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testfil för utgiftshanteraren
"""

import sys
import os

# Lägg till projektmappen i Python-sökvägen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from expense_manager import CurrencyConverter, Participant, Expense, Group, ExpenseManager

def test_currency_converter():
    """Testar valutakonvertering"""
    print("Testing CurrencyConverter...")
    converter = CurrencyConverter()
    
    # Testa grundläggande konvertering
    rate = converter.get_exchange_rate("SEK", "USD")
    print(f"SEK to USD rate: {rate}")
    
    # Testa samma valuta
    rate = converter.get_exchange_rate("SEK", "SEK")
    print(f"SEK to SEK rate: {rate}")
    
    # Testa beloppskonvertering
    amount = converter.convert_amount(100, "SEK", "USD")
    print(f"100 SEK = {amount} USD")

def test_participant():
    """Testar deltagarfunktioner"""
    print("\nTesting Participant...")
    participant = Participant("Anna", "anna@example.com")
    
    # Lägg till utgifter
    participant.add_expense_paid({
        'amount': 100,
        'currency': 'SEK',
        'description': 'Lunch',
        'date': None
    })
    
    participant.add_expense_owed({
        'amount': 50,
        'currency': 'SEK',
        'description': 'Lunch',
        'date': None
    })
    
    print(f"Total paid: {participant.get_total_paid()}")
    print(f"Total owed: {participant.get_total_owed()}")
    print(f"Balance: {participant.get_balance()}")

def test_expense():
    """Testar utgiftsfunktioner"""
    print("\nTesting Expense...")
    expense = Expense("Lunch", 100, "SEK", "Anna", category="Mat")
    
    # Lägg till delningar
    expense.add_split("Anna", 0.5)
    expense.add_split("Erik", 0.5)
    
    print(f"Expense: {expense.description}")
    print(f"Amount: {expense.amount} {expense.currency}")
    print(f"Paid by: {expense.paid_by}")
    print(f"Splits: {expense.splits}")

def test_group():
    """Testar gruppfunktioner"""
    print("\nTesting Group...")
    group = Group("Test Group")
    
    # Lägg till deltagare
    group.add_participant("Anna", "anna@example.com")
    group.add_participant("Erik", "erik@example.com")
    
    # Skapa och lägg till utgift
    expense = Expense("Lunch", 100, "SEK", "Anna", category="Mat")
    expense.add_split("Anna", 0.5)
    expense.add_split("Erik", 0.5)
    
    group.add_expense(expense)
    
    print(f"Group: {group.name}")
    print(f"Participants: {list(group.participants.keys())}")
    print(f"Expenses: {len(group.expenses)}")
    
    # Visa saldon
    balances = group.get_group_balance()
    print(f"Balances: {balances}")

def test_manager():
    """Testar huvudhanteraren"""
    print("\nTesting ExpenseManager...")
    manager = ExpenseManager()
    
    # Skapa grupp
    group = manager.create_group("Test Group")
    print(f"Created group: {group.name}")
    
    # Lägg till deltagare
    group.add_participant("Anna", "anna@example.com")
    group.add_participant("Erik", "erik@example.com")
    
    # Skapa och lägg till utgift
    expense = Expense("Lunch", 100, "SEK", "Anna", category="Mat")
    expense.add_split("Anna", 0.5)
    expense.add_split("Erik", 0.5)
    
    group.add_expense(expense)
    
    print(f"Groups: {manager.list_groups()}")
    print(f"Current group: {manager.get_current_group().name}")

def main():
    """Kör alla tester"""
    print("=" * 50)
    print("TESTING UTGIFTSHANTERAREN")
    print("=" * 50)
    
    try:
        test_currency_converter()
        test_participant()
        test_expense()
        test_group()
        test_manager()
        
        print("\n" + "=" * 50)
        print("ALLA TEST GENOMFÖRDA FRAMGÅNGSRIKT!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nFel under testning: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()