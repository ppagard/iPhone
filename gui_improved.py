#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Förbättrad GUI för utgiftshanteraren
Med tema-stöd, sortering, filtrering och bättre UX
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional
import threading
from datetime import datetime
import json
import os
from enum import Enum

from database import DatabaseManager
from expense_manager import CurrencyConverter, Expense

class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"

class ImprovedExpenseManagerGUI:
    """Förbättrad GUI-klass med tema-stöd och avancerade funktioner"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Utgiftshanterare - Förbättrad version")
        self.root.geometry("1400x900")
        
        # Initiera databas och valutakonverterare
        self.db = DatabaseManager()
        self.currency_converter = CurrencyConverter()
        
        # Variabler
        self.current_group_id = None
        self.current_group_name = None
        self.current_theme = Theme.LIGHT
        self.sort_column = None
        self.sort_reverse = False
        
        # Ladda inställningar
        self.load_settings()
        
        # Skapa GUI-komponenter
        self.setup_gui()
        self.apply_theme()
        self.load_groups()
        
        # Bind events
        self.bind_events()
    
    def load_settings(self):
        """Laddar användarinställningar"""
        self.settings_file = "settings.json"
        self.settings = {
            'theme': 'light',
            'window_size': '1400x900',
            'auto_backup': True,
            'currency': 'SEK'
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
        except Exception as e:
            print(f"Kunde inte ladda inställningar: {e}")
    
    def save_settings(self):
        """Sparar användarinställningar"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Kunde inte spara inställningar: {e}")
    
    def setup_gui(self):
        """Sätter upp GUI-komponenterna"""
        # Huvudram
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Meny
        self.setup_menu()
        
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
        
        # Statusbar
        self.setup_statusbar()
    
    def setup_menu(self):
        """Sätter upp menyn"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Fil-meny
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fil", menu=file_menu)
        file_menu.add_command(label="Exportera till Excel", command=self.export_to_excel)
        file_menu.add_command(label="Exportera till PDF", command=self.export_to_pdf)
        file_menu.add_command(label="Exportera till CSV", command=self.export_to_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Säkerhetskopiera", command=self.backup_database)
        file_menu.add_command(label="Återställ från backup", command=self.restore_database)
        file_menu.add_separator()
        file_menu.add_command(label="Avsluta", command=self.root.quit)
        
        # Redigera-meny
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Redigera", menu=edit_menu)
        edit_menu.add_command(label="Ångra", command=self.undo_action)
        edit_menu.add_command(label="Gör om", command=self.redo_action)
        
        # Visa-meny
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Visa", menu=view_menu)
        view_menu.add_command(label="Ljust tema", command=lambda: self.change_theme(Theme.LIGHT))
        view_menu.add_command(label="Mörkt tema", command=lambda: self.change_theme(Theme.DARK))
        
        # Hjälp-meny
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hjälp", menu=help_menu)
        help_menu.add_command(label="Snabbstart", command=self.show_help)
        help_menu.add_command(label="Om", command=self.show_about)
    
    def setup_group_panel(self, parent):
        """Sätter upp grupphanteringspanelen med förbättringar"""
        group_frame = ttk.LabelFrame(parent, text="Grupphantering", padding=10)
        group_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Övre rad
        top_row = ttk.Frame(group_frame)
        top_row.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(top_row, text="Aktiv grupp:").pack(side=tk.LEFT, padx=(0, 5))
        self.group_var = tk.StringVar()
        self.group_combo = ttk.Combobox(top_row, textvariable=self.group_var, state="readonly", width=40)
        self.group_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.group_combo.bind('<<ComboboxSelected>>', self.on_group_selected)
        
        # Knappar
        ttk.Button(top_row, text="Ny grupp", command=self.create_group_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_row, text="Redigera", command=self.edit_group_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_row, text="Ta bort", command=self.delete_group).pack(side=tk.LEFT, padx=5)
        
        # Undre rad med sökfunktion
        bottom_row = ttk.Frame(group_frame)
        bottom_row.pack(fill=tk.X)
        
        ttk.Label(bottom_row, text="Sök:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(bottom_row, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_var.trace('w', self.on_search_changed)
        
        # Status
        self.status_label = ttk.Label(bottom_row, text="Ingen grupp vald")
        self.status_label.pack(side=tk.RIGHT)
    
    def setup_participants_tab(self):
        """Sätter upp förbättrad deltagarflik"""
        participants_frame = ttk.Frame(self.notebook)
        self.notebook.add(participants_frame, text="Deltagare")
        
        # Kontrollpanel
        control_frame = ttk.Frame(participants_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="Lägg till", command=self.add_participant_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Redigera", command=self.edit_participant_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Ta bort", command=self.delete_participant).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Uppdatera", command=self.refresh_participants).pack(side=tk.LEFT, padx=5)
        
        # Deltagarlista med förbättringar
        list_frame = ttk.Frame(participants_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Treeview för deltagare med sortering
        columns = ('ID', 'Namn', 'E-post', 'Skapad', 'Antal utgifter', 'Totalt betalat')
        self.participants_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.participants_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.participants_tree, c))
            if col == 'Namn':
                self.participants_tree.column(col, width=150)
            elif col == 'E-post':
                self.participants_tree.column(col, width=200)
            elif col == 'Skapad':
                self.participants_tree.column(col, width=150)
            else:
                self.participants_tree.column(col, width=100)
        
        # Scrollbar
        participants_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.participants_tree.yview)
        self.participants_tree.configure(yscrollcommand=participants_scrollbar.set)
        
        self.participants_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        participants_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_expenses_tab(self):
        """Sätter upp förbättrad utgiftsflik"""
        expenses_frame = ttk.Frame(self.notebook)
        self.notebook.add(expenses_frame, text="Utgifter")
        
        # Kontrollpanel
        control_frame = ttk.Frame(expenses_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="Lägg till", command=self.add_expense_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Redigera", command=self.edit_expense_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Ta bort", command=self.delete_expense).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Uppdatera", command=self.refresh_expenses).pack(side=tk.LEFT, padx=5)
        
        # Filtreringspanel
        filter_frame = ttk.LabelFrame(expenses_frame, text="Filtrering", padding=5)
        filter_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Kategori:").pack(side=tk.LEFT, padx=(0, 5))
        self.category_filter_var = tk.StringVar()
        self.category_filter_combo = ttk.Combobox(filter_frame, textvariable=self.category_filter_var, width=15)
        self.category_filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(filter_frame, text="Valuta:").pack(side=tk.LEFT, padx=(0, 5))
        self.currency_filter_var = tk.StringVar()
        self.currency_filter_combo = ttk.Combobox(filter_frame, textvariable=self.currency_filter_var, width=10)
        self.currency_filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(filter_frame, text="Filtrera", command=self.apply_expense_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Rensa", command=self.clear_expense_filters).pack(side=tk.LEFT, padx=5)
        
        # Utgiftslista
        list_frame = ttk.Frame(expenses_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Treeview för utgifter med sortering
        columns = ('ID', 'Beskrivning', 'Belopp', 'Valuta', 'Betalad av', 'Kategori', 'Datum', 'Delning')
        self.expenses_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.expenses_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.expenses_tree, c))
            if col == 'Beskrivning':
                self.expenses_tree.column(col, width=200)
            elif col == 'Datum':
                self.expenses_tree.column(col, width=150)
            elif col == 'Delning':
                self.expenses_tree.column(col, width=200)
            else:
                self.expenses_tree.column(col, width=100)
        
        # Scrollbar
        expenses_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.expenses_tree.yview)
        self.expenses_tree.configure(yscrollcommand=expenses_scrollbar.set)
        
        self.expenses_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        expenses_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_balances_tab(self):
        """Sätter upp förbättrad saldoflik"""
        balances_frame = ttk.Frame(self.notebook)
        self.notebook.add(balances_frame, text="Saldon")
        
        # Kontrollpanel
        control_frame = ttk.Frame(balances_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(control_frame, text="Valuta:").pack(side=tk.LEFT, padx=(0, 5))
        self.balance_currency_var = tk.StringVar(value=self.settings.get('currency', 'SEK'))
        currency_combo = ttk.Combobox(control_frame, textvariable=self.balance_currency_var, 
                                     values=["SEK", "USD", "EUR", "GBP"], width=10)
        currency_combo.pack(side=tk.LEFT, padx=(0, 10))
        currency_combo.bind('<<ComboboxSelected>>', self.refresh_balances)
        
        ttk.Button(control_frame, text="Uppdatera", command=self.refresh_balances).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Exportera saldon", command=self.export_balances).pack(side=tk.LEFT, padx=5)
        
        # Saldolista
        list_frame = ttk.Frame(balances_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Treeview för saldon med sortering
        columns = ('Namn', 'Betalt', 'Skyldigt', 'Saldo', 'Status', 'Procent')
        self.balances_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.balances_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.balances_tree, c))
            self.balances_tree.column(col, width=120)
        
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
        """Sätter upp förbättrad statistikflik"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="Statistik")
        
        # Kontrollpanel
        control_frame = ttk.Frame(stats_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="Uppdatera", command=self.refresh_statistics).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Exportera rapport", command=self.export_statistics).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Säkerhetskopiera", command=self.backup_database).pack(side=tk.LEFT, padx=5)
        
        # Statistikpanel
        stats_panel = ttk.LabelFrame(stats_frame, text="Gruppstatistik", padding=10)
        stats_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.stats_text = tk.Text(stats_panel, wrap=tk.WORD)
        stats_scrollbar = ttk.Scrollbar(stats_panel, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_statusbar(self):
        """Sätter upp statusbar"""
        self.statusbar = ttk.Label(self.root, text="Redo", relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def bind_events(self):
        """Bindar events för bättre UX"""
        # Dubbelklick för redigering
        self.participants_tree.bind('<Double-1>', lambda e: self.edit_participant_dialog())
        self.expenses_tree.bind('<Double-1>', lambda e: self.edit_expense_dialog())
        
        # Snabbstart
        self.root.bind('<Control-n>', lambda e: self.create_group_dialog())
        self.root.bind('<Control-p>', lambda e: self.add_participant_dialog())
        self.root.bind('<Control-e>', lambda e: self.add_expense_dialog())
        
        # Spara inställningar vid stängning
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def apply_theme(self):
        """Applicerar valt tema"""
        if self.current_theme == Theme.DARK:
            self.root.configure(bg='#2b2b2b')
            style = ttk.Style()
            style.theme_use('clam')
            style.configure('TLabel', background='#2b2b2b', foreground='white')
            style.configure('TFrame', background='#2b2b2b')
            style.configure('TLabelframe', background='#2b2b2b', foreground='white')
            style.configure('TLabelframe.Label', background='#2b2b2b', foreground='white')
        else:
            self.root.configure(bg='#f0f0f0')
            style = ttk.Style()
            style.theme_use('clam')
    
    def change_theme(self, theme):
        """Ändrar tema"""
        self.current_theme = theme
        self.settings['theme'] = theme.value
        self.apply_theme()
        self.save_settings()
        self.show_snackbar(f"Tema ändrat till {theme.value}")
    
    def sort_treeview(self, tree, column):
        """Sorterar treeview per kolumn"""
        items = [(tree.set(item, column), item) for item in tree.get_children('')]
        
        # Toggle sort direction
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
        
        self.sort_column = column
        
        # Sort items
        items.sort(reverse=self.sort_reverse)
        
        # Rearrange items in sorted positions
        for index, (val, item) in enumerate(items):
            tree.move(item, '', index)
        
        # Update column header to show sort direction
        tree.heading(column, text=f"{column} {'↓' if self.sort_reverse else '↑'}")
    
    def on_search_changed(self, *args):
        """Hanterar sökändringar"""
        search_term = self.search_var.get().lower()
        # Implementera sökfunktionalitet här
        self.update_status(f"Söker efter: {search_term}")
    
    def apply_expense_filters(self):
        """Applicerar utgiftsfilter"""
        category = self.category_filter_var.get()
        currency = self.currency_filter_var.get()
        self.refresh_expenses_with_filters(category, currency)
    
    def clear_expense_filters(self):
        """Rensar utgiftsfilter"""
        self.category_filter_var.set('')
        self.currency_filter_var.set('')
        self.refresh_expenses()
    
    def show_snackbar(self, message, duration=3000):
        """Visar en snackbar-meddelande"""
        snackbar = tk.Toplevel(self.root)
        snackbar.geometry(f"+{self.root.winfo_x() + 50}+{self.root.winfo_y() + 50}")
        snackbar.overrideredirect(True)
        snackbar.configure(bg='#333333')
        
        label = tk.Label(snackbar, text=message, bg='#333333', fg='white', padx=20, pady=10)
        label.pack()
        
        self.root.after(duration, snackbar.destroy)
    
    def update_status(self, message):
        """Uppdaterar statusbar"""
        self.statusbar.config(text=message)
    
    def undo_action(self):
        """Ångrar senaste åtgärd"""
        self.show_snackbar("Ångra-funktion kommer snart!")
    
    def redo_action(self):
        """Gör om senaste åtgärd"""
        self.show_snackbar("Gör om-funktion kommer snart!")
    
    def show_help(self):
        """Visar hjälp"""
        help_text = """
Snabbstart:
- Ctrl+N: Ny grupp
- Ctrl+P: Lägg till deltagare
- Ctrl+E: Lägg till utgift
- Dubbelklick: Redigera objekt

Sortering:
- Klicka på kolumnrubriker för att sortera
- Klicka igen för att växla riktning

Filtrering:
- Använd sökfältet för att filtrera
- Använd filter-panelen för utgifter
        """
        messagebox.showinfo("Hjälp", help_text)
    
    def show_about(self):
        """Visar om-dialog"""
        about_text = """
Utgiftshanterare - Förbättrad version
Version 2.0

Funktioner:
- GUI med tema-stöd
- Sortering och filtrering
- Export-funktioner
- Förbättrad databashantering
        """
        messagebox.showinfo("Om", about_text)
    
    def on_closing(self):
        """Hanterar stängning av applikationen"""
        self.save_settings()
        self.root.destroy()
    
    # Övriga metoder (load_groups, refresh_all_data, etc.) är samma som i original GUI
    # Men med förbättrad felhantering och statusuppdateringar
    
    def load_groups(self):
        """Laddar grupper från databasen"""
        try:
            groups = self.db.get_all_groups()
            group_names = [f"{g['name']} ({g['participant_count']} deltagare, {g['expense_count']} utgifter)" 
                          for g in groups]
            
            self.group_combo['values'] = group_names
            if groups:
                self.group_combo.set(group_names[0])
                self.on_group_selected()
            
            self.update_status(f"Laddade {len(groups)} grupper")
        except Exception as e:
            self.show_error(f"Fel vid laddning av grupper: {e}")
    
    def show_error(self, message):
        """Visar felmeddelande"""
        messagebox.showerror("Fel", message)
        self.update_status(f"Fel: {message}")
    
    def show_success(self, message):
        """Visar framgångsmeddelande"""
        self.show_snackbar(message)
        self.update_status(message)
    
    # Export-funktioner kommer att implementeras separat
    
    def run(self):
        """Startar GUI-applikationen"""
        self.root.mainloop()

def main():
    """Huvudfunktion för förbättrad GUI"""
    app = ImprovedExpenseManagerGUI()
    app.run()

if __name__ == "__main__":
    main()