#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export-funktioner för utgiftshanteraren
Stöder Excel, PDF och CSV med formatering
"""

import json
import csv
from datetime import datetime
from typing import Dict, List, Optional
import os

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class ExportManager:
    """Hanterar export av data till olika format"""
    
    def __init__(self, database_manager):
        self.db = database_manager
    
    def export_to_excel(self, group_id: int, filename: str) -> bool:
        """Exporterar gruppdata till Excel med formatering"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas krävs för Excel-export. Installera med: pip install pandas openpyxl")
        
        try:
            # Hämta data
            group = self.db.get_group_by_id(group_id)
            participants = self.db.get_participants(group_id)
            expenses = self.db.get_expenses(group_id)
            balances = self.db.get_participant_balances(group_id)
            
            # Skapa Excel-fil med flera ark
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Ark 1: Översikt
                overview_data = {
                    'Gruppnamn': [group['name']],
                    'Skapad': [group['created_at']],
                    'Antal deltagare': [len(participants)],
                    'Antal utgifter': [len(expenses)],
                    'Totala utgifter': [sum(exp['amount'] for exp in expenses)]
                }
                overview_df = pd.DataFrame(overview_data)
                overview_df.to_excel(writer, sheet_name='Översikt', index=False)
                
                # Ark 2: Deltagare
                participants_data = []
                for p in participants:
                    participants_data.append({
                        'ID': p['id'],
                        'Namn': p['name'],
                        'E-post': p['email'] or '',
                        'Skapad': p['created_at']
                    })
                participants_df = pd.DataFrame(participants_data)
                participants_df.to_excel(writer, sheet_name='Deltagare', index=False)
                
                # Ark 3: Utgifter
                expenses_data = []
                for exp in expenses:
                    expenses_data.append({
                        'ID': exp['id'],
                        'Beskrivning': exp['description'],
                        'Belopp': exp['amount'],
                        'Valuta': exp['currency'],
                        'Betalad av': exp['paid_by'],
                        'Kategori': exp['category'] or '',
                        'Datum': exp['date'],
                        'Delning': ', '.join([f"{s['participant']} ({s['share']:.2f})" for s in exp['splits']])
                    })
                expenses_df = pd.DataFrame(expenses_data)
                expenses_df.to_excel(writer, sheet_name='Utgifter', index=False)
                
                # Ark 4: Saldon
                balances_data = []
                for bal in balances:
                    status = "Får tillbaka" if bal['balance'] > 0 else "Ska betala" if bal['balance'] < 0 else "Balanserad"
                    balances_data.append({
                        'Namn': bal['name'],
                        'Betalt': bal['total_paid'],
                        'Skyldigt': bal['total_owed'],
                        'Saldo': bal['balance'],
                        'Status': status
                    })
                balances_df = pd.DataFrame(balances_data)
                balances_df.to_excel(writer, sheet_name='Saldon', index=False)
                
                # Ark 5: Statistik per kategori
                category_stats = {}
                for exp in expenses:
                    category = exp['category'] or 'Okategoriserad'
                    if category not in category_stats:
                        category_stats[category] = {'antal': 0, 'total': 0}
                    category_stats[category]['antal'] += 1
                    category_stats[category]['total'] += exp['amount']
                
                category_data = []
                for category, stats in category_stats.items():
                    category_data.append({
                        'Kategori': category,
                        'Antal utgifter': stats['antal'],
                        'Totalt belopp': stats['total']
                    })
                category_df = pd.DataFrame(category_data)
                category_df.to_excel(writer, sheet_name='Kategorier', index=False)
            
            return True
            
        except Exception as e:
            print(f"Fel vid Excel-export: {e}")
            return False
    
    def export_to_pdf(self, group_id: int, filename: str) -> bool:
        """Exporterar gruppdata till PDF med formatering"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab krävs för PDF-export. Installera med: pip install reportlab")
        
        try:
            # Hämta data
            group = self.db.get_group_by_id(group_id)
            participants = self.db.get_participants(group_id)
            expenses = self.db.get_expenses(group_id)
            balances = self.db.get_participant_balances(group_id)
            
            # Skapa PDF-dokument
            doc = SimpleDocTemplate(filename, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Titel
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # Center
            )
            story.append(Paragraph(f"Rapport: {group['name']}", title_style))
            story.append(Spacer(1, 12))
            
            # Översikt
            story.append(Paragraph("Översikt", styles['Heading2']))
            overview_data = [
                ['Gruppnamn', group['name']],
                ['Skapad', group['created_at']],
                ['Antal deltagare', str(len(participants))],
                ['Antal utgifter', str(len(expenses))],
                ['Totala utgifter', f"{sum(exp['amount'] for exp in expenses):.2f}"]
            ]
            overview_table = Table(overview_data, colWidths=[2*inch, 3*inch])
            overview_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(overview_table)
            story.append(Spacer(1, 20))
            
            # Deltagare
            story.append(Paragraph("Deltagare", styles['Heading2']))
            if participants:
                participant_headers = ['ID', 'Namn', 'E-post', 'Skapad']
                participant_data = [participant_headers]
                for p in participants:
                    participant_data.append([
                        str(p['id']),
                        p['name'],
                        p['email'] or '',
                        p['created_at']
                    ])
                participant_table = Table(participant_data, colWidths=[0.5*inch, 1.5*inch, 2*inch, 1.5*inch])
                participant_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(participant_table)
            else:
                story.append(Paragraph("Inga deltagare", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Utgifter
            story.append(Paragraph("Utgifter", styles['Heading2']))
            if expenses:
                expense_headers = ['Beskrivning', 'Belopp', 'Valuta', 'Betalad av', 'Kategori', 'Datum']
                expense_data = [expense_headers]
                for exp in expenses:
                    expense_data.append([
                        exp['description'],
                        f"{exp['amount']:.2f}",
                        exp['currency'],
                        exp['paid_by'],
                        exp['category'] or '',
                        exp['date']
                    ])
                expense_table = Table(expense_data, colWidths=[1.5*inch, 0.8*inch, 0.6*inch, 1*inch, 1*inch, 1.2*inch])
                expense_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(expense_table)
            else:
                story.append(Paragraph("Inga utgifter", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Saldon
            story.append(Paragraph("Saldon", styles['Heading2']))
            if balances:
                balance_headers = ['Namn', 'Betalt', 'Skyldigt', 'Saldo', 'Status']
                balance_data = [balance_headers]
                for bal in balances:
                    status = "Får tillbaka" if bal['balance'] > 0 else "Ska betala" if bal['balance'] < 0 else "Balanserad"
                    balance_data.append([
                        bal['name'],
                        f"{bal['total_paid']:.2f}",
                        f"{bal['total_owed']:.2f}",
                        f"{bal['balance']:.2f}",
                        status
                    ])
                balance_table = Table(balance_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1.2*inch])
                balance_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(balance_table)
            else:
                story.append(Paragraph("Inga saldon", styles['Normal']))
            
            # Skapa PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Fel vid PDF-export: {e}")
            return False
    
    def export_to_csv(self, group_id: int, filename: str, data_type: str = "all") -> bool:
        """Exporterar data till CSV-format"""
        try:
            if data_type == "all":
                # Exportera all data till separata CSV-filer
                base_name = filename.replace('.csv', '')
                
                # Deltagare
                participants = self.db.get_participants(group_id)
                participant_filename = f"{base_name}_deltagare.csv"
                with open(participant_filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'Namn', 'E-post', 'Skapad'])
                    for p in participants:
                        writer.writerow([p['id'], p['name'], p['email'] or '', p['created_at']])
                
                # Utgifter
                expenses = self.db.get_expenses(group_id)
                expense_filename = f"{base_name}_utgifter.csv"
                with open(expense_filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'Beskrivning', 'Belopp', 'Valuta', 'Betalad av', 'Kategori', 'Datum'])
                    for exp in expenses:
                        writer.writerow([
                            exp['id'], exp['description'], exp['amount'], exp['currency'],
                            exp['paid_by'], exp['category'] or '', exp['date']
                        ])
                
                # Saldon
                balances = self.db.get_participant_balances(group_id)
                balance_filename = f"{base_name}_saldon.csv"
                with open(balance_filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Namn', 'Betalt', 'Skyldigt', 'Saldo', 'Status'])
                    for bal in balances:
                        status = "Får tillbaka" if bal['balance'] > 0 else "Ska betala" if bal['balance'] < 0 else "Balanserad"
                        writer.writerow([
                            bal['name'], bal['total_paid'], bal['total_owed'],
                            bal['balance'], status
                        ])
                
                return True
            else:
                # Exportera specifik datatyp
                if data_type == "participants":
                    data = self.db.get_participants(group_id)
                    headers = ['ID', 'Namn', 'E-post', 'Skapad']
                    fieldnames = ['id', 'name', 'email', 'created_at']
                elif data_type == "expenses":
                    data = self.db.get_expenses(group_id)
                    headers = ['ID', 'Beskrivning', 'Belopp', 'Valuta', 'Betalad av', 'Kategori', 'Datum']
                    fieldnames = ['id', 'description', 'amount', 'currency', 'paid_by', 'category', 'date']
                elif data_type == "balances":
                    data = self.db.get_participant_balances(group_id)
                    headers = ['Namn', 'Betalt', 'Skyldigt', 'Saldo', 'Status']
                    fieldnames = ['name', 'total_paid', 'total_owed', 'balance', 'status']
                else:
                    raise ValueError(f"Okänd datatyp: {data_type}")
                
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for item in data:
                        if data_type == "balances":
                            status = "Får tillbaka" if item['balance'] > 0 else "Ska betala" if item['balance'] < 0 else "Balanserad"
                            item['status'] = status
                        writer.writerow(item)
                
                return True
                
        except Exception as e:
            print(f"Fel vid CSV-export: {e}")
            return False
    
    def export_balances_only(self, group_id: int, filename: str) -> bool:
        """Exporterar endast saldon till CSV"""
        return self.export_to_csv(group_id, filename, "balances")
    
    def export_statistics_report(self, group_id: int, filename: str) -> bool:
        """Exporterar statistikrapport till JSON"""
        try:
            group = self.db.get_group_by_id(group_id)
            participants = self.db.get_participants(group_id)
            expenses = self.db.get_expenses(group_id)
            balances = self.db.get_participant_balances(group_id)
            stats = self.db.get_group_statistics(group_id)
            
            # Beräkna kategoristatistik
            category_stats = {}
            for exp in expenses:
                category = exp['category'] or 'Okategoriserad'
                if category not in category_stats:
                    category_stats[category] = {'antal': 0, 'total': 0}
                category_stats[category]['antal'] += 1
                category_stats[category]['total'] += exp['amount']
            
            # Beräkna deltagarstatistik
            participant_stats = {}
            for p in participants:
                participant_expenses = [exp for exp in expenses if exp['paid_by'] == p['name']]
                participant_stats[p['name']] = {
                    'antal_utgifter': len(participant_expenses),
                    'total_betalt': sum(exp['amount'] for exp in participant_expenses),
                    'saldo': next((bal['balance'] for bal in balances if bal['name'] == p['name']), 0)
                }
            
            report_data = {
                'grupp': group,
                'statistik': stats,
                'kategorier': category_stats,
                'deltagare': participant_stats,
                'saldon': balances,
                'genererad': datetime.now().isoformat()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Fel vid export av statistikrapport: {e}")
            return False

# Hjälpfunktioner för GUI-integration
def get_export_formats():
    """Returnerar tillgängliga export-format"""
    formats = {
        'CSV': 'Comma Separated Values',
        'JSON': 'JavaScript Object Notation'
    }
    
    if PANDAS_AVAILABLE:
        formats['Excel'] = 'Microsoft Excel (.xlsx)'
    
    if REPORTLAB_AVAILABLE:
        formats['PDF'] = 'Portable Document Format'
    
    return formats

def check_export_dependencies():
    """Kontrollerar om export-beroenden är installerade"""
    missing = []
    
    if not PANDAS_AVAILABLE:
        missing.append("pandas (för Excel-export)")
    
    if not REPORTLAB_AVAILABLE:
        missing.append("reportlab (för PDF-export)")
    
    return missing