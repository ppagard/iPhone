#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schemalagd säkerhetskopiering för utgiftshanteraren
Automatisk backup och återställning
"""

import os
import shutil
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import time
import schedule
import zipfile
import hashlib

class BackupManager:
    """Hanterar schemalagd säkerhetskopiering"""
    
    def __init__(self, database_path: str = "expense_manager.db"):
        self.database_path = database_path
        self.backup_dir = "backups"
        self.backup_config_file = "backup_config.json"
        self.setup_backup_directory()
        self.load_config()
        self.backup_thread = None
        self.is_running = False
    
    def setup_backup_directory(self):
        """Skapar backup-katalog om den inte finns"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def load_config(self):
        """Laddar backup-konfiguration"""
        self.config = {
            'auto_backup': True,
            'backup_interval_hours': 24,
            'max_backups': 10,
            'backup_on_startup': True,
            'compress_backups': True,
            'backup_settings': True,
            'backup_logs': True
        }
        
        try:
            if os.path.exists(self.backup_config_file):
                with open(self.backup_config_file, 'r') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
        except Exception as e:
            print(f"Kunde inte ladda backup-konfiguration: {e}")
    
    def save_config(self):
        """Sparar backup-konfiguration"""
        try:
            with open(self.backup_config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Kunde inte spara backup-konfiguration: {e}")
    
    def create_backup(self, backup_name: str = None) -> str:
        """Skapar en säkerhetskopia"""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
        
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            # Skapa backup-katalog
            os.makedirs(backup_path, exist_ok=True)
            
            # Kopiera databas
            if os.path.exists(self.database_path):
                db_backup_path = os.path.join(backup_path, "expense_manager.db")
                shutil.copy2(self.database_path, db_backup_path)
            
            # Kopiera inställningar
            if self.config['backup_settings']:
                settings_files = ['settings.json', 'currency_cache.json']
                for settings_file in settings_files:
                    if os.path.exists(settings_file):
                        shutil.copy2(settings_file, os.path.join(backup_path, settings_file))
            
            # Kopiera loggar
            if self.config['backup_logs']:
                log_files = ['error_log.txt', 'detailed_error_log.json']
                for log_file in log_files:
                    if os.path.exists(log_file):
                        shutil.copy2(log_file, os.path.join(backup_path, log_file))
            
            # Skapa backup-metadata
            metadata = {
                'backup_name': backup_name,
                'created_at': datetime.now().isoformat(),
                'database_size': os.path.getsize(self.database_path) if os.path.exists(self.database_path) else 0,
                'config': self.config
            }
            
            with open(os.path.join(backup_path, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Komprimera backup om aktiverat
            if self.config['compress_backups']:
                self.compress_backup(backup_path)
                backup_path += '.zip'
            
            print(f"Säkerhetskopia skapad: {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"Fel vid skapande av säkerhetskopia: {e}")
            return None
    
    def compress_backup(self, backup_path: str):
        """Komprimerar backup-katalog"""
        try:
            zip_path = backup_path + '.zip'
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_path)
                        zipf.write(file_path, arcname)
            
            # Ta bort den okomprimerade katalogen
            shutil.rmtree(backup_path)
            
        except Exception as e:
            print(f"Fel vid komprimering av backup: {e}")
    
    def extract_backup(self, backup_path: str) -> str:
        """Extraherar komprimerad backup"""
        try:
            if backup_path.endswith('.zip'):
                extract_path = backup_path[:-4]
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(extract_path)
                return extract_path
            else:
                return backup_path
        except Exception as e:
            print(f"Fel vid extrahering av backup: {e}")
            return None
    
    def restore_backup(self, backup_path: str) -> bool:
        """Återställer från säkerhetskopia"""
        try:
            # Extrahera backup om den är komprimerad
            if backup_path.endswith('.zip'):
                backup_path = self.extract_backup(backup_path)
            
            if not backup_path or not os.path.exists(backup_path):
                print("Backup-katalog hittades inte")
                return False
            
            # Skapa backup av nuvarande databas
            current_backup = f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.create_backup(current_backup)
            
            # Återställ databas
            db_backup_path = os.path.join(backup_path, "expense_manager.db")
            if os.path.exists(db_backup_path):
                shutil.copy2(db_backup_path, self.database_path)
            
            # Återställ inställningar
            settings_files = ['settings.json', 'currency_cache.json']
            for settings_file in settings_files:
                settings_backup_path = os.path.join(backup_path, settings_file)
                if os.path.exists(settings_backup_path):
                    shutil.copy2(settings_backup_path, settings_file)
            
            print(f"Backup återställd från: {backup_path}")
            return True
            
        except Exception as e:
            print(f"Fel vid återställning av backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """Listar alla tillgängliga säkerhetskopior"""
        backups = []
        
        try:
            for item in os.listdir(self.backup_dir):
                item_path = os.path.join(self.backup_dir, item)
                
                if os.path.isdir(item_path):
                    # Okomprimerad backup
                    metadata_path = os.path.join(item_path, 'metadata.json')
                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            backups.append({
                                'name': item,
                                'path': item_path,
                                'type': 'directory',
                                'metadata': metadata
                            })
                
                elif item.endswith('.zip'):
                    # Komprimerad backup
                    try:
                        with zipfile.ZipFile(item_path, 'r') as zipf:
                            metadata_file = None
                            for file in zipf.namelist():
                                if file.endswith('metadata.json'):
                                    metadata_file = file
                                    break
                            
                            if metadata_file:
                                with zipf.open(metadata_file) as f:
                                    metadata = json.load(f)
                                    backups.append({
                                        'name': item,
                                        'path': item_path,
                                        'type': 'compressed',
                                        'metadata': metadata
                                    })
                    except Exception as e:
                        print(f"Fel vid läsning av komprimerad backup {item}: {e}")
        
        except Exception as e:
            print(f"Fel vid listning av backups: {e}")
        
        # Sortera efter skapandedatum
        backups.sort(key=lambda x: x['metadata']['created_at'], reverse=True)
        return backups
    
    def cleanup_old_backups(self):
        """Rensar gamla säkerhetskopior"""
        backups = self.list_backups()
        
        if len(backups) > self.config['max_backups']:
            backups_to_delete = backups[self.config['max_backups']:]
            
            for backup in backups_to_delete:
                try:
                    if os.path.isdir(backup['path']):
                        shutil.rmtree(backup['path'])
                    else:
                        os.remove(backup['path'])
                    print(f"Tog bort gammal backup: {backup['name']}")
                except Exception as e:
                    print(f"Fel vid borttagning av backup {backup['name']}: {e}")
    
    def verify_backup(self, backup_path: str) -> bool:
        """Verifierar att en backup är intakt"""
        try:
            if backup_path.endswith('.zip'):
                backup_path = self.extract_backup(backup_path)
            
            if not backup_path or not os.path.exists(backup_path):
                return False
            
            # Kontrollera att databasen finns
            db_path = os.path.join(backup_path, "expense_manager.db")
            if not os.path.exists(db_path):
                return False
            
            # Kontrollera att databasen är giltig
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                conn.close()
                
                required_tables = ['groups', 'participants', 'expenses', 'expense_splits']
                existing_tables = [table[0] for table in tables]
                
                return all(table in existing_tables for table in required_tables)
                
            except Exception:
                return False
                
        except Exception:
            return False
    
    def start_auto_backup(self):
        """Startar automatisk säkerhetskopiering"""
        if not self.config['auto_backup']:
            return
        
        self.is_running = True
        
        # Schemalägg backup
        schedule.every(self.config['backup_interval_hours']).hours.do(self.auto_backup_job)
        
        # Starta backup-tråd
        self.backup_thread = threading.Thread(target=self.backup_scheduler_loop, daemon=True)
        self.backup_thread.start()
        
        print(f"Automatisk säkerhetskopiering startad (var {self.config['backup_interval_hours']} timme)")
    
    def stop_auto_backup(self):
        """Stoppar automatisk säkerhetskopiering"""
        self.is_running = False
        schedule.clear()
        print("Automatisk säkerhetskopiering stoppad")
    
    def backup_scheduler_loop(self):
        """Huvudloop för backup-schemaläggare"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Kontrollera varje minut
    
    def auto_backup_job(self):
        """Automatisk backup-jobb"""
        try:
            print("Kör automatisk säkerhetskopiering...")
            backup_path = self.create_backup()
            
            if backup_path:
                self.cleanup_old_backups()
                print("Automatisk säkerhetskopiering slutförd")
            else:
                print("Automatisk säkerhetskopiering misslyckades")
                
        except Exception as e:
            print(f"Fel vid automatisk säkerhetskopiering: {e}")
    
    def get_backup_stats(self) -> Dict:
        """Returnerar statistik för säkerhetskopior"""
        backups = self.list_backups()
        
        total_size = 0
        for backup in backups:
            try:
                total_size += os.path.getsize(backup['path'])
            except:
                pass
        
        return {
            'total_backups': len(backups),
            'total_size_mb': total_size / (1024 * 1024),
            'oldest_backup': backups[-1]['metadata']['created_at'] if backups else None,
            'newest_backup': backups[0]['metadata']['created_at'] if backups else None,
            'auto_backup_enabled': self.config['auto_backup'],
            'backup_interval_hours': self.config['backup_interval_hours']
        }

class BackupDialog:
    """Dialog för backup-hantering"""
    
    def __init__(self, parent, backup_manager):
        self.parent = parent
        self.backup_manager = backup_manager
        self.dialog = None
    
    def show_backup_dialog(self):
        """Visar backup-hanteringsdialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Säkerhetskopiering")
        self.dialog.geometry("600x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Skapa notebook för olika flikar
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Flik 1: Skapa backup
        self.setup_create_backup_tab(notebook)
        
        # Flik 2: Återställ backup
        self.setup_restore_backup_tab(notebook)
        
        # Flik 3: Backup-lista
        self.setup_backup_list_tab(notebook)
        
        # Flik 4: Inställningar
        self.setup_settings_tab(notebook)
    
    def setup_create_backup_tab(self, notebook):
        """Sätter upp flik för att skapa backup"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Skapa backup")
        
        # Kontrollpanel
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="Skapa backup nu", 
                  command=self.create_backup_now).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Verifiera senaste backup", 
                  command=self.verify_latest_backup).pack(side=tk.LEFT, padx=5)
        
        # Statistik
        stats_frame = ttk.LabelFrame(frame, text="Backup-statistik", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.stats_text = tk.Text(stats_frame, height=8, wrap=tk.WORD)
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.update_backup_stats()
    
    def setup_restore_backup_tab(self, notebook):
        """Sätter upp flik för att återställa backup"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Återställ backup")
        
        # Backup-lista
        list_frame = ttk.LabelFrame(frame, text="Tillgängliga backups", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview för backups
        columns = ('Namn', 'Datum', 'Storlek', 'Typ', 'Status')
        self.backup_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.backup_tree.heading(col, text=col)
            self.backup_tree.column(col, width=120)
        
        # Scrollbar
        backup_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=backup_scrollbar.set)
        
        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        backup_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Knappar
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Återställ vald backup", 
                  command=self.restore_selected_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Verifiera vald backup", 
                  command=self.verify_selected_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Uppdatera lista", 
                  command=self.refresh_backup_list).pack(side=tk.LEFT, padx=5)
        
        self.refresh_backup_list()
    
    def setup_backup_list_tab(self, notebook):
        """Sätter upp flik för backup-lista"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Backup-lista")
        
        # Detaljerad lista
        self.backup_list_text = tk.Text(frame, wrap=tk.WORD)
        list_scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.backup_list_text.yview)
        self.backup_list_text.configure(yscrollcommand=list_scrollbar.set)
        
        self.backup_list_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        self.update_backup_list()
    
    def setup_settings_tab(self, notebook):
        """Sätter upp flik för inställningar"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Inställningar")
        
        # Inställningar
        settings_frame = ttk.LabelFrame(frame, text="Backup-inställningar", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Auto-backup
        self.auto_backup_var = tk.BooleanVar(value=self.backup_manager.config['auto_backup'])
        ttk.Checkbutton(settings_frame, text="Aktivera automatisk backup", 
                       variable=self.auto_backup_var).pack(anchor=tk.W, pady=2)
        
        # Backup-intervall
        ttk.Label(settings_frame, text="Backup-intervall (timmar):").pack(anchor=tk.W, pady=(10, 2))
        self.interval_var = tk.StringVar(value=str(self.backup_manager.config['backup_interval_hours']))
        ttk.Entry(settings_frame, textvariable=self.interval_var, width=10).pack(anchor=tk.W)
        
        # Max backups
        ttk.Label(settings_frame, text="Max antal backups:").pack(anchor=tk.W, pady=(10, 2))
        self.max_backups_var = tk.StringVar(value=str(self.backup_manager.config['max_backups']))
        ttk.Entry(settings_frame, textvariable=self.max_backups_var, width=10).pack(anchor=tk.W)
        
        # Komprimering
        self.compress_var = tk.BooleanVar(value=self.backup_manager.config['compress_backups'])
        ttk.Checkbutton(settings_frame, text="Komprimera backups", 
                       variable=self.compress_var).pack(anchor=tk.W, pady=(10, 2))
        
        # Spara inställningar
        ttk.Button(settings_frame, text="Spara inställningar", 
                  command=self.save_backup_settings).pack(pady=10)
    
    def create_backup_now(self):
        """Skapar backup nu"""
        try:
            backup_path = self.backup_manager.create_backup()
            if backup_path:
                messagebox.showinfo("Framgång", f"Backup skapad: {backup_path}")
                self.update_backup_stats()
                self.refresh_backup_list()
            else:
                messagebox.showerror("Fel", "Kunde inte skapa backup")
        except Exception as e:
            messagebox.showerror("Fel", f"Fel vid skapande av backup: {e}")
    
    def verify_latest_backup(self):
        """Verifierar senaste backup"""
        backups = self.backup_manager.list_backups()
        if backups:
            latest_backup = backups[0]
            is_valid = self.backup_manager.verify_backup(latest_backup['path'])
            if is_valid:
                messagebox.showinfo("Verifiering", "Senaste backup är giltig")
            else:
                messagebox.showerror("Verifiering", "Senaste backup är korrupt")
        else:
            messagebox.showwarning("Verifiering", "Inga backups hittades")
    
    def restore_selected_backup(self):
        """Återställer vald backup"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("Varning", "Välj en backup först")
            return
        
        item = self.backup_tree.item(selection[0])
        backup_name = item['values'][0]
        
        if messagebox.askyesno("Bekräfta", f"Är du säker på att du vill återställa från {backup_name}?"):
            try:
                # Hitta backup-sökväg
                backups = self.backup_manager.list_backups()
                backup = next((b for b in backups if b['name'] == backup_name), None)
                
                if backup:
                    success = self.backup_manager.restore_backup(backup['path'])
                    if success:
                        messagebox.showinfo("Framgång", f"Backup återställd från {backup_name}")
                    else:
                        messagebox.showerror("Fel", "Kunde inte återställa backup")
                else:
                    messagebox.showerror("Fel", "Backup hittades inte")
            except Exception as e:
                messagebox.showerror("Fel", f"Fel vid återställning: {e}")
    
    def verify_selected_backup(self):
        """Verifierar vald backup"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("Varning", "Välj en backup först")
            return
        
        item = self.backup_tree.item(selection[0])
        backup_name = item['values'][0]
        
        try:
            backups = self.backup_manager.list_backups()
            backup = next((b for b in backups if b['name'] == backup_name), None)
            
            if backup:
                is_valid = self.backup_manager.verify_backup(backup['path'])
                if is_valid:
                    messagebox.showinfo("Verifiering", f"Backup {backup_name} är giltig")
                else:
                    messagebox.showerror("Verifiering", f"Backup {backup_name} är korrupt")
            else:
                messagebox.showerror("Fel", "Backup hittades inte")
        except Exception as e:
            messagebox.showerror("Fel", f"Fel vid verifiering: {e}")
    
    def refresh_backup_list(self):
        """Uppdaterar backup-listan"""
        # Rensa lista
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        # Ladda backups
        backups = self.backup_manager.list_backups()
        for backup in backups:
            try:
                size_mb = os.path.getsize(backup['path']) / (1024 * 1024)
                backup_type = "Komprimerad" if backup['type'] == 'compressed' else "Okomprimerad"
                
                self.backup_tree.insert('', 'end', values=(
                    backup['name'],
                    backup['metadata']['created_at'][:19],
                    f"{size_mb:.1f} MB",
                    backup_type,
                    "Giltig" if self.backup_manager.verify_backup(backup['path']) else "Korrupt"
                ))
            except Exception as e:
                print(f"Fel vid laddning av backup {backup['name']}: {e}")
    
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
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
    
    def update_backup_list(self):
        """Uppdaterar backup-listan i textform"""
        backups = self.backup_manager.list_backups()
        
        list_text = "Backup-lista:\n" + "="*50 + "\n\n"
        
        for backup in backups:
            try:
                size_mb = os.path.getsize(backup['path']) / (1024 * 1024)
                is_valid = self.backup_manager.verify_backup(backup['path'])
                
                list_text += f"Namn: {backup['name']}\n"
                list_text += f"Datum: {backup['metadata']['created_at']}\n"
                list_text += f"Storlek: {size_mb:.1f} MB\n"
                list_text += f"Typ: {backup['type']}\n"
                list_text += f"Status: {'Giltig' if is_valid else 'Korrupt'}\n"
                list_text += "-" * 30 + "\n\n"
            except Exception as e:
                list_text += f"Fel vid läsning av {backup['name']}: {e}\n\n"
        
        self.backup_list_text.delete(1.0, tk.END)
        self.backup_list_text.insert(1.0, list_text)
    
    def save_backup_settings(self):
        """Sparar backup-inställningar"""
        try:
            self.backup_manager.config['auto_backup'] = self.auto_backup_var.get()
            self.backup_manager.config['backup_interval_hours'] = int(self.interval_var.get())
            self.backup_manager.config['max_backups'] = int(self.max_backups_var.get())
            self.backup_manager.config['compress_backups'] = self.compress_var.get()
            
            self.backup_manager.save_config()
            
            # Starta/stoppa auto-backup baserat på inställning
            if self.backup_manager.config['auto_backup']:
                self.backup_manager.start_auto_backup()
            else:
                self.backup_manager.stop_auto_backup()
            
            messagebox.showinfo("Framgång", "Backup-inställningar sparade")
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte spara inställningar: {e}")

# Hjälpfunktioner
def check_schedule_availability() -> bool:
    """Kontrollerar om schedule-biblioteket är tillgängligt"""
    try:
        import schedule
        return True
    except ImportError:
        return False