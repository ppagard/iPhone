#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI-modul för utgiftshanteraren
Använder tkinter för användargränssnittet
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional
import threading
from datetime import datetime
import json

from database import DatabaseManager
from expense_manager import CurrencyConverter, Expense

class ExpenseManagerGUI:
    """Huvudklass för GUI-applikationen"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Utgiftshanterare")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Initiera databas och valutakonverterare
        self.db = DatabaseManager()
        self.currency_converter = CurrencyConverter()
        
        # Variabler
        self.current_group_id = None
        self.current_group_name = None
        
        # Skapa GUI-komponenter
        self.setup_gui()
        self.load_groups()
    
    def setup_gui(self):
        """Sätter upp GUI-komponenterna"""
        # Huvudram
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Övre panel för grupphantering
        self.setup_group_panel(main_frame)
        
        # Huvudpanel med notebook för olika flikar
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Skapa flikar
        self.setup_participants_tab()
        self.setup_expenses_tab()
        self.setup_balances_tab()
        self.setup_statistics_tab()
    
    def setup_group_panel(self, parent):
        """Sätter upp grupphanteringspanelen"""
        group_frame = ttk.LabelFrame(parent, text="Grupphantering", padding=10)
        group_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Gruppval
        ttk.Label(group_frame, text="Aktiv grupp:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.group_var = tk.StringVar()
        self.group_combo = ttk.Combobox(group_frame, textvariable=self.group_var, state="readonly", width=30)
        self.group_combo.grid(row=0, column=1, padx=(0, 10))
        self.group_combo.bind('<<ComboboxSelected>>', self.on_group_selected)
        
        # Knappar
        ttk.Button(group_frame, text="Ny grupp", command=self.create_group_dialog).grid(row=0, column=2, padx=5)
        ttk.Button(group_frame, text="Redigera grupp", command=self.edit_group_dialog).grid(row=0, column=3, padx=5)
        ttk.Button(group_frame, text="Ta bort grupp", command=self.delete_group).grid(row=0, column=4, padx=5)
        
        # Status
        self.status_label = ttk.Label(group_frame, text="Ingen grupp vald")
        self.status_label.grid(row=1, column=0, columnspan=5, sticky=tk.W, pady=(5, 0))
    
    def setup_participants_tab(self):
        """Sätter upp deltagarflik"""
        participants_frame = ttk.Frame(self.notebook)
        self.notebook.add(participants_frame, text="Deltagare")
        
        # Kontrollpanel
        control_frame = ttk.Frame(participants_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="Lägg till deltagare", command=self.add_participant_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Redigera deltagare", command=self.edit_participant_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Ta bort deltagare", command=self.delete_participant).pack(side=tk.LEFT, padx=5)
        
        # Deltagarlista
        list_frame = ttk.Frame(participants_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Treeview för deltagare
        columns = ('ID', 'Namn', 'E-post', 'Skapad')
        self.participants_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.participants_tree.heading(col, text=col)
            self.participants_tree.column(col, width=150)
        
        # Scrollbar
        participants_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.participants_tree.yview)
        self.participants_tree.configure(yscrollcommand=participants_scrollbar.set)
        
        self.participants_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        participants_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_expenses_tab(self):
        """Sätter upp utgiftsflik"""
        expenses_frame = ttk.Frame(self.notebook)
        self.notebook.add(expenses_frame, text="Utgifter")
        
        # Kontrollpanel
        control_frame = ttk.Frame(expenses_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="Lägg till utgift", command=self.add_expense_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Redigera utgift", command=self.edit_expense_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Ta bort utgift", command=self.delete_expense).pack(side=tk.LEFT, padx=5)
        
        # Utgiftslista
        list_frame = ttk.Frame(expenses_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Treeview för utgifter
        columns = ('ID', 'Beskrivning', 'Belopp', 'Valuta', 'Betalad av', 'Kategori', 'Datum')
        self.expenses_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.expenses_tree.heading(col, text=col)
            if col == 'Beskrivning':
                self.expenses_tree.column(col, width=200)
            elif col == 'Datum':
                self.expenses_tree.column(col, width=150)
            else:
                self.expenses_tree.column(col, width=100)
        
        # Scrollbar
        expenses_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.expenses_tree.yview)
        self.expenses_tree.configure(yscrollcommand=expenses_scrollbar.set)
        
        self.expenses_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        expenses_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_balances_tab(self):
        """Sätter upp saldoflik"""
        balances_frame = ttk.Frame(self.notebook)
        self.notebook.add(balances_frame, text="Saldon")
        
        # Kontrollpanel
        control_frame = ttk.Frame(balances_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(control_frame, text="Valuta:").pack(side=tk.LEFT, padx=(0, 5))
        self.balance_currency_var = tk.StringVar(value="SEK")
        currency_combo = ttk.Combobox(control_frame, textvariable=self.balance_currency_var, 
                                     values=["SEK", "USD", "EUR", "GBP"], width=10)
        currency_combo.pack(side=tk.LEFT, padx=(0, 10))
        currency_combo.bind('<<ComboboxSelected>>', self.refresh_balances)
        
        ttk.Button(control_frame, text="Uppdatera saldon", command=self.refresh_balances).pack(side=tk.LEFT, padx=5)
        
        # Saldolista
        list_frame = ttk.Frame(balances_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Treeview för saldon
        columns = ('Namn', 'Betalt', 'Skyldigt', 'Saldo', 'Status')
        self.balances_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.balances_tree.heading(col, text=col)
            self.balances_tree.column(col, width=150)
        
        # Scrollbar
        balances_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.balances_tree.yview)
        self.balances_tree.configure(yscrollcommand=balances_scrollbar.set)
        
        self.balances_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        balances_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Överföringslista
        transfers_frame = ttk.LabelFrame(balances_frame, text="Rekommenderade överföringar", padding=10)
        transfers_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.transfers_text = tk.Text(transfers_frame, height=6, wrap=tk.WORD)
        transfers_scrollbar = ttk.Scrollbar(transfers_frame, orient=tk.VERTICAL, command=self.transfers_text.yview)
        self.transfers_text.configure(yscrollcommand=transfers_scrollbar.set)
        
        self.transfers_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        transfers_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_statistics_tab(self):
        """Sätter upp statistikflik"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="Statistik")
        
        # Statistikpanel
        stats_panel = ttk.LabelFrame(stats_frame, text="Gruppstatistik", padding=10)
        stats_panel.pack(fill=tk.X, padx=10, pady=10)
        
        self.stats_text = tk.Text(stats_panel, height=10, wrap=tk.WORD)
        stats_scrollbar = ttk.Scrollbar(stats_panel, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Knappar
        button_frame = ttk.Frame(stats_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Uppdatera statistik", command=self.refresh_statistics).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Exportera data", command=self.export_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Säkerhetskopiera", command=self.backup_database).pack(side=tk.LEFT, padx=5)
    
    def load_groups(self):
        """Laddar grupper från databasen"""
        groups = self.db.get_all_groups()
        group_names = [f"{g['name']} ({g['participant_count']} deltagare, {g['expense_count']} utgifter)" 
                      for g in groups]
        
        self.group_combo['values'] = group_names
        if groups:
            self.group_combo.set(group_names[0])
            self.on_group_selected()
    
    def on_group_selected(self, event=None):
        """Hanterar gruppval"""
        selection = self.group_var.get()
        if selection:
            group_name = selection.split(' (')[0]
            groups = self.db.get_all_groups()
            for group in groups:
                if group['name'] == group_name:
                    self.current_group_id = group['id']
                    self.current_group_name = group['name']
                    self.status_label.config(text=f"Aktiv grupp: {group_name}")
                    self.refresh_all_data()
                    break
    
    def refresh_all_data(self):
        """Uppdaterar all data för aktuell grupp"""
        if self.current_group_id:
            self.refresh_participants()
            self.refresh_expenses()
            self.refresh_balances()
            self.refresh_statistics()
    
    def refresh_participants(self):
        """Uppdaterar deltagarlistan"""
        if not self.current_group_id:
            return
        
        # Rensa lista
        for item in self.participants_tree.get_children():
            self.participants_tree.delete(item)
        
        # Ladda deltagare
        participants = self.db.get_participants(self.current_group_id)
        for participant in participants:
            self.participants_tree.insert('', 'end', values=(
                participant['id'],
                participant['name'],
                participant['email'] or '',
                participant['created_at']
            ))
    
    def refresh_expenses(self):
        """Uppdaterar utgiftslistan"""
        if not self.current_group_id:
            return
        
        # Rensa lista
        for item in self.expenses_tree.get_children():
            self.expenses_tree.delete(item)
        
        # Ladda utgifter
        expenses = self.db.get_expenses(self.current_group_id)
        for expense in expenses:
            # Formatera datum
            try:
                date_obj = datetime.fromisoformat(expense['date'])
                date_str = date_obj.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = expense['date']
            
            self.expenses_tree.insert('', 'end', values=(
                expense['id'],
                expense['description'],
                f"{expense['amount']:.2f}",
                expense['currency'],
                expense['paid_by'],
                expense['category'] or '',
                date_str
            ))
    
    def refresh_balances(self, event=None):
        """Uppdaterar saldolistan"""
        if not self.current_group_id:
            return
        
        # Rensa lista
        for item in self.balances_tree.get_children():
            self.balances_tree.delete(item)
        
        # Ladda saldon
        currency = self.balance_currency_var.get()
        balances = self.db.get_participant_balances(self.current_group_id, currency)
        
        for balance in balances:
            status = "Får tillbaka" if balance['balance'] > 0 else "Ska betala" if balance['balance'] < 0 else "Balanserad"
            
            self.balances_tree.insert('', 'end', values=(
                balance['name'],
                f"{balance['total_paid']:.2f}",
                f"{balance['total_owed']:.2f}",
                f"{balance['balance']:.2f}",
                status
            ))
        
        # Uppdatera överföringar
        self.update_transfers()
    
    def update_transfers(self):
        """Uppdaterar rekommenderade överföringar"""
        if not self.current_group_id:
            return
        
        self.transfers_text.delete(1.0, tk.END)
        
        currency = self.balance_currency_var.get()
        balances = self.db.get_participant_balances(self.current_group_id, currency)
        
        # Separera positiva och negativa saldon
        creditors = [(b['name'], b['balance']) for b in balances if b['balance'] > 0]
        debtors = [(b['name'], b['balance']) for b in balances if b['balance'] < 0]
        
        transfers = []
        
        for debtor_name, debtor_balance in debtors:
            remaining_debt = abs(debtor_balance)
            
            for creditor_name, creditor_balance in creditors:
                if remaining_debt <= 0:
                    break
                
                available_credit = creditor_balance
                transfer_amount = min(remaining_debt, available_credit)
                
                if transfer_amount > 0.01:
                    transfers.append({
                        'from': debtor_name,
                        'to': creditor_name,
                        'amount': transfer_amount
                    })
                    
                    remaining_debt -= transfer_amount
                    creditor_balance -= transfer_amount
        
        if transfers:
            self.transfers_text.insert(tk.END, f"Rekommenderade överföringar ({currency}):\n\n")
            for i, transfer in enumerate(transfers, 1):
                self.transfers_text.insert(tk.END, 
                    f"{i}. {transfer['from']} → {transfer['to']}: {transfer['amount']:.2f} {currency}\n")
        else:
            self.transfers_text.insert(tk.END, "Alla saldon är balanserade!")
    
    def refresh_statistics(self):
        """Uppdaterar statistik"""
        if not self.current_group_id:
            return
        
        stats = self.db.get_group_statistics(self.current_group_id)
        
        self.stats_text.delete(1.0, tk.END)
        
        self.stats_text.insert(tk.END, f"Statistik för grupp: {self.current_group_name}\n")
        self.stats_text.insert(tk.END, "=" * 50 + "\n\n")
        
        self.stats_text.insert(tk.END, f"Antal deltagare: {stats['participant_count']}\n")
        self.stats_text.insert(tk.END, f"Antal utgifter: {stats['expense_count']}\n\n")
        
        if stats['totals_by_currency']:
            self.stats_text.insert(tk.END, "Totala utgifter per valuta:\n")
            for currency, total in stats['totals_by_currency'].items():
                self.stats_text.insert(tk.END, f"  {currency}: {total:.2f}\n")
        else:
            self.stats_text.insert(tk.END, "Inga utgifter registrerade ännu.\n")
    
    def create_group_dialog(self):
        """Dialog för att skapa ny grupp"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Skapa ny grupp")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Gruppnamn:").pack(pady=10)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=40)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        def create():
            name = name_var.get().strip()
            if name:
                try:
                    self.db.create_group(name)
                    self.load_groups()
                    dialog.destroy()
                    messagebox.showinfo("Framgång", f"Skapade grupp: {name}")
                except Exception as e:
                    messagebox.showerror("Fel", f"Kunde inte skapa grupp: {e}")
            else:
                messagebox.showwarning("Varning", "Ange ett gruppnamn")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Skapa", command=create).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Avbryt", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        dialog.bind('<Return>', lambda e: create())
    
    def edit_group_dialog(self):
        """Dialog för att redigera grupp"""
        if not self.current_group_id:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Redigera grupp")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Gruppnamn:").pack(pady=10)
        name_var = tk.StringVar(value=self.current_group_name)
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=40)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        def save():
            name = name_var.get().strip()
            if name:
                try:
                    self.db.update_group(self.current_group_id, name)
                    self.load_groups()
                    dialog.destroy()
                    messagebox.showinfo("Framgång", f"Uppdaterade grupp: {name}")
                except Exception as e:
                    messagebox.showerror("Fel", f"Kunde inte uppdatera grupp: {e}")
            else:
                messagebox.showwarning("Varning", "Ange ett gruppnamn")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Spara", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Avbryt", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        dialog.bind('<Return>', lambda e: save())
    
    def delete_group(self):
        """Tar bort aktuell grupp"""
        if not self.current_group_id:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        if messagebox.askyesno("Bekräfta", f"Är du säker på att du vill ta bort gruppen '{self.current_group_name}'?"):
            try:
                self.db.delete_group(self.current_group_id)
                self.current_group_id = None
                self.current_group_name = None
                self.load_groups()
                self.refresh_all_data()
                messagebox.showinfo("Framgång", "Grupp borttagen")
            except Exception as e:
                messagebox.showerror("Fel", f"Kunde inte ta bort grupp: {e}")
    
    def add_participant_dialog(self):
        """Dialog för att lägga till deltagare"""
        if not self.current_group_id:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Lägg till deltagare")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Namn:").pack(pady=(10, 0))
        name_var = tk.StringVar()
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=40)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        ttk.Label(dialog, text="E-post (valfritt):").pack(pady=(10, 0))
        email_var = tk.StringVar()
        email_entry = ttk.Entry(dialog, textvariable=email_var, width=40)
        email_entry.pack(pady=5)
        
        def add():
            name = name_var.get().strip()
            email = email_var.get().strip()
            if name:
                try:
                    self.db.add_participant(self.current_group_id, name, email)
                    self.refresh_participants()
                    dialog.destroy()
                    messagebox.showinfo("Framgång", f"Lade till deltagare: {name}")
                except Exception as e:
                    messagebox.showerror("Fel", f"Kunde inte lägga till deltagare: {e}")
            else:
                messagebox.showwarning("Varning", "Ange ett namn")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Lägg till", command=add).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Avbryt", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        dialog.bind('<Return>', lambda e: add())
    
    def edit_participant_dialog(self):
        """Dialog för att redigera deltagare"""
        selection = self.participants_tree.selection()
        if not selection:
            messagebox.showwarning("Varning", "Välj en deltagare först")
            return
        
        item = self.participants_tree.item(selection[0])
        participant_id = item['values'][0]
        current_name = item['values'][1]
        current_email = item['values'][2]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Redigera deltagare")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Namn:").pack(pady=(10, 0))
        name_var = tk.StringVar(value=current_name)
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=40)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        ttk.Label(dialog, text="E-post (valfritt):").pack(pady=(10, 0))
        email_var = tk.StringVar(value=current_email)
        email_entry = ttk.Entry(dialog, textvariable=email_var, width=40)
        email_entry.pack(pady=5)
        
        def save():
            name = name_var.get().strip()
            email = email_var.get().strip()
            if name:
                try:
                    self.db.update_participant(participant_id, name, email)
                    self.refresh_participants()
                    dialog.destroy()
                    messagebox.showinfo("Framgång", f"Uppdaterade deltagare: {name}")
                except Exception as e:
                    messagebox.showerror("Fel", f"Kunde inte uppdatera deltagare: {e}")
            else:
                messagebox.showwarning("Varning", "Ange ett namn")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Spara", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Avbryt", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        dialog.bind('<Return>', lambda e: save())
    
    def delete_participant(self):
        """Tar bort vald deltagare"""
        selection = self.participants_tree.selection()
        if not selection:
            messagebox.showwarning("Varning", "Välj en deltagare först")
            return
        
        item = self.participants_tree.item(selection[0])
        participant_id = item['values'][0]
        participant_name = item['values'][1]
        
        if messagebox.askyesno("Bekräfta", f"Är du säker på att du vill ta bort deltagaren '{participant_name}'?"):
            try:
                self.db.delete_participant(participant_id)
                self.refresh_participants()
                messagebox.showinfo("Framgång", f"Tog bort deltagare: {participant_name}")
            except Exception as e:
                messagebox.showerror("Fel", f"Kunde inte ta bort deltagare: {e}")
    
    def add_expense_dialog(self):
        """Dialog för att lägga till utgift"""
        if not self.current_group_id:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        participants = self.db.get_participants(self.current_group_id)
        if not participants:
            messagebox.showwarning("Varning", "Lägg till deltagare först")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Lägg till utgift")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Formulär
        ttk.Label(dialog, text="Beskrivning:").pack(pady=(10, 0))
        description_var = tk.StringVar()
        description_entry = ttk.Entry(dialog, textvariable=description_var, width=50)
        description_entry.pack(pady=5)
        description_entry.focus()
        
        ttk.Label(dialog, text="Belopp:").pack(pady=(10, 0))
        amount_var = tk.StringVar()
        amount_entry = ttk.Entry(dialog, textvariable=amount_var, width=20)
        amount_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Valuta:").pack(pady=(10, 0))
        currency_var = tk.StringVar(value="SEK")
        currency_combo = ttk.Combobox(dialog, textvariable=currency_var, 
                                     values=["SEK", "USD", "EUR", "GBP"], width=20)
        currency_combo.pack(pady=5)
        
        ttk.Label(dialog, text="Betalad av:").pack(pady=(10, 0))
        paid_by_var = tk.StringVar()
        paid_by_combo = ttk.Combobox(dialog, textvariable=paid_by_var, 
                                     values=[p['name'] for p in participants], width=30)
        paid_by_combo.pack(pady=5)
        
        ttk.Label(dialog, text="Kategori (valfritt):").pack(pady=(10, 0))
        category_var = tk.StringVar()
        category_entry = ttk.Entry(dialog, textvariable=category_var, width=30)
        category_entry.pack(pady=5)
        
        # Delning
        ttk.Label(dialog, text="Delning:").pack(pady=(10, 0))
        split_frame = ttk.Frame(dialog)
        split_frame.pack(fill=tk.X, padx=20)
        
        split_var = tk.StringVar(value="equal")
        ttk.Radiobutton(split_frame, text="Dela lika", variable=split_var, value="equal").pack(anchor=tk.W)
        ttk.Radiobutton(split_frame, text="Manuell delning", variable=split_var, value="manual").pack(anchor=tk.W)
        ttk.Radiobutton(split_frame, text="Bara betalaren", variable=split_var, value="payer").pack(anchor=tk.W)
        
        def add():
            try:
                description = description_var.get().strip()
                amount = float(amount_var.get())
                currency = currency_var.get()
                paid_by = paid_by_var.get()
                category = category_var.get().strip()
                split_type = split_var.get()
                
                if not description or amount <= 0 or not paid_by:
                    messagebox.showwarning("Varning", "Fyll i alla obligatoriska fält")
                    return
                
                # Skapa delningar
                splits = []
                if split_type == "equal":
                    share = 1.0 / len(participants)
                    for participant in participants:
                        splits.append({'participant': participant['name'], 'share': share})
                elif split_type == "payer":
                    splits.append({'participant': paid_by, 'share': 1.0})
                else:
                    # Manuell delning - för enkelhetens skull delar vi lika
                    share = 1.0 / len(participants)
                    for participant in participants:
                        splits.append({'participant': participant['name'], 'share': share})
                
                self.db.add_expense(self.current_group_id, description, amount, currency, 
                                  paid_by, category, splits=splits)
                self.refresh_expenses()
                dialog.destroy()
                messagebox.showinfo("Framgång", f"Lade till utgift: {description}")
                
            except ValueError:
                messagebox.showerror("Fel", "Ange ett giltigt belopp")
            except Exception as e:
                messagebox.showerror("Fel", f"Kunde inte lägga till utgift: {e}")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Lägg till", command=add).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Avbryt", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        dialog.bind('<Return>', lambda e: add())
    
    def edit_expense_dialog(self):
        """Dialog för att redigera utgift"""
        selection = self.expenses_tree.selection()
        if not selection:
            messagebox.showwarning("Varning", "Välj en utgift först")
            return
        
        item = self.expenses_tree.item(selection[0])
        expense_id = item['values'][0]
        
        # Hämta utgift från databasen
        expenses = self.db.get_expenses(self.current_group_id)
        expense = None
        for exp in expenses:
            if exp['id'] == expense_id:
                expense = exp
                break
        
        if not expense:
            messagebox.showerror("Fel", "Kunde inte hitta utgiften")
            return
        
        # Skapa dialog (liknande add_expense_dialog men med förifyllda värden)
        dialog = tk.Toplevel(self.root)
        dialog.title("Redigera utgift")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Formulär med förifyllda värden
        ttk.Label(dialog, text="Beskrivning:").pack(pady=(10, 0))
        description_var = tk.StringVar(value=expense['description'])
        description_entry = ttk.Entry(dialog, textvariable=description_var, width=50)
        description_entry.pack(pady=5)
        description_entry.focus()
        
        ttk.Label(dialog, text="Belopp:").pack(pady=(10, 0))
        amount_var = tk.StringVar(value=str(expense['amount']))
        amount_entry = ttk.Entry(dialog, textvariable=amount_var, width=20)
        amount_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Valuta:").pack(pady=(10, 0))
        currency_var = tk.StringVar(value=expense['currency'])
        currency_combo = ttk.Combobox(dialog, textvariable=currency_var, 
                                     values=["SEK", "USD", "EUR", "GBP"], width=20)
        currency_combo.pack(pady=5)
        
        participants = self.db.get_participants(self.current_group_id)
        ttk.Label(dialog, text="Betalad av:").pack(pady=(10, 0))
        paid_by_var = tk.StringVar(value=expense['paid_by'])
        paid_by_combo = ttk.Combobox(dialog, textvariable=paid_by_var, 
                                     values=[p['name'] for p in participants], width=30)
        paid_by_combo.pack(pady=5)
        
        ttk.Label(dialog, text="Kategori (valfritt):").pack(pady=(10, 0))
        category_var = tk.StringVar(value=expense['category'] or '')
        category_entry = ttk.Entry(dialog, textvariable=category_var, width=30)
        category_entry.pack(pady=5)
        
        def save():
            try:
                description = description_var.get().strip()
                amount = float(amount_var.get())
                currency = currency_var.get()
                paid_by = paid_by_var.get()
                category = category_var.get().strip()
                
                if not description or amount <= 0 or not paid_by:
                    messagebox.showwarning("Varning", "Fyll i alla obligatoriska fält")
                    return
                
                # För enkelhetens skull behåller vi samma delningar
                splits = expense['splits']
                
                self.db.update_expense(expense_id, description, amount, currency, 
                                     paid_by, category, splits=splits)
                self.refresh_expenses()
                dialog.destroy()
                messagebox.showinfo("Framgång", f"Uppdaterade utgift: {description}")
                
            except ValueError:
                messagebox.showerror("Fel", "Ange ett giltigt belopp")
            except Exception as e:
                messagebox.showerror("Fel", f"Kunde inte uppdatera utgift: {e}")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Spara", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Avbryt", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        dialog.bind('<Return>', lambda e: save())
    
    def delete_expense(self):
        """Tar bort vald utgift"""
        selection = self.expenses_tree.selection()
        if not selection:
            messagebox.showwarning("Varning", "Välj en utgift först")
            return
        
        item = self.expenses_tree.item(selection[0])
        expense_id = item['values'][0]
        expense_description = item['values'][1]
        
        if messagebox.askyesno("Bekräfta", f"Är du säker på att du vill ta bort utgiften '{expense_description}'?"):
            try:
                self.db.delete_expense(expense_id)
                self.refresh_expenses()
                messagebox.showinfo("Framgång", f"Tog bort utgift: {expense_description}")
            except Exception as e:
                messagebox.showerror("Fel", f"Kunde inte ta bort utgift: {e}")
    
    def export_data(self):
        """Exporterar data till JSON-fil"""
        if not self.current_group_id:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Hämta all data för gruppen
                group = self.db.get_group_by_id(self.current_group_id)
                participants = self.db.get_participants(self.current_group_id)
                expenses = self.db.get_expenses(self.current_group_id)
                
                export_data = {
                    'group': group,
                    'participants': participants,
                    'expenses': expenses
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("Framgång", f"Data exporterad till {filename}")
                
            except Exception as e:
                messagebox.showerror("Fel", f"Kunde inte exportera data: {e}")
    
    def backup_database(self):
        """Säkerhetskopierar databasen"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )
        
        if filename:
            if self.db.backup_database(filename):
                messagebox.showinfo("Framgång", f"Databas säkerhetskopierad till {filename}")
            else:
                messagebox.showerror("Fel", "Kunde inte säkerhetskopiera databasen")
    
    def run(self):
        """Startar GUI-applikationen"""
        self.root.mainloop()

def main():
    """Huvudfunktion för GUI-applikationen"""
    app = ExpenseManagerGUI()
    app.run()

if __name__ == "__main__":
    main()