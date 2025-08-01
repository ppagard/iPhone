#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utgiftshanterare - Program för att hantera utgifter och splitta dem mellan deltagare
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests
from dateutil import parser
from tabulate import tabulate
from colorama import init, Fore, Style

# Initiera colorama för färgad output
init(autoreset=True)

class CurrencyConverter:
    """Hanterar valutakonvertering med hjälp av API"""
    
    def __init__(self):
        self.base_url = "https://api.exchangerate-api.com/v4/latest/"
        self.cache = {}
        self.cache_file = "currency_cache.json"
        self.load_cache()
    
    def load_cache(self):
        """Laddar cachade valutakurser från fil"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
        except Exception as e:
            print(f"Varning: Kunde inte ladda valutacache: {e}")
            self.cache = {}
    
    def save_cache(self):
        """Sparar cachade valutakurser till fil"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
        except Exception as e:
            print(f"Varning: Kunde inte spara valutacache: {e}")
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Hämtar växelkurs mellan två valutor"""
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency == to_currency:
            return 1.0
        
        cache_key = f"{from_currency}_{to_currency}"
        
        # Kontrollera cache först
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            response = requests.get(f"{self.base_url}{from_currency}")
            if response.status_code == 200:
                data = response.json()
                rate = data['rates'].get(to_currency)
                if rate:
                    self.cache[cache_key] = rate
                    self.save_cache()
                    return rate
        except Exception as e:
            print(f"Fel vid hämtning av växelkurs: {e}")
        
        # Fallback till 1.0 om API misslyckas
        return 1.0
    
    def convert_amount(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Konverterar belopp mellan valutor"""
        rate = self.get_exchange_rate(from_currency, to_currency)
        return amount * rate

class Participant:
    """Representerar en deltagare i gruppen"""
    
    def __init__(self, name: str, email: str = ""):
        self.name = name
        self.email = email
        self.expenses_paid: List[Dict] = []
        self.expenses_owed: List[Dict] = []
    
    def add_expense_paid(self, expense: Dict):
        """Lägger till en utgift som deltagaren har betalat"""
        self.expenses_paid.append(expense)
    
    def add_expense_owed(self, expense: Dict):
        """Lägger till en utgift som deltagaren är skyldig"""
        self.expenses_owed.append(expense)
    
    def get_total_paid(self, currency: str = "SEK") -> float:
        """Beräknar totalt betalat belopp i given valuta"""
        total = 0.0
        for expense in self.expenses_paid:
            if expense['currency'] == currency:
                total += expense['amount']
            else:
                # Konvertera till önskad valuta
                converter = CurrencyConverter()
                converted = converter.convert_amount(
                    expense['amount'], 
                    expense['currency'], 
                    currency
                )
                total += converted
        return total
    
    def get_total_owed(self, currency: str = "SEK") -> float:
        """Beräknar totalt skyldigt belopp i given valuta"""
        total = 0.0
        for expense in self.expenses_owed:
            if expense['currency'] == currency:
                total += expense['amount']
            else:
                # Konvertera till önskad valuta
                converter = CurrencyConverter()
                converted = converter.convert_amount(
                    expense['amount'], 
                    expense['currency'], 
                    currency
                )
                total += converted
        return total
    
    def get_balance(self, currency: str = "SEK") -> float:
        """Beräknar saldo (positivt = ska få tillbaka, negativt = ska betala)"""
        return self.get_total_paid(currency) - self.get_total_owed(currency)

