#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Komplett GUI för utgiftshanteraren - Fas 2
Integrerar alla förbättringar från Fas 1 och Fas 2
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional
import threading
from datetime import datetime
import json
import os
from enum import Enum

# Importera alla moduler
from database import DatabaseManager
from expense_manager import CurrencyConverter, Expense
from gui_improved import ImprovedExpenseManagerGUI, Theme
from export_functions import ExportManager, get_export_formats, check_export_dependencies
from statistics_charts import ExpenseStatistics, create_chart_widget, check_matplotlib_availability
from backup_scheduler import BackupManager, BackupDialog, check_schedule_availability
from offline_currency import OfflineCurrencyConverter, create_currency_widget, check_offline_availability

class CompleteExpenseManagerGUI:
    """Komplett GUI med alla förbättringar från Fas 1 och Fas 2"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Utgiftshanterare - Komplett version (Fas 2)")
        self.root.geometry("1600x1000")
        
        # Initiera alla moduler
        self.db = DatabaseManager()
        self.currency_converter = OfflineCurrencyConverter()  # Använd offline-version
        self.export_manager = ExportManager(self.db)
        self.statistics = ExpenseStatistics(self.db)
        self.backup_manager = BackupManager()
        
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
        
        # Starta automatisk backup
        self.backup_manager.start_auto_backup()
    
    def load_settings(self):
        """Laddar användarinställningar"""
        self.settings_file = "settings_fas2.json"
        self.settings = {
            'theme': 'light',
            'window_size': '1600x1000',
            'auto_backup': True,
            'currency': 'SEK',
            'show_charts': True,
            'auto_update_rates': True
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
        self.setup_charts_tab()  # Ny flik för grafer
        self.setup_backup_tab()  # Ny flik för backup
        self.setup_currency_tab()  # Ny flik för valuta
        
        # Statusbar
        self.setup_statusbar()
    
    def setup_menu(self):
        """Sätter upp menyn med alla funktioner"""
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
        view_menu.add_separator()
        view_menu.add_command(label="Visa grafer", command=self.toggle_charts)
        
        # Verktyg-meny
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Verktyg", menu=tools_menu)
        tools_menu.add_command(label="Backup-hantering", command=self.show_backup_dialog)
        tools_menu.add_command(label="Valutakonvertering", command=self.show_currency_dialog)
        tools_menu.add_command(label="Uppdatera valutakurser", command=self.update_currency_rates)
        tools_menu.add_separator()
        tools_menu.add_command(label="Rensa gamla data", command=self.cleanup_old_data)
        
        # Hjälp-meny
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hjälp", menu=help_menu)
        help_menu.add_command(label="Snabbstart", command=self.show_help)
        help_menu.add_command(label="Om", command=self.show_about)
        help_menu.add_command(label="Systemstatus", command=self.show_system_status)
    
    def setup_group_panel(self, parent):
        """Sätter upp grupphanteringspanelen"""
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
        """Sätter upp deltagarflik"""
        participants_frame = ttk.Frame(self.notebook)
        self.notebook.add(participants_frame, text="Deltagare")
        
        # Kontrollpanel
        control_frame = ttk.Frame(participants_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="Lägg till", command=self.add_participant_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Redigera", command=self.edit_participant_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Ta bort", command=self.delete_participant).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Uppdatera", command=self.refresh_participants).pack(side=tk.LEFT, padx=5)
        
        # Deltagarlista
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
        """Sätter upp utgiftsflik"""
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
        """Sätter upp saldoflik"""
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
        """Sätter upp statistikflik"""
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
    
    def setup_charts_tab(self):
        """Sätter upp grafflik (ny i Fas 2)"""
        charts_frame = ttk.Frame(self.notebook)
        self.notebook.add(charts_frame, text="Grafer")
        
        # Kontrollpanel
        control_frame = ttk.Frame(charts_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="Översiktsgraf", command=self.show_overview_chart).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Månadstrend", command=self.show_monthly_chart).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Deltagaranalys", command=self.show_participant_chart).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Kategorianalys", command=self.show_category_chart).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Spara graf", command=self.save_chart).pack(side=tk.LEFT, padx=5)
        
        # Grafpanel
        self.chart_frame = ttk.Frame(charts_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Platshållare för graf
        self.chart_placeholder = ttk.Label(self.chart_frame, text="Välj en graf från knapparna ovan")
        self.chart_placeholder.pack(expand=True)
    
    def setup_backup_tab(self):
        """Sätter upp backup-flik (ny i Fas 2)"""
        backup_frame = ttk.Frame(self.notebook)
        self.notebook.add(backup_frame, text="Backup")
        
        # Kontrollpanel
        control_frame = ttk.Frame(backup_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="Skapa backup nu", command=self.create_backup_now).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Backup-hantering", command=self.show_backup_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Verifiera backup", command=self.verify_backup).pack(side=tk.LEFT, padx=5)
        
        # Backup-statistik
        stats_frame = ttk.LabelFrame(backup_frame, text="Backup-statistik", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.backup_stats_text = tk.Text(stats_frame, height=8, wrap=tk.WORD)
        backup_stats_scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.backup_stats_text.yview)
        self.backup_stats_text.configure(yscrollcommand=backup_stats_scrollbar.set)
        
        self.backup_stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        backup_stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.update_backup_stats()
    
    def setup_currency_tab(self):
        """Sätter upp valuta-flik (ny i Fas 2)"""
        currency_frame = ttk.Frame(self.notebook)
        self.notebook.add(currency_frame, text="Valuta")
        
        # Valutakonvertering widget
        self.currency_widget = create_currency_widget(currency_frame, self.currency_converter)
        self.currency_widget.pack(fill=tk.X, padx=10, pady=10)
        
        # Valutastatus
        status_frame = ttk.LabelFrame(currency_frame, text="Valutastatus", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.currency_status_text = tk.Text(status_frame, height=6, wrap=tk.WORD)
        currency_status_scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.currency_status_text.yview)
        self.currency_status_text.configure(yscrollcommand=currency_status_scrollbar.set)
        
        self.currency_status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        currency_status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.update_currency_status()
    
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
    
    # Graffunktioner (Fas 2)
    def show_overview_chart(self):
        """Visar översiktsgraf"""
        if not self.current_group_id:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        try:
            fig = self.statistics.create_expense_overview_chart(self.current_group_id)
            self.display_chart(fig)
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte skapa graf: {e}")
    
    def show_monthly_chart(self):
        """Visar månadstrendgraf"""
        if not self.current_group_id:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        try:
            fig = self.statistics.create_monthly_trend_chart(self.current_group_id)
            self.display_chart(fig)
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte skapa graf: {e}")
    
    def show_participant_chart(self):
        """Visar deltagaranalysgraf"""
        if not self.current_group_id:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        try:
            fig = self.statistics.create_participant_analysis_chart(self.current_group_id)
            self.display_chart(fig)
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte skapa graf: {e}")
    
    def show_category_chart(self):
        """Visar kategorianalysgraf"""
        if not self.current_group_id:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        try:
            fig = self.statistics.create_category_analysis_chart(self.current_group_id)
            self.display_chart(fig)
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte skapa graf: {e}")
    
    def display_chart(self, fig):
        """Visar graf i GUI"""
        # Rensa tidigare graf
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # Skapa canvas för graf
        canvas = create_chart_widget(self.chart_frame, fig)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def save_chart(self):
        """Sparar aktuell graf som bild"""
        if not hasattr(self, 'current_fig'):
            messagebox.showwarning("Varning", "Ingen graf att spara")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.statistics.save_chart_as_image(self.current_fig, filename)
                messagebox.showinfo("Framgång", f"Graf sparad som {filename}")
            except Exception as e:
                messagebox.showerror("Fel", f"Kunde inte spara graf: {e}")
    
    # Backup-funktioner (Fas 2)
    def create_backup_now(self):
        """Skapar backup nu"""
        try:
            backup_path = self.backup_manager.create_backup()
            if backup_path:
                self.show_success(f"Backup skapad: {backup_path}")
                self.update_backup_stats()
            else:
                self.show_error("Kunde inte skapa backup")
        except Exception as e:
            self.show_error(f"Fel vid skapande av backup: {e}")
    
    def show_backup_dialog(self):
        """Visar backup-hanteringsdialog"""
        dialog = BackupDialog(self.root, self.backup_manager)
        dialog.show_backup_dialog()
    
    def verify_backup(self):
        """Verifierar senaste backup"""
        backups = self.backup_manager.list_backups()
        if backups:
            latest_backup = backups[0]
            is_valid = self.backup_manager.verify_backup(latest_backup['path'])
            if is_valid:
                self.show_success("Senaste backup är giltig")
            else:
                self.show_error("Senaste backup är korrupt")
        else:
            self.show_warning("Inga backups hittades")
    
    def update_backup_stats(self):
        """Uppdaterar backup-statistik"""
        stats = self.backup_manager.get_backup_stats()
        
        stats_text = f"""
