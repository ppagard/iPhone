#!/usr/bin/env python3
"""
Svensk personnummer validator
Kontrollerar svenska personnummer enligt officiella regler
"""

import re
from datetime import datetime
from typing import Tuple, Optional


class PersonnummerValidator:
    """Klass för att validera svenska personnummer"""
    
    def __init__(self):
        # Regex för att matcha svenska personnummer
        self.pattern = re.compile(r'^(\d{2})(\d{2})(\d{2})[-+]?(\d{3})(\d)$')
    
    def clean_personnummer(self, pnr: str) -> str:
        """Rensar personnummer från formatering"""
        return re.sub(r'[^\d]', '', pnr)
    
    def extract_date_and_control(self, pnr: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Extraherar datum och kontrollsiffra från personnummer"""
        match = self.pattern.match(pnr)
        if match:
            year, month, day, birth_number, control_digit = match.groups()
            return year, month, day, birth_number, control_digit
        return None, None, None, None, None
    
    def calculate_control_digit(self, digits: str) -> int:
        """Beräknar kontrollsiffra enligt svensk algoritm"""
        # För svenska personnummer: multiplicera med 2, 1, 2, 1, 2, 1, 2, 1, 2
        multipliers = [2, 1, 2, 1, 2, 1, 2, 1, 2]
        multiplied = []
        
        for i, digit in enumerate(digits):
            num = int(digit)
            product = num * multipliers[i]
            # Om produkten är större än 9, lägg ihop siffrorna
            if product > 9:
                product = (product // 10) + (product % 10)
            multiplied.append(product)
        
        # Summera alla siffror
        total = sum(multiplied)
        
        # Kontrollsiffran är (10 - (summa % 10)) % 10
        control = (10 - (total % 10)) % 10
        return control
    
    def validate_date(self, year: str, month: str, day: str) -> bool:
        """Validerar datum i personnummer"""
        try:
            # Hantera århundrade
            full_year = int(year)
            if full_year < 50:
                full_year += 2000
            else:
                full_year += 1900
            
            # Kontrollera om datumet är giltigt
            datetime(full_year, int(month), int(day))
            return True
        except ValueError:
            return False
    
    def validate_personnummer(self, pnr: str) -> dict:
        """
        Validerar svenskt personnummer
        
        Args:
            pnr: Personnummer som sträng (med eller utan formatering)
            
        Returns:
            dict: Resultat med validering och information
        """
        result = {
            'valid': False,
            'error': None,
            'formatted': None,
            'birth_date': None,
            'gender': None
        }
        
        # Rensa personnummer
        clean_pnr = self.clean_personnummer(pnr)
        
        # Kontrollera längd
        if len(clean_pnr) != 10:
            result['error'] = "Personnummer måste ha exakt 10 siffror"
            return result
        
        # Extrahera komponenter
        year, month, day, birth_number, control_digit = self.extract_date_and_control(clean_pnr)
        
        if not all([year, month, day, birth_number, control_digit]):
            result['error'] = "Ogiltigt format för personnummer"
            return result
        
        # Validera datum
        if not self.validate_date(year, month, day):
            result['error'] = "Ogiltigt datum i personnummer"
            return result
        
        # Beräkna kontrollsiffra
        first_nine = year + month + day + birth_number
        calculated_control = self.calculate_control_digit(first_nine)
        actual_control = int(control_digit)
        
        if calculated_control != actual_control:
            result['error'] = f"Felaktig kontrollsiffra. Förväntad: {calculated_control}, Faktisk: {actual_control}"
            return result
        
        # Om vi kommit hit är personnumret giltigt
        result['valid'] = True
        
        # Formatera personnummer
        result['formatted'] = f"{year}{month}{day}-{birth_number}{control_digit}"
        
        # Bestäm födelsedatum
        full_year = int(year)
        if full_year < 50:
            full_year += 2000
        else:
            full_year += 1900
        
        result['birth_date'] = f"{full_year}-{month}-{day}"
        
        # Bestäm kön (jämn siffra = kvinna, udda = man)
        last_birth_digit = int(birth_number[-1])
        result['gender'] = "Kvinna" if last_birth_digit % 2 == 0 else "Man"
        
        return result


def main():
    """Huvudfunktion för att testa personnummer-validatorn"""
    validator = PersonnummerValidator()
    
    print("=== Svensk Personnummer Validator ===")
    print("Skriv 'quit' för att avsluta\n")
    
    # Testa några exempel
    test_numbers = [
        "19811224-1234",
        "850101-1234", 
        "900101+1234",
        "123456-7890",
        "19811224-1235"  # Felaktig kontrollsiffra
    ]
    
    print("Testar några exempel:")
    for pnr in test_numbers:
        result = validator.validate_personnummer(pnr)
        status = "✅ GILTIGT" if result['valid'] else "❌ OGILTIGT"
        print(f"{pnr}: {status}")
        if result['error']:
            print(f"  Fel: {result['error']}")
        elif result['valid']:
            print(f"  Födelsedatum: {result['birth_date']}")
            print(f"  Kön: {result['gender']}")
        print()
    
    # Interaktivt läge
    while True:
        try:
            pnr = input("Ange personnummer (eller 'quit'): ").strip()
            
            if pnr.lower() == 'quit':
                print("Avslutar programmet...")
                break
            
            if not pnr:
                print("Ange ett personnummer!")
                continue
            
            result = validator.validate_personnummer(pnr)
            
            if result['valid']:
                print(f"✅ Personnumret är giltigt!")
                print(f"   Formaterat: {result['formatted']}")
                print(f"   Födelsedatum: {result['birth_date']}")
                print(f"   Kön: {result['gender']}")
            else:
                print(f"❌ Personnumret är ogiltigt!")
                print(f"   Fel: {result['error']}")
            
            print()
            
        except KeyboardInterrupt:
            print("\nAvslutar programmet...")
            break
        except Exception as e:
            print(f"Ett fel uppstod: {e}")


if __name__ == "__main__":
    main()