class Expense:
    """Representerar en utgift"""
    
    def __init__(self, description: str, amount: float, currency: str, 
                 paid_by: str, date: datetime = None, category: str = ""):
        self.description = description
        self.amount = amount
        self.currency = currency.upper()
        self.paid_by = paid_by
        self.date = date or datetime.now()
        self.category = category
        self.splits: List[Dict] = []  # Lista över hur utgiften ska delas
    
    def add_split(self, participant_name: str, share: float):
        """Lägger till en delning av utgiften"""
        self.splits.append({
            'participant': participant_name,
            'share': share
        })
    
    def to_dict(self) -> Dict:
        """Konverterar utgift till dictionary för lagring"""
        return {
            'description': self.description,
            'amount': self.amount,
            'currency': self.currency,
            'paid_by': self.paid_by,
            'date': self.date.isoformat(),
            'category': self.category,
            'splits': self.splits
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Expense':
        """Skapar utgift från dictionary"""
        expense = cls(
            description=data['description'],
            amount=data['amount'],
            currency=data['currency'],
            paid_by=data['paid_by'],
            date=parser.parse(data['date']),
            category=data.get('category', '')
        )
        expense.splits = data.get('splits', [])
        return expense

class Group:
    """Representerar en grupp av deltagare"""
    
    def __init__(self, name: str):
        self.name = name
        self.participants: Dict[str, Participant] = {}
        self.expenses: List[Expense] = []
        self.currency_converter = CurrencyConverter()
    
    def add_participant(self, name: str, email: str = "") -> Participant:
        """Lägger till en deltagare i gruppen"""
        if name not in self.participants:
            self.participants[name] = Participant(name, email)
        return self.participants[name]
    
    def remove_participant(self, name: str) -> bool:
        """Tar bort en deltagare från gruppen"""
        if name in self.participants:
            del self.participants[name]
            return True
        return False
    
    def add_expense(self, expense: Expense):
        """Lägger till en utgift i gruppen"""
        self.expenses.append(expense)
        
        # Uppdatera deltagarnas utgifter
        if expense.paid_by in self.participants:
            self.participants[expense.paid_by].add_expense_paid({
                'amount': expense.amount,
                'currency': expense.currency,
                'description': expense.description,
                'date': expense.date
            })
        
        # Uppdatera deltagarnas skyldigheter baserat på splits
        for split in expense.splits:
            participant_name = split['participant']
            if participant_name in self.participants:
                share_amount = expense.amount * split['share']
                self.participants[participant_name].add_expense_owed({
                    'amount': share_amount,
                    'currency': expense.currency,
                    'description': expense.description,
                    'date': expense.date
                })
    
    def get_group_balance(self, currency: str = "SEK") -> Dict[str, float]:
        """Beräknar saldo för alla deltagare"""
        balances = {}
        for name, participant in self.participants.items():
            balances[name] = participant.get_balance(currency)
        return balances
    
    def get_total_expenses(self, currency: str = "SEK") -> float:
        """Beräknar totala utgifter i given valuta"""
        total = 0.0
        for expense in self.expenses:
            if expense.currency == currency:
                total += expense.amount
            else:
                converted = self.currency_converter.convert_amount(
                    expense.amount, expense.currency, currency
                )
                total += converted
        return total
    
    def calculate_optimal_transfers(self, currency: str = "SEK") -> List[Dict]:
        """Beräknar optimala överföringar för att balansera gruppen"""
        balances = self.get_group_balance(currency)
        
        # Separera positiva och negativa saldon
        creditors = [(name, balance) for name, balance in balances.items() if balance > 0]
        debtors = [(name, balance) for name, balance in balances.items() if balance < 0]
        
        transfers = []
        
        for debtor_name, debtor_balance in debtors:
            remaining_debt = abs(debtor_balance)
            
            for creditor_name, creditor_balance in creditors:
                if remaining_debt <= 0:
                    break
                
                available_credit = creditor_balance
                transfer_amount = min(remaining_debt, available_credit)
                
                if transfer_amount > 0.01:  # Ignorera små belopp
                    transfers.append({
                        'from': debtor_name,
                        'to': creditor_name,
                        'amount': transfer_amount,
                        'currency': currency
                    })
                    
                    remaining_debt -= transfer_amount
                    creditor_balance -= transfer_amount
        
        return transfers
    
    def save_to_file(self, filename: str):
        """Sparar gruppdata till fil"""
        data = {
            'name': self.name,
            'participants': {
                name: {
                    'name': participant.name,
                    'email': participant.email
                }
                for name, participant in self.participants.items()
            },
            'expenses': [expense.to_dict() for expense in self.expenses]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'Group':
        """Laddar gruppdata från fil"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        group = cls(data['name'])
        
        # Ladda deltagare
        for name, participant_data in data['participants'].items():
            group.add_participant(participant_data['name'], participant_data.get('email', ''))
        
        # Ladda utgifter
        for expense_data in data['expenses']:
            expense = Expense.from_dict(expense_data)
            group.add_expense(expense)
        
        return group

class ExpenseManager:
    """Huvudklass för utgiftshanteraren"""
    
    def __init__(self):
        self.groups: Dict[str, Group] = {}
        self.current_group: Optional[Group] = None
    
    def create_group(self, name: str) -> Group:
        """Skapar en ny grupp"""
        self.groups[name] = Group(name)
        if not self.current_group:
            self.current_group = self.groups[name]
        return self.groups[name]
    
    def select_group(self, name: str) -> bool:
        """Väljer en grupp som aktiv"""
        if name in self.groups:
            self.current_group = self.groups[name]
            return True
        return False
    
    def list_groups(self) -> List[str]:
        """Listar alla grupper"""
        return list(self.groups.keys())
    
    def get_current_group(self) -> Optional[Group]:
        """Hämtar aktuell grupp"""
        return self.current_group

def print_header():
    """Skriver ut programmets header"""
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}    UTGIFTSHANTERARE - SPLITTA KOSTNADER MELLAN GRUPPER")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

def print_menu():
    """Skriver ut huvudmenyn"""
    print(f"\n{Fore.YELLOW}HUVUDMENY:{Style.RESET_ALL}")
    print("1. Hantera grupper")
    print("2. Hantera deltagare")
    print("3. Hantera utgifter")
    print("4. Visa saldon och överföringar")
    print("5. Spara/ladda data")
    print("6. Avsluta")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

def main():
    """Huvudfunktion för programmet"""
    print_header()
    
    manager = ExpenseManager()
    
    # Skapa en standardgrupp om ingen finns
    if not manager.groups:
        default_group = manager.create_group("Min Grupp")
        print(f"{Fore.GREEN}Skapade standardgrupp: {default_group.name}{Style.RESET_ALL}")
    
    while True:
        print_menu()
        
        try:
            choice = input(f"{Fore.GREEN}Välj alternativ (1-6): {Style.RESET_ALL}").strip()
            
            if choice == "1":
                handle_groups(manager)
            elif choice == "2":
                handle_participants(manager)
            elif choice == "3":
                handle_expenses(manager)
            elif choice == "4":
                show_balances(manager)
            elif choice == "5":
                handle_data(manager)
            elif choice == "6":
                print(f"{Fore.YELLOW}Tack för att du använde Utgiftshanteraren!{Style.RESET_ALL}")
                break
            else:
                print(f"{Fore.RED}Ogiltigt val. Försök igen.{Style.RESET_ALL}")
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Avslutar programmet...{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"{Fore.RED}Ett fel uppstod: {e}{Style.RESET_ALL}")

def handle_groups(manager: ExpenseManager):
    """Hanterar grupprelaterade funktioner"""
    while True:
        print(f"\n{Fore.YELLOW}GRUPPHANTERING:{Style.RESET_ALL}")
        print("1. Skapa ny grupp")
        print("2. Välj grupp")
        print("3. Lista grupper")
        print("4. Tillbaka till huvudmeny")
        
        choice = input(f"{Fore.GREEN}Välj alternativ (1-4): {Style.RESET_ALL}").strip()
        
        if choice == "1":
            name = input("Ange gruppnamn: ").strip()
            if name:
                group = manager.create_group(name)
                print(f"{Fore.GREEN}Skapade grupp: {name}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Gruppnamn kan inte vara tomt.{Style.RESET_ALL}")
        
        elif choice == "2":
            groups = manager.list_groups()
            if groups:
                print("Tillgängliga grupper:")
                for i, group_name in enumerate(groups, 1):
                    print(f"{i}. {group_name}")
                
                try:
                    idx = int(input("Välj grupp (nummer): ")) - 1
                    if 0 <= idx < len(groups):
                        manager.select_group(groups[idx])
                        print(f"{Fore.GREEN}Valde grupp: {groups[idx]}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}Ogiltigt val.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED}Ange ett giltigt nummer.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Inga grupper finns ännu.{Style.RESET_ALL}")
        
        elif choice == "3":
            groups = manager.list_groups()
            if groups:
                print("Tillgängliga grupper:")
                for group_name in groups:
                    group = manager.groups[group_name]
                    participant_count = len(group.participants)
                    expense_count = len(group.expenses)
                    print(f"- {group_name} ({participant_count} deltagare, {expense_count} utgifter)")
            else:
                print(f"{Fore.YELLOW}Inga grupper finns ännu.{Style.RESET_ALL}")
        
        elif choice == "4":
            break

def handle_participants(manager: ExpenseManager):
    """Hanterar deltagarrelaterade funktioner"""
    current_group = manager.get_current_group()
    if not current_group:
        print(f"{Fore.RED}Ingen grupp vald. Välj en grupp först.{Style.RESET_ALL}")
        return
    
    while True:
        print(f"\n{Fore.YELLOW}DELTAGARHANTERING - Grupp: {current_group.name}{Style.RESET_ALL}")
        print("1. Lägg till deltagare")
        print("2. Ta bort deltagare")
        print("3. Lista deltagare")
        print("4. Tillbaka till huvudmeny")
        
        choice = input(f"{Fore.GREEN}Välj alternativ (1-4): {Style.RESET_ALL}").strip()
        
        if choice == "1":
            name = input("Ange namn: ").strip()
            if name:
                email = input("Ange e-post (valfritt): ").strip()
                participant = current_group.add_participant(name, email)
                print(f"{Fore.GREEN}Lade till deltagare: {name}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Namn kan inte vara tomt.{Style.RESET_ALL}")
        
        elif choice == "2":
            participants = list(current_group.participants.keys())
            if participants:
                print("Deltagare:")
                for i, name in enumerate(participants, 1):
                    print(f"{i}. {name}")
                
                try:
                    idx = int(input("Välj deltagare att ta bort (nummer): ")) - 1
                    if 0 <= idx < len(participants):
                        name = participants[idx]
                        if current_group.remove_participant(name):
                            print(f"{Fore.GREEN}Tog bort deltagare: {name}{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.RED}Kunde inte ta bort deltagare.{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}Ogiltigt val.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED}Ange ett giltigt nummer.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Inga deltagare finns ännu.{Style.RESET_ALL}")
        
        elif choice == "3":
            participants = current_group.participants
            if participants:
                print("Deltagare i gruppen:")
                for name, participant in participants.items():
                    print(f"- {name}")
                    if participant.email:
                        print(f"  E-post: {participant.email}")
            else:
                print(f"{Fore.YELLOW}Inga deltagare finns ännu.{Style.RESET_ALL}")
        
        elif choice == "4":
            break

def handle_expenses(manager: ExpenseManager):
    """Hanterar utgiftsrelaterade funktioner"""
    current_group = manager.get_current_group()
    if not current_group:
        print(f"{Fore.RED}Ingen grupp vald. Välj en grupp först.{Style.RESET_ALL}")
        return
    
    while True:
        print(f"\n{Fore.YELLOW}UTGIFTSHANTERING - Grupp: {current_group.name}{Style.RESET_ALL}")
        print("1. Lägg till utgift")
        print("2. Lista utgifter")
        print("3. Tillbaka till huvudmeny")
        
        choice = input(f"{Fore.GREEN}Välj alternativ (1-3): {Style.RESET_ALL}").strip()
        
        if choice == "1":
            add_expense(current_group)
        
        elif choice == "2":
            list_expenses(current_group)
        
        elif choice == "3":
            break

def add_expense(group: Group):
    """Lägger till en ny utgift"""
    if not group.participants:
        print(f"{Fore.RED}Inga deltagare finns i gruppen. Lägg till deltagare först.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.CYAN}LÄGG TILL UTGIFT{Style.RESET_ALL}")
    
    description = input("Beskrivning: ").strip()
    if not description:
        print(f"{Fore.RED}Beskrivning kan inte vara tom.{Style.RESET_ALL}")
        return
    
    try:
        amount = float(input("Belopp: ").strip())
        if amount <= 0:
            print(f"{Fore.RED}Belopp måste vara större än 0.{Style.RESET_ALL}")
            return
    except ValueError:
        print(f"{Fore.RED}Ange ett giltigt belopp.{Style.RESET_ALL}")
        return
    
    currency = input("Valuta (t.ex. SEK, USD, EUR): ").strip().upper()
    if not currency:
        currency = "SEK"
    
    # Visa deltagare som kan ha betalat
    participants = list(group.participants.keys())
    print("\nDeltagare som kan ha betalat:")
    for i, name in enumerate(participants, 1):
        print(f"{i}. {name}")
    
    try:
        paid_idx = int(input("Vem betalade? (nummer): ")) - 1
        if 0 <= paid_idx < len(participants):
            paid_by = participants[paid_idx]
        else:
            print(f"{Fore.RED}Ogiltigt val.{Style.RESET_ALL}")
            return
    except ValueError:
        print(f"{Fore.RED}Ange ett giltigt nummer.{Style.RESET_ALL}")
        return
    
    category = input("Kategori (valfritt): ").strip()
    
    # Skapa utgift
    expense = Expense(description, amount, currency, paid_by, category=category)
    
    # Hantera delning av utgiften
    print(f"\n{Fore.CYAN}DELNING AV UTGIFT{Style.RESET_ALL}")
    print("1. Dela lika mellan alla")
    print("2. Dela manuellt")
    print("3. Bara betalaren betalar")
    
    split_choice = input("Välj delning (1-3): ").strip()
    
    if split_choice == "1":
        # Dela lika mellan alla
        share = 1.0 / len(participants)
        for participant_name in participants:
            expense.add_split(participant_name, share)
    
    elif split_choice == "2":
        # Manuell delning
        print("Ange andel för varje deltagare (summan ska bli 1.0):")
        total_share = 0.0
        
        for participant_name in participants:
            try:
                share = float(input(f"Andel för {participant_name} (0-1): "))
                if 0 <= share <= 1:
                    expense.add_split(participant_name, share)
                    total_share += share
                else:
                    print(f"{Fore.RED}Andel måste vara mellan 0 och 1.{Style.RESET_ALL}")
                    return
            except ValueError:
                print(f"{Fore.RED}Ange ett giltigt nummer.{Style.RESET_ALL}")
                return
        
        if abs(total_share - 1.0) > 0.01:
            print(f"{Fore.RED}Summan av andelar måste vara 1.0 (nuvarande: {total_share}){Style.RESET_ALL}")
            return
    
    elif split_choice == "3":
        # Bara betalaren betalar
        expense.add_split(paid_by, 1.0)
    
    else:
        print(f"{Fore.RED}Ogiltigt val.{Style.RESET_ALL}")
        return
    
    # Lägg till utgiften i gruppen
    group.add_expense(expense)
    print(f"{Fore.GREEN}Lade till utgift: {description} ({amount} {currency}){Style.RESET_ALL}")

def list_expenses(group: Group):
    """Listar alla utgifter i gruppen"""
    if not group.expenses:
        print(f"{Fore.YELLOW}Inga utgifter finns ännu.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.CYAN}UTGIFTER I GRUPPEN{Style.RESET_ALL}")
    
    # Skapa tabell för utgifter
    table_data = []
    for i, expense in enumerate(group.expenses, 1):
        date_str = expense.date.strftime("%Y-%m-%d %H:%M")
        splits_str = ", ".join([f"{split['participant']} ({split['share']:.2f})" 
                               for split in expense.splits])
        
        table_data.append([
            i,
            expense.description,
            f"{expense.amount} {expense.currency}",
            expense.paid_by,
            date_str,
            expense.category,
            splits_str
        ])
    
    headers = ["#", "Beskrivning", "Belopp", "Betalad av", "Datum", "Kategori", "Delning"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def show_balances(manager: ExpenseManager):
    """Visar saldon och överföringar"""
    current_group = manager.get_current_group()
    if not current_group:
        print(f"{Fore.RED}Ingen grupp vald. Välj en grupp först.{Style.RESET_ALL}")
        return
    
    if not current_group.participants:
        print(f"{Fore.YELLOW}Inga deltagare finns i gruppen.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.CYAN}SALDON - Grupp: {current_group.name}{Style.RESET_ALL}")
    
    # Visa saldon för varje deltagare
    balances = current_group.get_group_balance()
    table_data = []
    
    for name, balance in balances.items():
        status = "Får tillbaka" if balance > 0 else "Ska betala" if balance < 0 else "Balanserad"
        color = Fore.GREEN if balance > 0 else Fore.RED if balance < 0 else Fore.YELLOW
        table_data.append([name, f"{balance:.2f} SEK", status])
    
    headers = ["Deltagare", "Saldo", "Status"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Visa optimala överföringar
    transfers = current_group.calculate_optimal_transfers()
    if transfers:
        print(f"\n{Fore.CYAN}REKOMMENDERADE ÖVERFÖRINGAR{Style.RESET_ALL}")
        transfer_data = []
        
        for transfer in transfers:
            transfer_data.append([
                transfer['from'],
                transfer['to'],
                f"{transfer['amount']:.2f} {transfer['currency']}"
            ])
        
        headers = ["Från", "Till", "Belopp"]
        print(tabulate(transfer_data, headers=headers, tablefmt="grid"))
    else:
        print(f"\n{Fore.GREEN}Alla saldon är balanserade!{Style.RESET_ALL}")
    
    # Visa totala utgifter
    total_expenses = current_group.get_total_expenses()
    print(f"\n{Fore.CYAN}Totala utgifter: {total_expenses:.2f} SEK{Style.RESET_ALL}")

def handle_data(manager: ExpenseManager):
    """Hanterar sparande och laddning av data"""
    while True:
        print(f"\n{Fore.YELLOW}DATAHANTERING{Style.RESET_ALL}")
        print("1. Spara alla grupper")
        print("2. Ladda grupp från fil")
        print("3. Tillbaka till huvudmeny")
        
        choice = input(f"{Fore.GREEN}Välj alternativ (1-3): {Style.RESET_ALL}").strip()
        
        if choice == "1":
            for group_name, group in manager.groups.items():
                filename = f"{group_name.lower().replace(' ', '_')}.json"
                try:
                    group.save_to_file(filename)
                    print(f"{Fore.GREEN}Sparade grupp '{group_name}' till {filename}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}Fel vid sparande av {group_name}: {e}{Style.RESET_ALL}")
        
        elif choice == "2":
            filename = input("Ange filnamn: ").strip()
            if filename:
                try:
                    group = Group.load_from_file(filename)
                    manager.groups[group.name] = group
                    print(f"{Fore.GREEN}Laddade grupp '{group.name}' från {filename}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}Fel vid laddning: {e}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Ange ett filnamn.{Style.RESET_ALL}")
        
        elif choice == "3":
            break

if __name__ == "__main__":
    main()