Backup-statistik:
================

Totalt antal backups: {stats['total_backups']}
Total storlek: {stats['total_size_mb']:.1f} MB
Äldsta backup: {stats['oldest_backup'] or 'Ingen'}
Senaste backup: {stats['newest_backup'] or 'Ingen'}

Automatisk backup: {'Aktiverad' if stats['auto_backup_enabled'] else 'Inaktiverad'}
Backup-intervall: {stats['backup_interval_hours']} timmar
        """
        
        self.backup_stats_text.delete(1.0, tk.END)
        self.backup_stats_text.insert(1.0, stats_text)
    
    # Valutafunktioner (Fas 2)
    def update_currency_rates(self):
        """Uppdaterar valutakurser"""
        try:
            results = self.currency_converter.update_all_rates()
            self.show_success(f"Uppdaterade {results['successful']} kurser, {results['failed']} misslyckades")
            self.update_currency_status()
        except Exception as e:
            self.show_error(f"Fel vid uppdatering av kurser: {e}")
    
    def update_currency_status(self):
        """Uppdaterar valutastatus"""
        status = self.currency_converter.get_offline_status()
        
        status_text = f"""
Valutastatus:
=============

Online: {'Ja' if status['online'] else 'Nej'}
Cache: {status['cache_stats']['valid_cached_pairs']} av {status['cache_stats']['total_cached_pairs']} giltiga
Databas: {status['database_entries']} poster
Fallback: {'Tillgänglig' if status['fallback_available'] else 'Ej tillgänglig'}

