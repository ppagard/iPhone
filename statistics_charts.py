#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statistik och grafer för utgiftshanteraren
Använder matplotlib för visualisering
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
    # Sätt seaborn-stil
    sns.set_style("whitegrid")
    sns.set_palette("husl")
except ImportError:
    SEABORN_AVAILABLE = False

class ExpenseStatistics:
    """Hanterar statistik och grafer för utgifter"""
    
    def __init__(self, database_manager):
        self.db = database_manager
        self.setup_matplotlib()
    
    def setup_matplotlib(self):
        """Sätter upp matplotlib för svenska tecken"""
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
    
    def create_expense_overview_chart(self, group_id: int) -> Figure:
        """Skapar översiktsgraf för utgifter"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('Utgiftsöversikt', fontsize=16, fontweight='bold')
        
        # Hämta data
        expenses = self.db.get_expenses(group_id)
        participants = self.db.get_participants(group_id)
        balances = self.db.get_participant_balances(group_id)
        
        # 1. Utgifter per kategori (cirkeldiagram)
        category_totals = {}
        for exp in expenses:
            category = exp['category'] or 'Okategoriserad'
            if category not in category_totals:
                category_totals[category] = 0
            category_totals[category] += exp['amount']
        
        if category_totals:
            categories = list(category_totals.keys())
            amounts = list(category_totals.values())
            colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
            
            ax1.pie(amounts, labels=categories, autopct='%1.1f%%', colors=colors)
            ax1.set_title('Utgifter per kategori')
        
        # 2. Utgifter över tid (linjediagram)
        if expenses:
            dates = []
            amounts = []
            for exp in expenses:
                try:
                    date = datetime.fromisoformat(exp['date'].replace('Z', '+00:00'))
                    dates.append(date)
                    amounts.append(exp['amount'])
                except:
                    continue
            
            if dates:
                # Gruppera per dag
                daily_totals = {}
                for date, amount in zip(dates, amounts):
                    date_key = date.date()
                    if date_key not in daily_totals:
                        daily_totals[date_key] = 0
                    daily_totals[date_key] += amount
                
                sorted_dates = sorted(daily_totals.keys())
                daily_amounts = [daily_totals[d] for d in sorted_dates]
                
                ax2.plot(sorted_dates, daily_amounts, marker='o', linewidth=2, markersize=6)
                ax2.set_title('Utgifter över tid')
                ax2.set_xlabel('Datum')
                ax2.set_ylabel('Belopp')
                ax2.tick_params(axis='x', rotation=45)
        
        # 3. Saldon per deltagare (stapeldiagram)
        if balances:
            names = [bal['name'] for bal in balances]
            balance_amounts = [bal['balance'] for bal in balances]
            colors = ['green' if bal > 0 else 'red' if bal < 0 else 'gray' for bal in balance_amounts]
            
            bars = ax3.bar(names, balance_amounts, color=colors, alpha=0.7)
            ax3.set_title('Saldo per deltagare')
            ax3.set_xlabel('Deltagare')
            ax3.set_ylabel('Saldo')
            ax3.tick_params(axis='x', rotation=45)
            
            # Lägg till värden på staplarna
            for bar, amount in zip(bars, balance_amounts):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{amount:.0f}', ha='center', va='bottom' if height > 0 else 'top')
        
        # 4. Utgifter per deltagare (stapeldiagram)
        if expenses:
            participant_totals = {}
            for exp in expenses:
                paid_by = exp['paid_by']
                if paid_by not in participant_totals:
                    participant_totals[paid_by] = 0
                participant_totals[paid_by] += exp['amount']
            
            if participant_totals:
                participants = list(participant_totals.keys())
                amounts = list(participant_totals.values())
                
                bars = ax4.bar(participants, amounts, color='skyblue', alpha=0.7)
                ax4.set_title('Utgifter per deltagare')
                ax4.set_xlabel('Deltagare')
                ax4.set_ylabel('Totalt betalat')
                ax4.tick_params(axis='x', rotation=45)
                
                # Lägg till värden på staplarna
                for bar, amount in zip(bars, amounts):
                    height = bar.get_height()
                    ax4.text(bar.get_x() + bar.get_width()/2., height,
                            f'{amount:.0f}', ha='center', va='bottom')
        
        plt.tight_layout()
        return fig
    
    def create_monthly_trend_chart(self, group_id: int) -> Figure:
        """Skapar månadsvis trendgraf"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle('Månadsvis trend', fontsize=16, fontweight='bold')
        
        expenses = self.db.get_expenses(group_id)
        
        if expenses:
            # Gruppera utgifter per månad
            monthly_data = {}
            for exp in expenses:
                try:
                    date = datetime.fromisoformat(exp['date'].replace('Z', '+00:00'))
                    month_key = date.strftime('%Y-%m')
                    if month_key not in monthly_data:
                        monthly_data[month_key] = {
                            'total': 0,
                            'count': 0,
                            'categories': {}
                        }
                    monthly_data[month_key]['total'] += exp['amount']
                    monthly_data[month_key]['count'] += 1
                    
                    category = exp['category'] or 'Okategoriserad'
                    if category not in monthly_data[month_key]['categories']:
                        monthly_data[month_key]['categories'][category] = 0
                    monthly_data[month_key]['categories'][category] += exp['amount']
                except:
                    continue
            
            if monthly_data:
                months = sorted(monthly_data.keys())
                totals = [monthly_data[m]['total'] for m in months]
                counts = [monthly_data[m]['count'] for m in months]
                
                # 1. Totala utgifter per månad
                ax1.plot(months, totals, marker='o', linewidth=2, markersize=8, color='blue')
                ax1.set_title('Totala utgifter per månad')
                ax1.set_ylabel('Belopp')
                ax1.grid(True, alpha=0.3)
                
                # Lägg till värden på punkterna
                for i, (month, total) in enumerate(zip(months, totals)):
                    ax1.annotate(f'{total:.0f}', (month, total), 
                               textcoords="offset points", xytext=(0,10), ha='center')
                
                # 2. Antal utgifter per månad
                ax2.bar(months, counts, color='orange', alpha=0.7)
                ax2.set_title('Antal utgifter per månad')
                ax2.set_xlabel('Månad')
                ax2.set_ylabel('Antal utgifter')
                ax2.grid(True, alpha=0.3)
                
                # Lägg till värden på staplarna
                for i, (month, count) in enumerate(zip(months, counts)):
                    ax2.text(month, count, str(count), ha='center', va='bottom')
        
        plt.tight_layout()
        return fig
    
    def create_participant_analysis_chart(self, group_id: int) -> Figure:
        """Skapar detaljerad deltagaranalys"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Deltagaranalys', fontsize=16, fontweight='bold')
        
        participants = self.db.get_participants(group_id)
        expenses = self.db.get_expenses(group_id)
        balances = self.db.get_participant_balances(group_id)
        
        if participants and expenses:
            participant_names = [p['name'] for p in participants]
            
            # 1. Betalat vs skyldigt per deltagare
            paid_amounts = []
            owed_amounts = []
            
            for participant in participants:
                name = participant['name']
                balance_info = next((b for b in balances if b['name'] == name), None)
                if balance_info:
                    paid_amounts.append(balance_info['total_paid'])
                    owed_amounts.append(balance_info['total_owed'])
                else:
                    paid_amounts.append(0)
                    owed_amounts.append(0)
            
            x = np.arange(len(participant_names))
            width = 0.35
            
            ax1.bar(x - width/2, paid_amounts, width, label='Betalt', color='green', alpha=0.7)
            ax1.bar(x + width/2, owed_amounts, width, label='Skyldigt', color='red', alpha=0.7)
            ax1.set_xlabel('Deltagare')
            ax1.set_ylabel('Belopp')
            ax1.set_title('Betalt vs Skyldigt per deltagare')
            ax1.set_xticks(x)
            ax1.set_xticklabels(participant_names, rotation=45)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. Antal utgifter per deltagare
            expense_counts = {}
            for exp in expenses:
                paid_by = exp['paid_by']
                if paid_by not in expense_counts:
                    expense_counts[paid_by] = 0
                expense_counts[paid_by] += 1
            
            counts = [expense_counts.get(name, 0) for name in participant_names]
            bars = ax2.bar(participant_names, counts, color='purple', alpha=0.7)
            ax2.set_title('Antal utgifter per deltagare')
            ax2.set_xlabel('Deltagare')
            ax2.set_ylabel('Antal utgifter')
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(True, alpha=0.3)
            
            # Lägg till värden på staplarna
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        str(count), ha='center', va='bottom')
            
            # 3. Genomsnittlig utgift per deltagare
            avg_amounts = []
            for name in participant_names:
                participant_expenses = [exp for exp in expenses if exp['paid_by'] == name]
                if participant_expenses:
                    avg_amount = sum(exp['amount'] for exp in participant_expenses) / len(participant_expenses)
                else:
                    avg_amount = 0
                avg_amounts.append(avg_amount)
            
            bars = ax3.bar(participant_names, avg_amounts, color='orange', alpha=0.7)
            ax3.set_title('Genomsnittlig utgift per deltagare')
            ax3.set_xlabel('Deltagare')
            ax3.set_ylabel('Genomsnittligt belopp')
            ax3.tick_params(axis='x', rotation=45)
            ax3.grid(True, alpha=0.3)
            
            # Lägg till värden på staplarna
            for bar, avg in zip(bars, avg_amounts):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{avg:.0f}', ha='center', va='bottom')
            
            # 4. Saldo-distribution (histogram)
            balance_values = [bal['balance'] for bal in balances]
            if balance_values:
                ax4.hist(balance_values, bins=10, color='lightblue', alpha=0.7, edgecolor='black')
                ax4.set_title('Distribution av saldon')
                ax4.set_xlabel('Saldo')
                ax4.set_ylabel('Antal deltagare')
                ax4.grid(True, alpha=0.3)
                
                # Lägg till vertikal linje för medelvärde
                mean_balance = np.mean(balance_values)
                ax4.axvline(mean_balance, color='red', linestyle='--', 
                           label=f'Medelvärde: {mean_balance:.0f}')
                ax4.legend()
        
        plt.tight_layout()
        return fig
    
    def create_category_analysis_chart(self, group_id: int) -> Figure:
        """Skapar kategorianalys"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Kategorianalys', fontsize=16, fontweight='bold')
        
        expenses = self.db.get_expenses(group_id)
        
        if expenses:
            # Gruppera data per kategori
            category_data = {}
            for exp in expenses:
                category = exp['category'] or 'Okategoriserad'
                if category not in category_data:
                    category_data[category] = {
                        'total': 0,
                        'count': 0,
                        'amounts': []
                    }
                category_data[category]['total'] += exp['amount']
                category_data[category]['count'] += 1
                category_data[category]['amounts'].append(exp['amount'])
            
            categories = list(category_data.keys())
            totals = [category_data[cat]['total'] for cat in categories]
            counts = [category_data[cat]['count'] for cat in categories]
            
            # 1. Totala utgifter per kategori (stapeldiagram)
            bars = ax1.bar(categories, totals, color='lightcoral', alpha=0.7)
            ax1.set_title('Totala utgifter per kategori')
            ax1.set_xlabel('Kategori')
            ax1.set_ylabel('Totalt belopp')
            ax1.tick_params(axis='x', rotation=45)
            ax1.grid(True, alpha=0.3)
            
            # Lägg till värden på staplarna
            for bar, total in zip(bars, totals):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{total:.0f}', ha='center', va='bottom')
            
            # 2. Antal utgifter per kategori (cirkeldiagram)
            if counts:
                colors = plt.cm.Pastel1(np.linspace(0, 1, len(categories)))
                wedges, texts, autotexts = ax2.pie(counts, labels=categories, autopct='%1.1f%%', 
                                                   colors=colors, startangle=90)
                ax2.set_title('Antal utgifter per kategori')
            
            # 3. Genomsnittlig utgift per kategori
            avg_amounts = []
            for cat in categories:
                amounts = category_data[cat]['amounts']
                avg_amount = sum(amounts) / len(amounts) if amounts else 0
                avg_amounts.append(avg_amount)
            
            bars = ax3.bar(categories, avg_amounts, color='lightgreen', alpha=0.7)
            ax3.set_title('Genomsnittlig utgift per kategori')
            ax3.set_xlabel('Kategori')
            ax3.set_ylabel('Genomsnittligt belopp')
            ax3.tick_params(axis='x', rotation=45)
            ax3.grid(True, alpha=0.3)
            
            # Lägg till värden på staplarna
            for bar, avg in zip(bars, avg_amounts):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{avg:.0f}', ha='center', va='bottom')
            
            # 4. Utgiftsfördelning (boxplot)
            if len(categories) > 1:
                amounts_by_category = [category_data[cat]['amounts'] for cat in categories]
                box_plot = ax4.boxplot(amounts_by_category, labels=categories, patch_artist=True)
                
                # Färglägg boxarna
                colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
                for patch, color in zip(box_plot['boxes'], colors):
                    patch.set_facecolor(color)
                    patch.set_alpha(0.7)
                
                ax4.set_title('Utgiftsfördelning per kategori')
                ax4.set_xlabel('Kategori')
                ax4.set_ylabel('Belopp')
                ax4.tick_params(axis='x', rotation=45)
                ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def save_chart_as_image(self, fig: Figure, filename: str, dpi: int = 300) -> bool:
        """Sparar graf som bildfil"""
        try:
            fig.savefig(filename, dpi=dpi, bbox_inches='tight')
            return True
        except Exception as e:
            print(f"Fel vid sparande av graf: {e}")
            return False
    
    def create_summary_statistics(self, group_id: int) -> Dict:
        """Skapar sammanfattande statistik"""
        expenses = self.db.get_expenses(group_id)
        participants = self.db.get_participants(group_id)
        balances = self.db.get_participant_balances(group_id)
        
        if not expenses:
            return {}
        
        # Grundläggande statistik
        total_expenses = sum(exp['amount'] for exp in expenses)
        avg_expense = total_expenses / len(expenses)
        max_expense = max(exp['amount'] for exp in expenses)
        min_expense = min(exp['amount'] for exp in expenses)
        
        # Kategoristatistik
        category_stats = {}
        for exp in expenses:
            category = exp['category'] or 'Okategoriserad'
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'count': 0}
            category_stats[category]['total'] += exp['amount']
            category_stats[category]['count'] += 1
        
        # Deltagarstatistik
        participant_stats = {}
        for p in participants:
            participant_expenses = [exp for exp in expenses if exp['paid_by'] == p['name']]
            participant_stats[p['name']] = {
                'total_paid': sum(exp['amount'] for exp in participant_expenses),
                'expense_count': len(participant_expenses),
                'avg_expense': sum(exp['amount'] for exp in participant_expenses) / len(participant_expenses) if participant_expenses else 0
            }
        
        # Tidsstatistik
        dates = []
        for exp in expenses:
            try:
                date = datetime.fromisoformat(exp['date'].replace('Z', '+00:00'))
                dates.append(date)
            except:
                continue
        
        if dates:
            date_range = max(dates) - min(dates)
            expenses_per_day = len(expenses) / max(date_range.days, 1)
        else:
            date_range = timedelta(0)
            expenses_per_day = 0
        
        return {
            'total_expenses': total_expenses,
            'expense_count': len(expenses),
            'participant_count': len(participants),
            'avg_expense': avg_expense,
            'max_expense': max_expense,
            'min_expense': min_expense,
            'date_range_days': date_range.days,
            'expenses_per_day': expenses_per_day,
            'category_stats': category_stats,
            'participant_stats': participant_stats,
            'balance_stats': {
                'total_positive': sum(bal['balance'] for bal in balances if bal['balance'] > 0),
                'total_negative': sum(bal['balance'] for bal in balances if bal['balance'] < 0),
                'balanced_participants': len([bal for bal in balances if abs(bal['balance']) < 0.01])
            }
        }

# Hjälpfunktioner för GUI-integration
def create_chart_widget(parent, fig: Figure) -> FigureCanvasTkAgg:
    """Skapar en Tkinter-widget för att visa matplotlib-graf"""
    canvas = FigureCanvasTkAgg(fig, parent)
    canvas.draw()
    return canvas

def check_matplotlib_availability() -> bool:
    """Kontrollerar om matplotlib är tillgängligt"""
    try:
        import matplotlib
        return True
    except ImportError:
        return False