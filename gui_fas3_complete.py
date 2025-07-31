#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Komplett GUI för utgiftshanteraren - Fas 3
Integrerar alla förbättringar från Fas 1, 2 och 3
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
from cloud_sync import CloudSyncManager, create_sync_widget, check_cloud_availability
from ai_recommendations import AIRecommendationEngine, create_ai_widget, check_ai_availability
from advanced_reporting import AdvancedReportingEngine, create_report_widget, check_reporting_availability

class CompleteExpenseManagerGUI:
    """Komplett GUI med alla förbättringar från Fas 1, 2 och 3"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Utgiftshanterare - Komplett version (Fas 3)")
        self.root.geometry("1800x1100")

        # Initiera alla moduler
        self.db = DatabaseManager()
        self.currency_converter = OfflineCurrencyConverter()  # Använd offline-version
        self.export_manager = ExportManager(self.db)
        self.statistics = ExpenseStatistics(self.db)
        self.backup_manager = BackupManager()
        self.cloud_sync = CloudSyncManager()
        self.ai_engine = AIRecommendationEngine(self.db)
        self.reporting_engine = AdvancedReportingEngine(self.db)

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

    def setup_gui(self):
        """Sätter upp GUI-komponenter"""
        # Huvudmeny
        self.create_menu()

        # Huvudram
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Vänster panel - Grupper och deltagare
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Grupper
        groups_frame = ttk.LabelFrame(left_panel, text="Grupper", padding=10)
        groups_frame.pack(fill=tk.X, pady=(0, 10))

        # Grupplista
        self.groups_tree = ttk.Treeview(groups_frame, columns=("name", "participants"), 
                                       show="tree headings", height=8)
        self.groups_tree.heading("#0", text="ID")
        self.groups_tree.heading("name", text="Namn")
        self.groups_tree.heading("participants", text="Deltagare")
        self.groups_tree.column("#0", width=50)
        self.groups_tree.column("name", width=150)
        self.groups_tree.column("participants", width=80)
        self.groups_tree.pack(fill=tk.X, pady=(0, 5))

        # Gruppknappar
        group_buttons = ttk.Frame(groups_frame)
        group_buttons.pack(fill=tk.X)
        ttk.Button(group_buttons, text="Ny grupp", command=self.add_group).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(group_buttons, text="Redigera", command=self.edit_group).pack(side=tk.LEFT, padx=5)
        ttk.Button(group_buttons, text="Ta bort", command=self.delete_group).pack(side=tk.LEFT, padx=5)

        # Deltagare
        participants_frame = ttk.LabelFrame(left_panel, text="Deltagare", padding=10)
        participants_frame.pack(fill=tk.X, pady=(0, 10))

        # Deltagarlista
        self.participants_tree = ttk.Treeview(participants_frame, columns=("name", "balance"), 
                                             show="tree headings", height=6)
        self.participants_tree.heading("#0", text="ID")
        self.participants_tree.heading("name", text="Namn")
        self.participants_tree.heading("balance", text="Saldo")
        self.participants_tree.column("#0", width=50)
        self.participants_tree.column("name", width=150)
        self.participants_tree.column("balance", width=80)
        self.participants_tree.pack(fill=tk.X, pady=(0, 5))

        # Deltagarknappar
        participant_buttons = ttk.Frame(participants_frame)
        participant_buttons.pack(fill=tk.X)
        ttk.Button(participant_buttons, text="Lägg till", command=self.add_participant).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(participant_buttons, text="Redigera", command=self.edit_participant).pack(side=tk.LEFT, padx=5)
        ttk.Button(participant_buttons, text="Ta bort", command=self.delete_participant).pack(side=tk.LEFT, padx=5)

        # Höger panel - Huvudinnehåll
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Notebook för flikar
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Flik 1: Utgifter
        self.expenses_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.expenses_frame, text="Utgifter")

        # Utgiftslista
        expenses_list_frame = ttk.Frame(self.expenses_frame)
        expenses_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Utgiftslista
        self.expenses_tree = ttk.Treeview(expenses_list_frame, 
                                         columns=("date", "description", "amount", "currency", 
                                                 "paid_by", "category"),
                                         show="tree headings", height=12)
        self.expenses_tree.heading("#0", text="ID")
        self.expenses_tree.heading("date", text="Datum")
        self.expenses_tree.heading("description", text="Beskrivning")
        self.expenses_tree.heading("amount", text="Belopp")
        self.expenses_tree.heading("currency", text="Valuta")
        self.expenses_tree.heading("paid_by", text="Betalad av")
        self.expenses_tree.heading("category", text="Kategori")
        self.expenses_tree.column("#0", width=50)
        self.expenses_tree.column("date", width=100)
        self.expenses_tree.column("description", width=200)
        self.expenses_tree.column("amount", width=100)
        self.expenses_tree.column("currency", width=80)
        self.expenses_tree.column("paid_by", width=120)
        self.expenses_tree.column("category", width=100)
        self.expenses_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Utgiftsknappar
        expense_buttons = ttk.Frame(expenses_list_frame)
        expense_buttons.pack(fill=tk.X)
        ttk.Button(expense_buttons, text="Lägg till utgift", command=self.add_expense).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(expense_buttons, text="Redigera", command=self.edit_expense).pack(side=tk.LEFT, padx=5)
        ttk.Button(expense_buttons, text="Ta bort", command=self.delete_expense).pack(side=tk.LEFT, padx=5)
        ttk.Button(expense_buttons, text="Visa saldon", command=self.show_balances).pack(side=tk.LEFT, padx=5)

        # Flik 2: Grafer (Fas 2)
        self.charts_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.charts_frame, text="Grafer")
        
        if check_matplotlib_availability():
            self.charts_widget = create_chart_widget(self.charts_frame, self.statistics)
        else:
            ttk.Label(self.charts_frame, text="Matplotlib krävs för grafer").pack(expand=True)

        # Flik 3: Backup (Fas 2)
        self.backup_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.backup_frame, text="Backup")
        
        if check_schedule_availability():
            self.backup_widget = BackupDialog(self.backup_frame, self.backup_manager)
        else:
            ttk.Label(self.backup_frame, text="Schedule-bibliotek krävs för backup").pack(expand=True)

        # Flik 4: Valuta (Fas 2)
        self.currency_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.currency_frame, text="Valuta")
        
        if check_offline_availability():
            self.currency_widget = create_currency_widget(self.currency_frame, self.currency_converter)
        else:
            ttk.Label(self.currency_frame, text="Offline-valuta stöd inte tillgängligt").pack(expand=True)

        # Flik 5: Cloud-synkronisering (Fas 3)
        self.sync_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sync_frame, text="Cloud-synk")
        
        if check_cloud_availability():
            self.sync_widget = create_sync_widget(self.sync_frame)
        else:
            ttk.Label(self.sync_frame, text="Cloud-synkronisering inte tillgänglig").pack(expand=True)

        # Flik 6: AI-rekommendationer (Fas 3)
        self.ai_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ai_frame, text="AI-rekommendationer")
        
        if check_ai_availability():
            self.ai_widget = create_ai_widget(self.ai_frame, self.ai_engine)
        else:
            ttk.Label(self.ai_frame, text="AI-funktioner kräver numpy").pack(expand=True)

        # Flik 7: Rapporter (Fas 3)
        self.reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_frame, text="Rapporter")
        
        if check_reporting_availability():
            self.reports_widget = create_report_widget(self.reports_frame, self.reporting_engine)
        else:
            ttk.Label(self.reports_frame, text="Rapportering kräver matplotlib och numpy").pack(expand=True)

        # Statusrad
        self.status_var = tk.StringVar(value="Redo")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_menu(self):
        """Skapar huvudmeny"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Arkiv-meny
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arkiv", menu=file_menu)
        file_menu.add_command(label="Ny grupp", command=self.add_group, accelerator="Ctrl+N")
        file_menu.add_command(label="Exportera data", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Avsluta", command=self.on_closing)

        # Redigera-meny
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Redigera", menu=edit_menu)
        edit_menu.add_command(label="Lägg till utgift", command=self.add_expense, accelerator="Ctrl+E")
        edit_menu.add_command(label="Lägg till deltagare", command=self.add_participant, accelerator="Ctrl+P")

        # Verktyg-meny
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Verktyg", menu=tools_menu)
        tools_menu.add_command(label="Visa saldon", command=self.show_balances)
        tools_menu.add_command(label="Backup-hantering", command=self.show_backup_dialog)
        tools_menu.add_command(label="Valutakonvertering", command=self.show_currency_dialog)
        tools_menu.add_separator()
        tools_menu.add_command(label="AI-rekommendationer", command=self.show_ai_recommendations)
        tools_menu.add_command(label="Avancerad rapportering", command=self.show_advanced_reports)
        tools_menu.add_command(label="Cloud-synkronisering", command=self.show_cloud_sync)

        # Inställningar-meny
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Inställningar", menu=settings_menu)
        settings_menu.add_command(label="Tema", command=self.toggle_theme)
        settings_menu.add_command(label="Spara inställningar", command=self.save_settings)

        # Hjälp-meny
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hjälp", menu=help_menu)
        help_menu.add_command(label="Om", command=self.show_about)

    def bind_events(self):
        """Bindar events"""
        # Gruppval
        self.groups_tree.bind("<<TreeviewSelect>>", self.on_group_selected)
        
        # Dubbelklick för redigering
        self.participants_tree.bind("<Double-1>", self.edit_participant)
        self.expenses_tree.bind("<Double-1>", self.edit_expense)
        
        # Tangentbordskort
        self.root.bind("<Control-n>", lambda e: self.add_group())
        self.root.bind("<Control-e>", lambda e: self.add_expense())
        self.root.bind("<Control-p>", lambda e: self.add_participant())
        
        # Stängning
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_groups(self):
        """Laddar grupper"""
        try:
            groups = self.db.get_groups()
            self.groups_tree.delete(*self.groups_tree.get_children())
            
            for group in groups:
                participants = self.db.get_participants(group['id'])
                self.groups_tree.insert("", "end", text=str(group['id']), 
                                      values=(group['name'], len(participants)))
        except Exception as e:
            self.show_error(f"Fel vid laddning av grupper: {e}")

    def on_group_selected(self, event):
        """Hanterar gruppval"""
        selection = self.groups_tree.selection()
        if selection:
            group_id = int(self.groups_tree.item(selection[0])["text"])
            self.current_group_id = group_id
            self.current_group_name = self.groups_tree.item(selection[0])["values"][0]
            self.load_participants()
            self.load_expenses()
            self.update_status(f"Vald grupp: {self.current_group_name}")
            
            # Uppdatera AI-rekommendationer om tillgängligt
            if hasattr(self, 'ai_widget') and check_ai_availability():
                self.ai_widget.set_group(group_id)
            
            # Uppdatera rapporter om tillgängligt
            if hasattr(self, 'reports_widget') and check_reporting_availability():
                self.reports_widget.set_group(group_id)

    def load_participants(self):
        """Laddar deltagare för vald grupp"""
        if not self.current_group_id:
            return
        
        try:
            participants = self.db.get_participants(self.current_group_id)
            balances = self.db.get_participant_balances(self.current_group_id)
            
            self.participants_tree.delete(*self.participants_tree.get_children())
            
            for participant in participants:
                balance = next((bal['balance'] for bal in balances if bal['name'] == participant['name']), 0)
                self.participants_tree.insert("", "end", text=str(participant['id']), 
                                           values=(participant['name'], f"{balance:.0f} kr"))
        except Exception as e:
            self.show_error(f"Fel vid laddning av deltagare: {e}")

    def load_expenses(self):
        """Laddar utgifter för vald grupp"""
        if not self.current_group_id:
            return
        
        try:
            expenses = self.db.get_expenses(self.current_group_id)
            
            self.expenses_tree.delete(*self.expenses_tree.get_children())
            
            for expense in expenses:
                self.expenses_tree.insert("", "end", text=str(expense['id']), 
                                       values=(expense['date'][:10], expense['description'], 
                                              f"{expense['amount']:.0f}", expense['currency'],
                                              expense['paid_by'], expense['category'] or 'Okategoriserad'))
        except Exception as e:
            self.show_error(f"Fel vid laddning av utgifter: {e}")

    def add_group(self):
        """Lägger till ny grupp"""
        dialog = GroupDialog(self.root, "Lägg till grupp")
        if dialog.result:
            try:
                group_id = self.db.add_group(dialog.result)
                self.load_groups()
                self.update_status(f"Grupp '{dialog.result}' tillagd")
            except Exception as e:
                self.show_error(f"Fel vid tillägg av grupp: {e}")

    def edit_group(self):
        """Redigerar vald grupp"""
        selection = self.groups_tree.selection()
        if not selection:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        group_id = int(self.groups_tree.item(selection[0])["text"])
        current_name = self.groups_tree.item(selection[0])["values"][0]
        
        dialog = GroupDialog(self.root, "Redigera grupp", current_name)
        if dialog.result:
            try:
                self.db.update_group(group_id, dialog.result)
                self.load_groups()
                self.update_status(f"Grupp uppdaterad till '{dialog.result}'")
            except Exception as e:
                self.show_error(f"Fel vid uppdatering av grupp: {e}")

    def delete_group(self):
        """Tar bort vald grupp"""
        selection = self.groups_tree.selection()
        if not selection:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        group_id = int(self.groups_tree.item(selection[0])["text"])
        group_name = self.groups_tree.item(selection[0])["values"][0]
        
        if messagebox.askyesno("Bekräfta", f"Är du säker på att ta bort gruppen '{group_name}'?"):
            try:
                self.db.delete_group(group_id)
                self.load_groups()
                self.update_status(f"Grupp '{group_name}' borttagen")
            except Exception as e:
                self.show_error(f"Fel vid borttagning av grupp: {e}")

    def add_participant(self):
        """Lägger till ny deltagare"""
        if not self.current_group_id:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        dialog = ParticipantDialog(self.root, "Lägg till deltagare")
        if dialog.result:
            try:
                self.db.add_participant(self.current_group_id, dialog.result)
                self.load_participants()
                self.update_status(f"Deltagare '{dialog.result}' tillagd")
            except Exception as e:
                self.show_error(f"Fel vid tillägg av deltagare: {e}")

    def edit_participant(self, event=None):
        """Redigerar vald deltagare"""
        selection = self.participants_tree.selection()
        if not selection:
            messagebox.showwarning("Varning", "Välj en deltagare först")
            return
        
        participant_id = int(self.participants_tree.item(selection[0])["text"])
        current_name = self.participants_tree.item(selection[0])["values"][0]
        
        dialog = ParticipantDialog(self.root, "Redigera deltagare", current_name)
        if dialog.result:
            try:
                self.db.update_participant(participant_id, dialog.result)
                self.load_participants()
                self.update_status(f"Deltagare uppdaterad till '{dialog.result}'")
            except Exception as e:
                self.show_error(f"Fel vid uppdatering av deltagare: {e}")

    def delete_participant(self):
        """Tar bort vald deltagare"""
        selection = self.participants_tree.selection()
        if not selection:
            messagebox.showwarning("Varning", "Välj en deltagare först")
            return
        
        participant_id = int(self.participants_tree.item(selection[0])["text"])
        participant_name = self.participants_tree.item(selection[0])["values"][0]
        
        if messagebox.askyesno("Bekräfta", f"Är du säker på att ta bort deltagaren '{participant_name}'?"):
            try:
                self.db.delete_participant(participant_id)
                self.load_participants()
                self.update_status(f"Deltagare '{participant_name}' borttagen")
            except Exception as e:
                self.show_error(f"Fel vid borttagning av deltagare: {e}")

    def add_expense(self):
        """Lägger till ny utgift"""
        if not self.current_group_id:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        participants = self.db.get_participants(self.current_group_id)
        if not participants:
            messagebox.showwarning("Varning", "Lägg till deltagare först")
            return
        
        dialog = ExpenseDialog(self.root, "Lägg till utgift", participants, self.currency_converter)
        if dialog.result:
            try:
                expense_data = dialog.result
                expense_id = self.db.add_expense(self.current_group_id, expense_data)
                
                # Lägg till för cloud-synkronisering
                if hasattr(self, 'cloud_sync'):
                    self.cloud_sync.add_sync_item("expenses", expense_id, expense_data)
                
                self.load_expenses()
                self.update_status(f"Utgift '{expense_data['description']}' tillagd")
            except Exception as e:
                self.show_error(f"Fel vid tillägg av utgift: {e}")

    def edit_expense(self, event=None):
        """Redigerar vald utgift"""
        selection = self.expenses_tree.selection()
        if not selection:
            messagebox.showwarning("Varning", "Välj en utgift först")
            return
        
        expense_id = int(self.expenses_tree.item(selection[0])["text"])
        participants = self.db.get_participants(self.current_group_id)
        
        # Hämta aktuell utgift
        expenses = self.db.get_expenses(self.current_group_id)
        current_expense = next((exp for exp in expenses if exp['id'] == expense_id), None)
        
        if current_expense:
            dialog = ExpenseDialog(self.root, "Redigera utgift", participants, 
                                 self.currency_converter, current_expense)
            if dialog.result:
                try:
                    self.db.update_expense(expense_id, dialog.result)
                    self.load_expenses()
                    self.update_status(f"Utgift uppdaterad")
                except Exception as e:
                    self.show_error(f"Fel vid uppdatering av utgift: {e}")

    def delete_expense(self):
        """Tar bort vald utgift"""
        selection = self.expenses_tree.selection()
        if not selection:
            messagebox.showwarning("Varning", "Välj en utgift först")
            return
        
        expense_id = int(self.expenses_tree.item(selection[0])["text"])
        expense_desc = self.expenses_tree.item(selection[0])["values"][1]
        
        if messagebox.askyesno("Bekräfta", f"Är du säker på att ta bort utgiften '{expense_desc}'?"):
            try:
                self.db.delete_expense(expense_id)
                self.load_expenses()
                self.update_status(f"Utgift '{expense_desc}' borttagen")
            except Exception as e:
                self.show_error(f"Fel vid borttagning av utgift: {e}")

    def show_balances(self):
        """Visar saldon för vald grupp"""
        if not self.current_group_id:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        try:
            balances = self.db.get_participant_balances(self.current_group_id)
            
            balance_text = f"Saldon för grupp: {self.current_group_name}\n\n"
            for balance in balances:
                balance_text += f"{balance['name']}: {balance['balance']:.0f} kr\n"
            
            messagebox.showinfo("Saldon", balance_text)
        except Exception as e:
            self.show_error(f"Fel vid hämtning av saldon: {e}")

    def export_data(self):
        """Exporterar data"""
        if not self.current_group_id:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                if filename.endswith('.xlsx'):
                    self.export_manager.export_to_excel(self.current_group_id, filename)
                elif filename.endswith('.csv'):
                    self.export_manager.export_to_csv(self.current_group_id, filename)
                
                self.update_status(f"Data exporterad till {filename}")
        except Exception as e:
            self.show_error(f"Fel vid export: {e}")

    def show_backup_dialog(self):
        """Visar backup-dialog"""
        if hasattr(self, 'backup_widget'):
            self.backup_widget.show_dialog()

    def show_currency_dialog(self):
        """Visar valutadialog"""
        if hasattr(self, 'currency_widget'):
            # Implementera valutadialog här
            pass

    def show_ai_recommendations(self):
        """Visar AI-rekommendationer"""
        if hasattr(self, 'ai_widget') and check_ai_availability():
            self.notebook.select(5)  # Växla till AI-fliken
        else:
            messagebox.showinfo("Info", "AI-funktioner kräver numpy")

    def show_advanced_reports(self):
        """Visar avancerade rapporter"""
        if hasattr(self, 'reports_widget') and check_reporting_availability():
            self.notebook.select(6)  # Växla till rapporter-fliken
        else:
            messagebox.showinfo("Info", "Rapportering kräver matplotlib och numpy")

    def show_cloud_sync(self):
        """Visar cloud-synkronisering"""
        if hasattr(self, 'sync_widget') and check_cloud_availability():
            self.notebook.select(4)  # Växla till cloud-sync-fliken
        else:
            messagebox.showinfo("Info", "Cloud-synkronisering inte tillgänglig")

    def toggle_theme(self):
        """Växlar tema"""
        self.current_theme = Theme.DARK if self.current_theme == Theme.LIGHT else Theme.LIGHT
        self.apply_theme()
        self.save_settings()

    def apply_theme(self):
        """Applicerar tema"""
        if self.current_theme == Theme.DARK:
            self.root.configure(bg='#2b2b2b')
            style = ttk.Style()
            style.theme_use('clam')
            style.configure('TLabel', background='#2b2b2b', foreground='white')
            style.configure('TFrame', background='#2b2b2b')
        else:
            self.root.configure(bg='#f0f0f0')
            style = ttk.Style()
            style.theme_use('clam')
            style.configure('TLabel', background='#f0f0f0', foreground='black')
            style.configure('TFrame', background='#f0f0f0')

    def load_settings(self):
        """Laddar inställningar"""
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    self.current_theme = Theme(settings.get("theme", "light"))
        except Exception as e:
            print(f"Fel vid laddning av inställningar: {e}")

    def save_settings(self):
        """Sparar inställningar"""
        try:
            settings = {
                "theme": self.current_theme.value,
                "last_saved": datetime.now().isoformat()
            }
            with open("settings.json", "w") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Fel vid sparande av inställningar: {e}")

    def update_status(self, message: str):
        """Uppdaterar statusrad"""
        self.status_var.set(message)

    def show_error(self, message: str):
        """Visar felmeddelande"""
        messagebox.showerror("Fel", message)

    def show_about(self):
        """Visar om-dialog"""
        about_text = """
Utgiftshanterare - Komplett version (Fas 3)

En avancerad applikation för att hantera utgifter och splitta dem mellan gruppdeltagare.

Funktioner:
• Grupp- och deltagarhantering
• Utgiftsregistrering med kategorisering
• Valutakonvertering med offline-stöd
• Export till Excel, PDF och CSV
• Statistik och grafer
• Schemalagd backup
• Cloud-synkronisering
• AI-baserade rekommendationer
• Avancerad rapportering

Version: 3.0
        """
        messagebox.showinfo("Om", about_text)

    def on_closing(self):
        """Hanterar stängning av applikationen"""
        try:
            # Stoppa automatisk backup
            if hasattr(self, 'backup_manager'):
                self.backup_manager.stop_auto_sync()
            
            # Stoppa cloud-synkronisering
            if hasattr(self, 'cloud_sync'):
                self.cloud_sync.stop_auto_sync()
            
            self.save_settings()
            self.root.destroy()
        except Exception as e:
            print(f"Fel vid stängning: {e}")
            self.root.destroy()

    def run(self):
        """Startar applikationen"""
        self.root.mainloop()

# Dialog-klasser
class GroupDialog:
    def __init__(self, parent, title, current_name=""):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("300x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrera dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Innehåll
        ttk.Label(self.dialog, text="Gruppnamn:").pack(pady=10)
        
        self.name_var = tk.StringVar(value=current_name)
        self.name_entry = ttk.Entry(self.dialog, textvariable=self.name_var, width=30)
        self.name_entry.pack(pady=5)
        self.name_entry.focus()
        
        # Knappar
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Avbryt", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter-tangent
        self.dialog.bind("<Return>", lambda e: self.ok_clicked())
        self.dialog.bind("<Escape>", lambda e: self.cancel_clicked())
        
        # Vänta på dialog
        self.dialog.wait_window()

    def ok_clicked(self):
        """Hanterar OK-klick"""
        name = self.name_var.get().strip()
        if name:
            self.result = name
            self.dialog.destroy()
        else:
            messagebox.showwarning("Varning", "Ange ett gruppnamn")

    def cancel_clicked(self):
        """Hanterar Avbryt-klick"""
        self.dialog.destroy()

class ParticipantDialog:
    def __init__(self, parent, title, current_name=""):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("300x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrera dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Innehåll
        ttk.Label(self.dialog, text="Deltagarnamn:").pack(pady=10)
        
        self.name_var = tk.StringVar(value=current_name)
        self.name_entry = ttk.Entry(self.dialog, textvariable=self.name_var, width=30)
        self.name_entry.pack(pady=5)
        self.name_entry.focus()
        
        # Knappar
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Avbryt", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter-tangent
        self.dialog.bind("<Return>", lambda e: self.ok_clicked())
        self.dialog.bind("<Escape>", lambda e: self.cancel_clicked())
        
        # Vänta på dialog
        self.dialog.wait_window()

    def ok_clicked(self):
        """Hanterar OK-klick"""
        name = self.name_var.get().strip()
        if name:
            self.result = name
            self.dialog.destroy()
        else:
            messagebox.showwarning("Varning", "Ange ett namn")

    def cancel_clicked(self):
        """Hanterar Avbryt-klick"""
        self.dialog.destroy()

class ExpenseDialog:
    def __init__(self, parent, title, participants, currency_converter, current_expense=None):
        self.result = None
        self.participants = participants
        self.currency_converter = currency_converter
        self.current_expense = current_expense
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrera dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Skapa formulär
        self.create_form()
        
        # Fyll i data om redigering
        if current_expense:
            self.fill_form(current_expense)
        
        # Vänta på dialog
        self.dialog.wait_window()

    def create_form(self):
        """Skapar formulär"""
        # Beskrivning
        ttk.Label(self.dialog, text="Beskrivning:").pack(pady=(10, 0))
        self.description_var = tk.StringVar()
        self.description_entry = ttk.Entry(self.dialog, textvariable=self.description_var, width=50)
        self.description_entry.pack(pady=5)
        
        # Belopp
        ttk.Label(self.dialog, text="Belopp:").pack(pady=(10, 0))
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(self.dialog, textvariable=self.amount_var, width=20)
        self.amount_entry.pack(pady=5)
        
        # Valuta
        ttk.Label(self.dialog, text="Valuta:").pack(pady=(10, 0))
        self.currency_var = tk.StringVar(value="SEK")
        currency_combo = ttk.Combobox(self.dialog, textvariable=self.currency_var, 
                                     values=["SEK", "USD", "EUR", "GBP"], width=10)
        currency_combo.pack(pady=5)
        
        # Kategori
        ttk.Label(self.dialog, text="Kategori:").pack(pady=(10, 0))
        self.category_var = tk.StringVar()
        category_combo = ttk.Combobox(self.dialog, textvariable=self.category_var,
                                     values=["Mat", "Transport", "Underhållning", "Shopping", "Övrigt"], width=20)
        category_combo.pack(pady=5)
        
        # Betald av
        ttk.Label(self.dialog, text="Betald av:").pack(pady=(10, 0))
        self.paid_by_var = tk.StringVar()
        paid_by_combo = ttk.Combobox(self.dialog, textvariable=self.paid_by_var,
                                     values=[p['name'] for p in self.participants], width=20)
        paid_by_combo.pack(pady=5)
        
        # Deltagare
        ttk.Label(self.dialog, text="Deltagare:").pack(pady=(10, 0))
        self.participants_frame = ttk.Frame(self.dialog)
        self.participants_frame.pack(pady=5)
        
        self.participant_vars = {}
        for participant in self.participants:
            var = tk.BooleanVar(value=True)
            self.participant_vars[participant['name']] = var
            ttk.Checkbutton(self.participants_frame, text=participant['name'], 
                           variable=var).pack(anchor=tk.W)
        
        # Knappar
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Avbryt", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)

    def fill_form(self, expense):
        """Fyller formuläret med befintlig data"""
        self.description_var.set(expense.get('description', ''))
        self.amount_var.set(str(expense.get('amount', '')))
        self.currency_var.set(expense.get('currency', 'SEK'))
        self.category_var.set(expense.get('category', ''))
        self.paid_by_var.set(expense.get('paid_by', ''))
        
        # Fyll i deltagare
        splits = expense.get('splits', [])
        for participant_name, var in self.participant_vars.items():
            var.set(any(split['participant'] == participant_name for split in splits))

    def ok_clicked(self):
        """Hanterar OK-klick"""
        try:
            description = self.description_var.get().strip()
            amount = float(self.amount_var.get())
            currency = self.currency_var.get()
            category = self.category_var.get()
            paid_by = self.paid_by_var.get()
            
            if not all([description, amount > 0, paid_by]):
                messagebox.showwarning("Varning", "Fyll i alla obligatoriska fält")
                return
            
            # Samla deltagare
            selected_participants = [name for name, var in self.participant_vars.items() if var.get()]
            
            if not selected_participants:
                messagebox.showwarning("Varning", "Välj minst en deltagare")
                return
            
            # Skapa splits
            split_amount = amount / len(selected_participants)
            splits = [{"participant": name, "amount": split_amount} for name in selected_participants]
            
            self.result = {
                "description": description,
                "amount": amount,
                "currency": currency,
                "category": category,
                "paid_by": paid_by,
                "splits": splits,
                "date": datetime.now().isoformat()
            }
            
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Fel", "Ange ett giltigt belopp")

    def cancel_clicked(self):
        """Hanterar Avbryt-klick"""
        self.dialog.destroy()

# Hjälpfunktioner
def check_cloud_availability() -> bool:
    """Kontrollerar om cloud-funktioner är tillgängliga"""
    try:
        import requests
        return True
    except ImportError:
        return False

def check_ai_availability() -> bool:
    """Kontrollerar om AI-funktioner är tillgängliga"""
    try:
        import numpy
        return True
    except ImportError:
        return False

def check_reporting_availability() -> bool:
    """Kontrollerar om rapporteringsfunktioner är tillgängliga"""
    try:
        import matplotlib
        import numpy
        return True
    except ImportError:
        return False

if __name__ == "__main__":
    app = CompleteExpenseManagerGUI()
    app.run()