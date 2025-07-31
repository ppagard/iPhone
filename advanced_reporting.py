#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Avancerad rapportering för utgiftshanteraren
Detaljerade analyser och anpassningsbara rapporter
"""

import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3
import os
from dataclasses import dataclass
from enum import Enum
import matplotlib.pyplot as plt
import numpy as np

class ReportType(Enum):
    MONTHLY_SUMMARY = "monthly_summary"
    PARTICIPANT_ANALYSIS = "participant_analysis"
    CATEGORY_BREAKDOWN = "category_breakdown"
    TREND_ANALYSIS = "trend_analysis"
    BUDGET_REPORT = "budget_report"
    CUSTOM_REPORT = "custom_report"

@dataclass
class ReportConfig:
    """Konfiguration för en rapport"""
    name: str
    type: ReportType
    parameters: Dict
    created_at: datetime
    last_generated: Optional[datetime] = None

class AdvancedReportingEngine:
    """Motor för avancerad rapportering"""
    
    def __init__(self, database_manager):
        self.db = database_manager
        self.reports = {}
        self.load_report_templates()
    
    def load_report_templates(self):
        """Laddar rapportmallar"""
        self.templates = {
            ReportType.MONTHLY_SUMMARY: {
                "name": "Månadsöversikt",
                "description": "Sammanfattning av månadens utgifter",
                "parameters": ["group_id", "month", "year"]
            },
            ReportType.PARTICIPANT_ANALYSIS: {
                "name": "Deltagaranalys",
                "description": "Detaljerad analys per deltagare",
                "parameters": ["group_id", "date_from", "date_to"]
            },
            ReportType.CATEGORY_BREAKDOWN: {
                "name": "Kategorifördelning",
                "description": "Utgifter fördelade per kategori",
                "parameters": ["group_id", "date_from", "date_to"]
            },
            ReportType.TREND_ANALYSIS: {
                "name": "Trendanalys",
                "description": "Utveckling över tid",
                "parameters": ["group_id", "months_back"]
            },
            ReportType.BUDGET_REPORT: {
                "name": "Budgetrapport",
                "description": "Budgetöverskridningar och spartips",
                "parameters": ["group_id", "budget_limits"]
            }
        }
    
    def generate_monthly_summary(self, group_id: int, month: int, year: int) -> Dict:
        """Genererar månadsöversikt"""
        try:
            # Hämta utgifter för månaden
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            expenses = self.get_expenses_in_period(group_id, start_date, end_date)
            participants = self.db.get_participants(group_id)
            balances = self.db.get_participant_balances(group_id)
            
            # Beräkna statistik
            total_expenses = sum(exp['amount'] for exp in expenses)
            avg_expense = total_expenses / len(expenses) if expenses else 0
            expense_count = len(expenses)
            
            # Kategorifördelning
            category_totals = {}
            for exp in expenses:
                category = exp['category'] or 'Okategoriserad'
                if category not in category_totals:
                    category_totals[category] = 0
                category_totals[category] += exp['amount']
            
            # Deltagarfördelning
            participant_totals = {}
            for exp in expenses:
                paid_by = exp['paid_by']
                if paid_by not in participant_totals:
                    participant_totals[paid_by] = 0
                participant_totals[paid_by] += exp['amount']
            
            return {
                "report_type": "monthly_summary",
                "period": f"{year}-{month:02d}",
                "total_expenses": total_expenses,
                "expense_count": expense_count,
                "avg_expense": avg_expense,
                "participant_count": len(participants),
                "category_breakdown": category_totals,
                "participant_breakdown": participant_totals,
                "balances": balances,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Fel vid generering av månadsöversikt: {e}")
            return {}
    
    def generate_participant_analysis(self, group_id: int, date_from: datetime, 
                                    date_to: datetime) -> Dict:
        """Genererar deltagaranalys"""
        try:
            expenses = self.get_expenses_in_period(group_id, date_from, date_to)
            participants = self.db.get_participants(group_id)
            
            participant_analysis = {}
            
            for participant in participants:
                name = participant['name']
                
                # Hitta utgifter betalda av denna deltagare
                paid_expenses = [exp for exp in expenses if exp['paid_by'] == name]
                
                # Hitta utgifter där deltagaren är med
                involved_expenses = []
                for exp in expenses:
                    splits = exp.get('splits', [])
                    if any(split['participant'] == name for split in splits):
                        involved_expenses.append(exp)
                
                # Beräkna statistik
                total_paid = sum(exp['amount'] for exp in paid_expenses)
                total_involved = sum(exp['amount'] for exp in involved_expenses)
                
                # Beräkna genomsnittlig deltagare
                avg_participation = total_involved / len(participants) if participants else 0
                fair_share = total_involved - avg_participation
                
                participant_analysis[name] = {
                    "total_paid": total_paid,
                    "total_involved": total_involved,
                    "expense_count": len(paid_expenses),
                    "avg_participation": avg_participation,
                    "fair_share": fair_share,
                    "balance": total_paid - fair_share
                }
            
            return {
                "report_type": "participant_analysis",
                "period": f"{date_from.strftime('%Y-%m-%d')} till {date_to.strftime('%Y-%m-%d')}",
                "participants": participant_analysis,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Fel vid generering av deltagaranalys: {e}")
            return {}
    
    def generate_category_breakdown(self, group_id: int, date_from: datetime, 
                                  date_to: datetime) -> Dict:
        """Genererar kategorifördelning"""
        try:
            expenses = self.get_expenses_in_period(group_id, date_from, date_to)
            
            category_analysis = {}
            
            for exp in expenses:
                category = exp['category'] or 'Okategoriserad'
                
                if category not in category_analysis:
                    category_analysis[category] = {
                        "total_amount": 0,
                        "expense_count": 0,
                        "avg_amount": 0,
                        "participants": set(),
                        "expenses": []
                    }
                
                category_analysis[category]["total_amount"] += exp['amount']
                category_analysis[category]["expense_count"] += 1
                category_analysis[category]["participants"].add(exp['paid_by'])
                category_analysis[category]["expenses"].append(exp)
            
            # Beräkna genomsnitt och konvertera sets till listor
            for category, data in category_analysis.items():
                data["avg_amount"] = data["total_amount"] / data["expense_count"]
                data["participants"] = list(data["participants"])
                data["participant_count"] = len(data["participants"])
            
            return {
                "report_type": "category_breakdown",
                "period": f"{date_from.strftime('%Y-%m-%d')} till {date_to.strftime('%Y-%m-%d')}",
                "categories": category_analysis,
                "total_expenses": sum(exp['amount'] for exp in expenses),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Fel vid generering av kategorifördelning: {e}")
            return {}
    
    def generate_trend_analysis(self, group_id: int, months_back: int = 6) -> Dict:
        """Genererar trendanalys"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months_back * 30)
            
            expenses = self.get_expenses_in_period(group_id, start_date, end_date)
            
            # Gruppera per månad
            monthly_data = {}
            for exp in expenses:
                try:
                    date = datetime.fromisoformat(exp['date'].replace('Z', '+00:00'))
                    month_key = date.strftime('%Y-%m')
                    
                    if month_key not in monthly_data:
                        monthly_data[month_key] = {
                            "total_amount": 0,
                            "expense_count": 0,
                            "categories": {},
                            "participants": set()
                        }
                    
                    monthly_data[month_key]["total_amount"] += exp['amount']
                    monthly_data[month_key]["expense_count"] += 1
                    monthly_data[month_key]["participants"].add(exp['paid_by'])
                    
                    category = exp['category'] or 'Okategoriserad'
                    if category not in monthly_data[month_key]["categories"]:
                        monthly_data[month_key]["categories"][category] = 0
                    monthly_data[month_key]["categories"][category] += exp['amount']
                    
                except Exception:
                    continue
            
            # Konvertera sets till listor
            for month_data in monthly_data.values():
                month_data["participants"] = list(month_data["participants"])
                month_data["participant_count"] = len(month_data["participants"])
            
            # Beräkna trender
            months = sorted(monthly_data.keys())
            amounts = [monthly_data[month]["total_amount"] for month in months]
            
            trend = self.calculate_trend(amounts) if len(amounts) > 1 else 0
            
            return {
                "report_type": "trend_analysis",
                "period": f"{months_back} månader tillbaka",
                "monthly_data": monthly_data,
                "trend": trend,
                "total_months": len(months),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Fel vid generering av trendanalys: {e}")
            return {}
    
    def generate_budget_report(self, group_id: int, budget_limits: Dict) -> Dict:
        """Genererar budgetrapport"""
        try:
            expenses = self.db.get_expenses(group_id)
            participants = self.db.get_participants(group_id)
            
            # Analysera budgetöverskridningar per kategori
            category_analysis = {}
            for exp in expenses:
                category = exp['category'] or 'Okategoriserad'
                
                if category not in category_analysis:
                    category_analysis[category] = {
                        "total_amount": 0,
                        "budget_limit": budget_limits.get(category, float('inf')),
                        "expense_count": 0
                    }
                
                category_analysis[category]["total_amount"] += exp['amount']
                category_analysis[category]["expense_count"] += 1
            
            # Beräkna överskridningar
            for category, data in category_analysis.items():
                data["over_budget"] = data["total_amount"] > data["budget_limit"]
                data["budget_usage"] = (data["total_amount"] / data["budget_limit"]) * 100 if data["budget_limit"] != float('inf') else 0
                data["remaining_budget"] = max(0, data["budget_limit"] - data["total_amount"])
            
            # Hitta problemområden
            over_budget_categories = [cat for cat, data in category_analysis.items() 
                                   if data["over_budget"]]
            
            # Generera spartips
            saving_tips = self.generate_budget_saving_tips(category_analysis)
            
            return {
                "report_type": "budget_report",
                "category_analysis": category_analysis,
                "over_budget_categories": over_budget_categories,
                "saving_tips": saving_tips,
                "total_budget_usage": sum(data["budget_usage"] for data in category_analysis.values() if data["budget_limit"] != float('inf')),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Fel vid generering av budgetrapport: {e}")
            return {}
    
    def generate_custom_report(self, group_id: int, parameters: Dict) -> Dict:
        """Genererar anpassad rapport"""
        try:
            report_type = parameters.get("type", "summary")
            date_from = parameters.get("date_from")
            date_to = parameters.get("date_to")
            
            if report_type == "summary":
                return self.generate_monthly_summary(group_id, 
                                                   parameters.get("month", datetime.now().month),
                                                   parameters.get("year", datetime.now().year))
            elif report_type == "participant":
                return self.generate_participant_analysis(group_id, date_from, date_to)
            elif report_type == "category":
                return self.generate_category_breakdown(group_id, date_from, date_to)
            elif report_type == "trend":
                return self.generate_trend_analysis(group_id, parameters.get("months_back", 6))
            else:
                return {"error": "Okänd rapporttyp"}
                
        except Exception as e:
            print(f"Fel vid generering av anpassad rapport: {e}")
            return {}
    
    def get_expenses_in_period(self, group_id: int, date_from: datetime, 
                              date_to: datetime) -> List[Dict]:
        """Hämtar utgifter inom ett tidsintervall"""
        try:
            expenses = self.db.get_expenses(group_id)
            filtered_expenses = []
            
            for exp in expenses:
                try:
                    exp_date = datetime.fromisoformat(exp['date'].replace('Z', '+00:00'))
                    if date_from <= exp_date < date_to:
                        filtered_expenses.append(exp)
                except Exception:
                    continue
            
            return filtered_expenses
            
        except Exception as e:
            print(f"Fel vid hämtning av utgifter: {e}")
            return []
    
    def calculate_trend(self, values: List[float]) -> float:
        """Beräknar trend i en lista av värden"""
        if len(values) < 2:
            return 0.0
        
        try:
            # Enkel linjär regression
            n = len(values)
            x_values = list(range(n))
            y_values = values
            
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)
            
            if n * sum_x2 - sum_x * sum_x == 0:
                return 0.0
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # Konvertera till procentuell förändring
            avg_value = sum_y / n
            trend_percentage = (slope / avg_value) * 100 if avg_value > 0 else 0
            
            return trend_percentage
            
        except Exception:
            return 0.0
    
    def generate_budget_saving_tips(self, category_analysis: Dict) -> List[str]:
        """Genererar spartips baserat på budgetanalys"""
        tips = []
        
        # Hitta kategorier över budget
        over_budget = [(cat, data) for cat, data in category_analysis.items() 
                      if data["over_budget"]]
        
        if over_budget:
            largest_over = max(over_budget, key=lambda x: x[1]["total_amount"])
            tips.append(f"Kategori '{largest_over[0]}' är {largest_over[1]['budget_usage']:.1f}% över budget. "
                       f"Överväg att minska utgifterna i denna kategori.")
        
        # Hitta kategorier nära budgetgränsen
        near_limit = [(cat, data) for cat, data in category_analysis.items() 
                     if 80 <= data["budget_usage"] <= 100 and not data["over_budget"]]
        
        if near_limit:
            tips.append(f"{len(near_limit)} kategorier är nära budgetgränsen. "
                       f"Var försiktig med nya utgifter i dessa kategorier.")
        
        # Allmänna tips
        tips.extend([
            "Sätt upp månadsbudgetar för varje kategori",
            "Granska regelbundet utgiftsmönster",
            "Dela stora utgifter mellan fler deltagare",
            "Använd kategorisering för bättre översikt"
        ])
        
        return tips
    
    def export_report_to_json(self, report: Dict, filename: str) -> bool:
        """Exporterar rapport till JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Fel vid export till JSON: {e}")
            return False
    
    def export_report_to_csv(self, report: Dict, filename: str) -> bool:
        """Exporterar rapport till CSV"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Skriv header
                writer.writerow(['Rapport', report.get('report_type', 'unknown')])
                writer.writerow(['Period', report.get('period', 'unknown')])
                writer.writerow(['Genererad', report.get('generated_at', 'unknown')])
                writer.writerow([])
                
                # Skriv data beroende på rapporttyp
                if report.get('report_type') == 'monthly_summary':
                    writer.writerow(['Totala utgifter', report.get('total_expenses', 0)])
                    writer.writerow(['Antal utgifter', report.get('expense_count', 0)])
                    writer.writerow(['Genomsnittlig utgift', report.get('avg_expense', 0)])
                    writer.writerow([])
                    
                    # Kategorifördelning
                    writer.writerow(['Kategori', 'Belopp'])
                    for category, amount in report.get('category_breakdown', {}).items():
                        writer.writerow([category, amount])
                
                elif report.get('report_type') == 'participant_analysis':
                    writer.writerow(['Deltagare', 'Betalt', 'Involverad', 'Saldo'])
                    for name, data in report.get('participants', {}).items():
                        writer.writerow([
                            name,
                            data.get('total_paid', 0),
                            data.get('total_involved', 0),
                            data.get('balance', 0)
                        ])
            
            return True
            
        except Exception as e:
            print(f"Fel vid export till CSV: {e}")
            return False
    
    def create_report_chart(self, report: Dict, chart_type: str = "pie") -> Optional[plt.Figure]:
        """Skapar graf för rapport"""
        try:
            if chart_type == "pie" and report.get('report_type') == 'monthly_summary':
                return self.create_category_pie_chart(report)
            elif chart_type == "bar" and report.get('report_type') == 'participant_analysis':
                return self.create_participant_bar_chart(report)
            elif chart_type == "line" and report.get('report_type') == 'trend_analysis':
                return self.create_trend_line_chart(report)
            else:
                return None
                
        except Exception as e:
            print(f"Fel vid skapande av rapportgraf: {e}")
            return None
    
    def create_category_pie_chart(self, report: Dict) -> plt.Figure:
        """Skapar cirkeldiagram för kategorier"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        categories = list(report.get('category_breakdown', {}).keys())
        amounts = list(report.get('category_breakdown', {}).values())
        
        if categories and amounts:
            colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
            wedges, texts, autotexts = ax.pie(amounts, labels=categories, autopct='%1.1f%%', 
                                             colors=colors, startangle=90)
            ax.set_title(f"Kategorifördelning - {report.get('period', '')}")
        
        return fig
    
    def create_participant_bar_chart(self, report: Dict) -> plt.Figure:
        """Skapar stapeldiagram för deltagare"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        participants = list(report.get('participants', {}).keys())
        paid_amounts = [report['participants'][p].get('total_paid', 0) for p in participants]
        involved_amounts = [report['participants'][p].get('total_involved', 0) for p in participants]
        
        if participants:
            x = np.arange(len(participants))
            width = 0.35
            
            ax.bar(x - width/2, paid_amounts, width, label='Betalt', color='green', alpha=0.7)
            ax.bar(x + width/2, involved_amounts, width, label='Involverad', color='blue', alpha=0.7)
            
            ax.set_xlabel('Deltagare')
            ax.set_ylabel('Belopp')
            ax.set_title(f"Deltagaranalys - {report.get('period', '')}")
            ax.set_xticks(x)
            ax.set_xticklabels(participants, rotation=45)
            ax.legend()
        
        return fig
    
    def create_trend_line_chart(self, report: Dict) -> plt.Figure:
        """Skapar linjediagram för trender"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        monthly_data = report.get('monthly_data', {})
        months = sorted(monthly_data.keys())
        amounts = [monthly_data[month]['total_amount'] for month in months]
        
        if months and amounts:
            ax.plot(months, amounts, marker='o', linewidth=2, markersize=6)
            ax.set_xlabel('Månad')
            ax.set_ylabel('Totala utgifter')
            ax.set_title(f"Trendanalys - {report.get('period', '')}")
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
        
        return fig

class ReportWidget:
    """Widget för att hantera rapporter"""
    
    def __init__(self, parent, reporting_engine: AdvancedReportingEngine):
        self.parent = parent
        self.engine = reporting_engine
        self.current_group_id = None
    
    def create_widget(self):
        """Skapar rapportwidget"""
        frame = ttk.LabelFrame(self.parent, text="Avancerad rapportering", padding=10)
        
        # Kontrollpanel
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(control_frame, text="Rapporttyp:").pack(side=tk.LEFT)
        self.report_type_var = tk.StringVar(value="monthly_summary")
        report_combo = ttk.Combobox(control_frame, textvariable=self.report_type_var,
                                   values=list(self.engine.templates.keys()), width=20)
        report_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(control_frame, text="Generera rapport", 
                  command=self.generate_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Exportera", 
                  command=self.export_report).pack(side=tk.LEFT, padx=5)
        
        # Rapportvisning
        self.report_frame = ttk.Frame(frame)
        self.report_frame.pack(fill=tk.BOTH, expand=True)
        
        # Platshållare
        self.placeholder = ttk.Label(self.report_frame, 
                                   text="Generera en rapport för att se resultat")
        self.placeholder.pack(expand=True)
        
        return frame
    
    def set_group(self, group_id: int):
        """Sätter aktuell grupp"""
        self.current_group_id = group_id
    
    def generate_report(self):
        """Genererar rapport"""
        if not self.current_group_id:
            messagebox.showwarning("Varning", "Välj en grupp först")
            return
        
        try:
            report_type = self.report_type_var.get()
            
            if report_type == "monthly_summary":
                report = self.engine.generate_monthly_summary(
                    self.current_group_id, 
                    datetime.now().month, 
                    datetime.now().year
                )
            elif report_type == "participant_analysis":
                date_from = datetime.now() - timedelta(days=30)
                date_to = datetime.now()
                report = self.engine.generate_participant_analysis(
                    self.current_group_id, date_from, date_to
                )
            elif report_type == "category_breakdown":
                date_from = datetime.now() - timedelta(days=30)
                date_to = datetime.now()
                report = self.engine.generate_category_breakdown(
                    self.current_group_id, date_from, date_to
                )
            elif report_type == "trend_analysis":
                report = self.engine.generate_trend_analysis(self.current_group_id, 6)
            else:
                report = {"error": "Okänd rapporttyp"}
            
            self.display_report(report)
            
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte generera rapport: {e}")
    
    def display_report(self, report: Dict):
        """Visar rapport i GUI"""
        # Rensa tidigare rapport
        for widget in self.report_frame.winfo_children():
            widget.destroy()
        
        if "error" in report:
            ttk.Label(self.report_frame, text=f"Fel: {report['error']}").pack(expand=True)
            return
        
        # Skapa scrollbar
        canvas = tk.Canvas(self.report_frame)
        scrollbar = ttk.Scrollbar(self.report_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Visa rapportdata
        self.create_report_widget(scrollable_frame, report)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_report_widget(self, parent, report: Dict):
        """Skapar widget för rapportvisning"""
        # Header
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text=f"Rapport: {report.get('report_type', 'unknown')}", 
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        ttk.Label(header_frame, text=f"Period: {report.get('period', 'unknown')}", 
                 font=("Arial", 10)).pack(side=tk.RIGHT)
        
        # Rapportdata
        if report.get('report_type') == 'monthly_summary':
            self.create_monthly_summary_widget(parent, report)
        elif report.get('report_type') == 'participant_analysis':
            self.create_participant_analysis_widget(parent, report)
        elif report.get('report_type') == 'category_breakdown':
            self.create_category_breakdown_widget(parent, report)
        elif report.get('report_type') == 'trend_analysis':
            self.create_trend_analysis_widget(parent, report)
    
    def create_monthly_summary_widget(self, parent, report: Dict):
        """Skapar widget för månadsöversikt"""
        # Statistik
        stats_frame = ttk.LabelFrame(parent, text="Statistik", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        stats_text = f"""
Totala utgifter: {report.get('total_expenses', 0):.0f} kr
Antal utgifter: {report.get('expense_count', 0)}
Genomsnittlig utgift: {report.get('avg_expense', 0):.0f} kr
Antal deltagare: {report.get('participant_count', 0)}
        """
        
        ttk.Label(stats_frame, text=stats_text, justify=tk.LEFT).pack(anchor=tk.W)
        
        # Kategorifördelning
        if report.get('category_breakdown'):
            cat_frame = ttk.LabelFrame(parent, text="Kategorifördelning", padding=10)
            cat_frame.pack(fill=tk.X, pady=(0, 10))
            
            for category, amount in report['category_breakdown'].items():
                ttk.Label(cat_frame, text=f"{category}: {amount:.0f} kr").pack(anchor=tk.W)
    
    def create_participant_analysis_widget(self, parent, report: Dict):
        """Skapar widget för deltagaranalys"""
        if report.get('participants'):
            part_frame = ttk.LabelFrame(parent, text="Deltagaranalys", padding=10)
            part_frame.pack(fill=tk.X, pady=(0, 10))
            
            for name, data in report['participants'].items():
                part_text = f"""
{name}:
  Betalt: {data.get('total_paid', 0):.0f} kr
  Involverad: {data.get('total_involved', 0):.0f} kr
  Saldo: {data.get('balance', 0):.0f} kr
                """
                ttk.Label(part_frame, text=part_text, justify=tk.LEFT).pack(anchor=tk.W)
    
    def create_category_breakdown_widget(self, parent, report: Dict):
        """Skapar widget för kategorifördelning"""
        if report.get('categories'):
            cat_frame = ttk.LabelFrame(parent, text="Kategorifördelning", padding=10)
            cat_frame.pack(fill=tk.X, pady=(0, 10))
            
            for category, data in report['categories'].items():
                cat_text = f"""
{category}:
  Total: {data.get('total_amount', 0):.0f} kr
  Antal utgifter: {data.get('expense_count', 0)}
  Genomsnitt: {data.get('avg_amount', 0):.0f} kr
                """
                ttk.Label(cat_frame, text=cat_text, justify=tk.LEFT).pack(anchor=tk.W)
    
    def create_trend_analysis_widget(self, parent, report: Dict):
        """Skapar widget för trendanalys"""
        if report.get('monthly_data'):
            trend_frame = ttk.LabelFrame(parent, text="Trendanalys", padding=10)
            trend_frame.pack(fill=tk.X, pady=(0, 10))
            
            trend_text = f"Trend: {report.get('trend', 0):.1f}% per månad\n"
            trend_text += f"Antal månader: {report.get('total_months', 0)}\n\n"
            
            for month, data in report['monthly_data'].items():
                trend_text += f"{month}: {data.get('total_amount', 0):.0f} kr\n"
            
            ttk.Label(trend_frame, text=trend_text, justify=tk.LEFT).pack(anchor=tk.W)
    
    def export_report(self):
        """Exporterar aktuell rapport"""
        # Här skulle vi normalt exportera den senaste rapporten
        messagebox.showinfo("Export", "Export-funktion kommer snart!")

# Hjälpfunktioner
def create_report_widget(parent, reporting_engine: AdvancedReportingEngine):
    """Skapar rapportwidget för GUI"""
    widget = ReportWidget(parent, reporting_engine)
    return widget.create_widget()

def check_reporting_availability() -> bool:
    """Kontrollerar om rapporteringsfunktioner är tillgängliga"""
    try:
        import matplotlib
        import numpy
        return True
    except ImportError:
        return False