Tillgängliga valutor: {', '.join(self.currency_converter.get_available_currencies())}
        """
        
        self.currency_status_text.delete(1.0, tk.END)
        self.currency_status_text.insert(1.0, status_text)
    
    def show_currency_dialog(self):
        """Visar valutakonverteringsdialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Valutakonvertering")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        currency_widget = create_currency_widget(dialog, self.currency_converter)
        currency_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Övriga funktioner (ärvda från gui_improved.py)
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
    
    def show_snackbar(self, message, duration=3000):
        """Visar en snackbar-meddelande"""
        snackbar = tk.Toplevel(self.root)
        snackbar.geometry(f"+{self.root.winfo_x() + 50}+{self.root.winfo_y() + 50}")
        snackbar.overrideredirect(True)
        snackbar.configure(bg='#333333')
        
        label = tk.Label(snackbar, text=message, bg='#333333', fg='white', padx=20, pady=10)
        label.pack()
        
        self.root.after(duration, snackbar.destroy)
    
    def show_success(self, message):
        """Visar framgångsmeddelande"""
        self.show_snackbar(message)
        self.update_status(message)
    
    def show_error(self, message):
        """Visar felmeddelande"""
        messagebox.showerror("Fel", message)
        self.update_status(f"Fel: {message}")
    
    def show_warning(self, message):
        """Visar varningsmeddelande"""
        messagebox.showwarning("Varning", message)
        self.update_status(f"Varning: {message}")
    
    def update_status(self, message):
        """Uppdaterar statusbar"""
        self.statusbar.config(text=message)
    
    def on_closing(self):
        """Hanterar stängning av applikationen"""
        self.save_settings()
        self.backup_manager.stop_auto_backup()
        self.root.destroy()
    
    def run(self):
        """Startar GUI-applikationen"""
        self.root.mainloop()

def main():
    """Huvudfunktion för komplett GUI"""
    app = CompleteExpenseManagerGUI()
    app.run()

if __name__ == "__main__":
    main()