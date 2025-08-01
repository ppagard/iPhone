#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-baserade rekommendationer för utgiftshanteraren
Maskininlärning för förutsägelser och smarta tips
"""

import numpy as np
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3
import os
from dataclasses import dataclass
from enum import Enum
import random

class RecommendationType(Enum):
    EXPENSE_PREDICTION = "expense_prediction"
    BUDGET_ALERT = "budget_alert"
    SAVING_TIP = "saving_tip"
    CATEGORY_INSIGHT = "category_insight"
    PARTICIPANT_BALANCE = "participant_balance"

@dataclass
class Recommendation:
    """Representerar en AI-rekommendation"""
    id: str
    type: RecommendationType
    title: str
    description: str
    confidence: float
    priority: int
    created_at: datetime
    data: Dict = None

class AIRecommendationEngine:
    """AI-motor för rekommendationer"""
    
    def __init__(self, database_manager):
        self.db = database_manager
        self.models = {}
        self.recommendations = []
        self.load_models()
    
    def load_models(self):
        """Laddar tränade modeller"""
        try:
            # För nu använder vi enkla heuristiker
            # I en riktig implementation skulle vi ladda tränade ML-modeller
            self.models = {
                "expense_predictor": self.create_expense_predictor(),
                "category_analyzer": self.create_category_analyzer(),
                "budget_analyzer": self.create_budget_analyzer()
            }
        except Exception as e:
            print(f"Fel vid laddning av AI-modeller: {e}")
    
    def create_expense_predictor(self):
        """Skapar en enkel utgiftsförutsägare"""
        return {
            "type": "heuristic",
            "description": "Enkel heuristisk förutsägare baserad på historiska mönster"
        }
    
    def create_category_analyzer(self):
        """Skapar kategori-analysator"""
        return {
            "type": "heuristic",
            "description": "Analyserar utgiftsmönster per kategori"
        }
    
    def create_budget_analyzer(self):
        """Skapar budget-analysator"""
        return {
            "type": "heuristic",
            "description": "Analyserar budgetöverskridningar och spartips"
        }
    
    def generate_recommendations(self, group_id: int) -> List[Recommendation]:
        """Genererar AI-rekommendationer för en grupp"""
        recommendations = []
        
        try:
            # Hämta gruppdata
            expenses = self.db.get_expenses(group_id)
            participants = self.db.get_participants(group_id)
            balances = self.db.get_participant_balances(group_id)
            
            if not expenses:
                return recommendations
            
            # 1. Utgiftsförutsägelse
            expense_prediction = self.predict_expenses(expenses)
            if expense_prediction:
                recommendations.append(expense_prediction)
            
            # 2. Budget-varningar
            budget_alerts = self.analyze_budget(expenses, balances)
            recommendations.extend(budget_alerts)
            
            # 3. Sparande-tips
            saving_tips = self.generate_saving_tips(expenses)
            recommendations.extend(saving_tips)
            
            # 4. Kategori-insikter
            category_insights = self.analyze_categories(expenses)
            recommendations.extend(category_insights)
            
            # 5. Deltagarsaldon
            balance_recommendations = self.analyze_participant_balances(balances)
            recommendations.extend(balance_recommendations)
            
            # Sortera efter prioritet och konfidens
            recommendations.sort(key=lambda r: (r.priority, r.confidence), reverse=True)
            
            return recommendations
            
        except Exception as e:
            print(f"Fel vid generering av rekommendationer: {e}")
            return []
    
    def predict_expenses(self, expenses: List[Dict]) -> Optional[Recommendation]:
        """Förutsäger framtida utgifter baserat på historiska mönster"""
        try:
            if len(expenses) < 5:
                return None
            
            # Analysera utgiftsmönster
            total_expenses = sum(exp['amount'] for exp in expenses)
            avg_expense = total_expenses / len(expenses)
            
            # Beräkna trend (enkel linjär regression)
            dates = []
            amounts = []
            for exp in expenses:
                try:
                    date = datetime.fromisoformat(exp['date'].replace('Z', '+00:00'))
                    dates.append(date)
                    amounts.append(exp['amount'])
                except:
                    continue
            
            if len(dates) < 3:
                return None
            
            # Enkel trendanalys
            sorted_data = sorted(zip(dates, amounts), key=lambda x: x[0])
            recent_trend = self.calculate_trend(sorted_data[-10:])  # Senaste 10 utgifter
            
            # Förutsäg nästa månad
            predicted_amount = avg_expense * (1 + recent_trend)
            
            confidence = min(0.9, max(0.3, 0.5 + abs(recent_trend) * 0.4))
            
            return Recommendation(
                id=f"prediction_{int(datetime.now().timestamp())}",
                type=RecommendationType.EXPENSE_PREDICTION,
                title="Förutsägelse: Nästa månad",
                description=f"Baserat på dina utgiftsmönster förutspår vi att gruppen kommer att spendera cirka {predicted_amount:.0f} kr nästa månad. Detta är baserat på en {recent_trend*100:+.1f}% trend från senaste utgifterna.",
                confidence=confidence,
                priority=3,
                created_at=datetime.now(),
                data={
                    "predicted_amount": predicted_amount,
                    "trend": recent_trend,
                    "confidence": confidence
                }
            )
            
        except Exception as e:
            print(f"Fel vid utgiftsförutsägelse: {e}")
            return None
    
    def calculate_trend(self, data: List[Tuple[datetime, float]]) -> float:
        """Beräknar trend i data"""
        if len(data) < 2:
            return 0.0
        
        try:
            # Enkel linjär regression
            x_values = [(d - data[0][0]).days for d, _ in data]
            y_values = [amount for _, amount in data]
            
            if len(set(x_values)) < 2:
                return 0.0
            
            # Beräkna trend (förändring per dag)
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)
            
            if n * sum_x2 - sum_x * sum_x == 0:
                return 0.0
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # Konvertera till procentuell förändring per månad
            monthly_trend = slope * 30 / (sum_y / n) if sum_y > 0 else 0
            
            return monthly_trend
            
        except Exception:
            return 0.0
    
    def analyze_budget(self, expenses: List[Dict], balances: List[Dict]) -> List[Recommendation]:
        """Analyserar budget och genererar varningar"""
        recommendations = []
        
        try:
            # Analysera stora utgifter
            large_expenses = [exp for exp in expenses if exp['amount'] > 1000]
            if large_expenses:
                total_large = sum(exp['amount'] for exp in large_expenses)
                avg_expense = sum(exp['amount'] for exp in expenses) / len(expenses)
                
                if total_large > avg_expense * 3:
                    recommendations.append(Recommendation(
                        id=f"budget_alert_{int(datetime.now().timestamp())}",
                        type=RecommendationType.BUDGET_ALERT,
                        title="Stora utgifter upptäckta",
                        description=f"Gruppen har {len(large_expenses)} stora utgifter (över 1000 kr) som tillsammans uppgår till {total_large:.0f} kr. Detta är {total_large/avg_expense:.1f}x högre än genomsnittet.",
                        confidence=0.8,
                        priority=2,
                        created_at=datetime.now(),
                        data={"large_expenses": len(large_expenses), "total_amount": total_large}
                    ))
            
            # Analysera saldon
            negative_balances = [bal for bal in balances if bal['balance'] < -500]
            if negative_balances:
                recommendations.append(Recommendation(
                    id=f"balance_alert_{int(datetime.now().timestamp())}",
                    type=RecommendationType.BUDGET_ALERT,
                    title="Stora saldokulor",
                    description=f"{len(negative_balances)} deltagare har stora saldokulor (över 500 kr). Överväg att reglera dessa snart.",
                    confidence=0.7,
                    priority=2,
                    created_at=datetime.now(),
                    data={"negative_balances": len(negative_balances)}
                ))
            
        except Exception as e:
            print(f"Fel vid budgetanalys: {e}")
        
        return recommendations
    
    def generate_saving_tips(self, expenses: List[Dict]) -> List[Recommendation]:
        """Genererar spartips baserat på utgiftsmönster"""
        recommendations = []
        
        try:
            # Analysera kategorier för sparmöjligheter
            category_totals = {}
            for exp in expenses:
                category = exp['category'] or 'Okategoriserad'
                if category not in category_totals:
                    category_totals[category] = 0
                category_totals[category] += exp['amount']
            
            # Hitta största kategorierna
            sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
            
            if sorted_categories:
                largest_category, largest_amount = sorted_categories[0]
                total_expenses = sum(category_totals.values())
                percentage = (largest_amount / total_expenses) * 100
                
                if percentage > 30:  # Om en kategori är över 30% av totala utgifter
                    recommendations.append(Recommendation(
                        id=f"saving_tip_{int(datetime.now().timestamp())}",
                        type=RecommendationType.SAVING_TIP,
                        title=f"Sparmöjlighet: {largest_category}",
                        description=f"{largest_category} utgör {percentage:.1f}% av gruppens totala utgifter ({largest_amount:.0f} kr). Överväg att söka efter billigare alternativ eller minska utgifterna i denna kategori.",
                        confidence=0.6,
                        priority=1,
                        created_at=datetime.now(),
                        data={"category": largest_category, "amount": largest_amount, "percentage": percentage}
                    ))
            
            # Generera allmänna spartips
            tips = [
                "Överväg att dela stora utgifter mellan fler deltagare",
                "Sätt upp månadsbudgetar för olika kategorier",
                "Granska regelbundet gruppens utgiftsmönster",
                "Använd kategorisering för bättre översikt"
            ]
            
            for i, tip in enumerate(tips):
                recommendations.append(Recommendation(
                    id=f"general_tip_{int(datetime.now().timestamp())}_{i}",
                    type=RecommendationType.SAVING_TIP,
                    title="Spartips",
                    description=tip,
                    confidence=0.5,
                    priority=0,
                    created_at=datetime.now()
                ))
            
        except Exception as e:
            print(f"Fel vid generering av spartips: {e}")
        
        return recommendations
    
    def analyze_categories(self, expenses: List[Dict]) -> List[Recommendation]:
        """Analyserar kategorier och ger insikter"""
        recommendations = []
        
        try:
            # Gruppera utgifter per kategori
            category_data = {}
            for exp in expenses:
                category = exp['category'] or 'Okategoriserad'
                if category not in category_data:
                    category_data[category] = []
                category_data[category].append(exp)
            
            # Analysera varje kategori
            for category, category_expenses in category_data.items():
                if len(category_expenses) < 2:
                    continue
                
                amounts = [exp['amount'] for exp in category_expenses]
                avg_amount = sum(amounts) / len(amounts)
                max_amount = max(amounts)
                min_amount = min(amounts)
                
                # Hitta avvikelser
                if max_amount > avg_amount * 2:
                    recommendations.append(Recommendation(
                        id=f"category_insight_{int(datetime.now().timestamp())}",
                        type=RecommendationType.CATEGORY_INSIGHT,
                        title=f"Avvikelse i {category}",
                        description=f"Största utgiften i {category} ({max_amount:.0f} kr) är {max_amount/avg_amount:.1f}x högre än genomsnittet ({avg_amount:.0f} kr).",
                        confidence=0.7,
                        priority=1,
                        created_at=datetime.now(),
                        data={"category": category, "max_amount": max_amount, "avg_amount": avg_amount}
                    ))
                
                # Analysera frekvens
                if len(category_expenses) > 5:
                    recommendations.append(Recommendation(
                        id=f"category_frequency_{int(datetime.now().timestamp())}",
                        type=RecommendationType.CATEGORY_INSIGHT,
                        title=f"Frekvent kategori: {category}",
                        description=f"{category} är den mest frekventa kategorin med {len(category_expenses)} utgifter. Total kostnad: {sum(amounts):.0f} kr.",
                        confidence=0.6,
                        priority=0,
                        created_at=datetime.now(),
                        data={"category": category, "count": len(category_expenses), "total": sum(amounts)}
                    ))
            
        except Exception as e:
            print(f"Fel vid kategori-analys: {e}")
        
        return recommendations
    
    def analyze_participant_balances(self, balances: List[Dict]) -> List[Recommendation]:
        """Analyserar deltagarsaldon och ger rekommendationer"""
        recommendations = []
        
        try:
            if not balances:
                return recommendations
            
            # Hitta deltagare med stora saldon
            large_positive = [bal for bal in balances if bal['balance'] > 1000]
            large_negative = [bal for bal in balances if bal['balance'] < -1000]
            
            if large_positive:
                recommendations.append(Recommendation(
                    id=f"positive_balance_{int(datetime.now().timestamp())}",
                    type=RecommendationType.PARTICIPANT_BALANCE,
                    title="Stora positiva saldon",
                    description=f"{len(large_positive)} deltagare har stora positiva saldon (över 1000 kr). Överväg att reglera dessa för att balansera gruppen.",
                    confidence=0.6,
                    priority=1,
                    created_at=datetime.now(),
                    data={"positive_balances": len(large_positive)}
                ))
            
            if large_negative:
                recommendations.append(Recommendation(
                    id=f"negative_balance_{int(datetime.now().timestamp())}",
                    type=RecommendationType.PARTICIPANT_BALANCE,
                    title="Stora negativa saldon",
                    description=f"{len(large_negative)} deltagare har stora negativa saldon (över 1000 kr). Dessa bör prioriteras vid reglering.",
                    confidence=0.8,
                    priority=2,
                    created_at=datetime.now(),
                    data={"negative_balances": len(large_negative)}
                ))
            
            # Analysera balansfördelning
            total_positive = sum(bal['balance'] for bal in balances if bal['balance'] > 0)
            total_negative = abs(sum(bal['balance'] for bal in balances if bal['balance'] < 0))
            
            if total_positive > 0 and total_negative > 0:
                balance_ratio = total_positive / total_negative
                if balance_ratio > 1.5 or balance_ratio < 0.7:
                    recommendations.append(Recommendation(
                        id=f"balance_imbalance_{int(datetime.now().timestamp())}",
                        type=RecommendationType.PARTICIPANT_BALANCE,
                        title="Obalanserade saldon",
                        description=f"Gruppen har obalanserade saldon. Totala positiva: {total_positive:.0f} kr, negativa: {total_negative:.0f} kr. Överväg att reglera för att balansera gruppen.",
                        confidence=0.7,
                        priority=1,
                        created_at=datetime.now(),
                        data={"positive_total": total_positive, "negative_total": total_negative, "ratio": balance_ratio}
                    ))
            
        except Exception as e:
            print(f"Fel vid saldo-analys: {e}")
        
        return recommendations
    
    def get_recommendations_for_group(self, group_id: int, limit: int = 10) -> List[Recommendation]:
        """Hämtar rekommendationer för en grupp"""
        try:
            recommendations = self.generate_recommendations(group_id)
            return recommendations[:limit]
        except Exception as e:
            print(f"Fel vid hämtning av rekommendationer: {e}")
            return []
    
    def mark_recommendation_read(self, recommendation_id: str):
        """Markerar en rekommendation som läst"""
        # Här skulle vi normalt spara i databasen
        print(f"Rekommendation {recommendation_id} markerad som läst")
    
    def get_recommendation_stats(self) -> Dict:
        """Returnerar statistik för rekommendationer"""
        try:
            stats = {
                "total_recommendations": len(self.recommendations),
                "by_type": {},
                "average_confidence": 0.0,
                "high_priority_count": 0
            }
            
            if self.recommendations:
                # Gruppera per typ
                for rec in self.recommendations:
                    rec_type = rec.type.value
                    if rec_type not in stats["by_type"]:
                        stats["by_type"][rec_type] = 0
                    stats["by_type"][rec_type] += 1
                
                # Beräkna genomsnittlig konfidens
                confidences = [rec.confidence for rec in self.recommendations]
                stats["average_confidence"] = sum(confidences) / len(confidences)
                
                # Räkna höga prioriteter
                stats["high_priority_count"] = len([rec for rec in self.recommendations if rec.priority >= 2])
            
            return stats
            
        except Exception as e:
            print(f"Fel vid hämtning av rekommendationsstatistik: {e}")
            return {}

class AIWidget:
    """Widget för att visa AI-rekommendationer"""
    
    def __init__(self, parent, ai_engine: AIRecommendationEngine):
        self.parent = parent
        self.ai_engine = ai_engine
        self.current_group_id = None
        self.recommendations = []
    
    def create_widget(self):
        """Skapar AI-rekommendationswidget"""
        frame = ttk.LabelFrame(self.parent, text="AI-rekommendationer", padding=10)
        
        # Kontrollpanel
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="Uppdatera", 
                  command=self.refresh_recommendations).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Visa statistik", 
                  command=self.show_stats).pack(side=tk.LEFT, padx=5)
        
        # Rekommendationslista
        self.recommendations_frame = ttk.Frame(frame)
        self.recommendations_frame.pack(fill=tk.BOTH, expand=True)
        
        # Platshållare
        self.placeholder = ttk.Label(self.recommendations_frame, 
                                   text="Välj en grupp för att se AI-rekommendationer")
        self.placeholder.pack(expand=True)
        
        return frame
    
    def set_group(self, group_id: int):
        """Sätter aktuell grupp och uppdaterar rekommendationer"""
        self.current_group_id = group_id
        self.refresh_recommendations()
    
    def refresh_recommendations(self):
        """Uppdaterar rekommendationer"""
        if not self.current_group_id:
            return
        
        try:
            self.recommendations = self.ai_engine.get_recommendations_for_group(self.current_group_id)
            self.display_recommendations()
        except Exception as e:
            print(f"Fel vid uppdatering av rekommendationer: {e}")
    
    def display_recommendations(self):
        """Visar rekommendationer i GUI"""
        # Rensa tidigare rekommendationer
        for widget in self.recommendations_frame.winfo_children():
            widget.destroy()
        
        if not self.recommendations:
            self.placeholder = ttk.Label(self.recommendations_frame, 
                                       text="Inga rekommendationer tillgängliga")
            self.placeholder.pack(expand=True)
            return
        
        # Skapa scrollbar
        canvas = tk.Canvas(self.recommendations_frame)
        scrollbar = ttk.Scrollbar(self.recommendations_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Visa rekommendationer
        for i, rec in enumerate(self.recommendations):
            self.create_recommendation_widget(scrollable_frame, rec, i)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_recommendation_widget(self, parent, recommendation: Recommendation, index: int):
        """Skapar widget för en rekommendation"""
        # Huvudram
        rec_frame = ttk.Frame(parent)
        rec_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Titel och prioritet
        title_frame = ttk.Frame(rec_frame)
        title_frame.pack(fill=tk.X)
        
        priority_colors = {0: "green", 1: "orange", 2: "red", 3: "purple"}
        priority_color = priority_colors.get(recommendation.priority, "black")
        
        title_label = ttk.Label(title_frame, text=recommendation.title, 
                               font=("Arial", 10, "bold"), foreground=priority_color)
        title_label.pack(side=tk.LEFT)
        
        confidence_label = ttk.Label(title_frame, 
                                   text=f"Konfidens: {recommendation.confidence:.1%}")
        confidence_label.pack(side=tk.RIGHT)
        
        # Beskrivning
        desc_label = ttk.Label(rec_frame, text=recommendation.description, 
                              wraplength=400, justify=tk.LEFT)
        desc_label.pack(fill=tk.X, pady=(5, 0))
        
        # Metadata
        meta_frame = ttk.Frame(rec_frame)
        meta_frame.pack(fill=tk.X, pady=(5, 0))
        
        type_label = ttk.Label(meta_frame, text=f"Typ: {recommendation.type.value}")
        type_label.pack(side=tk.LEFT)
        
        date_label = ttk.Label(meta_frame, 
                              text=f"Skapad: {recommendation.created_at.strftime('%Y-%m-%d %H:%M')}")
        date_label.pack(side=tk.RIGHT)
        
        # Separator
        ttk.Separator(rec_frame, orient='horizontal').pack(fill=tk.X, pady=5)
    
    def show_stats(self):
        """Visar rekommendationsstatistik"""
        stats = self.ai_engine.get_recommendation_stats()
        
        stats_text = f"""
AI-rekommendationsstatistik:
============================

Totalt antal rekommendationer: {stats['total_recommendations']}
Genomsnittlig konfidens: {stats['average_confidence']:.1%}
Höga prioriteter: {stats['high_priority_count']}

Fördelning per typ:
"""
        
        for rec_type, count in stats['by_type'].items():
            stats_text += f"  {rec_type}: {count}\n"
        
        # Visa i dialog
        import tkinter.messagebox as messagebox
        messagebox.showinfo("AI-statistik", stats_text)

# Hjälpfunktioner
def create_ai_widget(parent, ai_engine: AIRecommendationEngine):
    """Skapar AI-widget för GUI"""
    widget = AIWidget(parent, ai_engine)
    return widget.create_widget()

def check_ai_availability() -> bool:
    """Kontrollerar om AI-funktioner är tillgängliga"""
    try:
        import numpy
        return True
    except ImportError:
        return False