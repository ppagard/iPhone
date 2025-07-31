#!/usr/bin/env python3
"""
Fungerande svensk personnummer validator
Med korrekt svensk algoritm för kontrollsiffra
"""

import re
from datetime import datetime


def calculate_control_digit(digits: str) -> int:
    """
    Beräknar kontrollsiffra enligt svensk personnummer-algoritm
    
    Svenska personnummer använder en modifierad version av Luhn-algoritmen:
    - Multiplicera med 2, 1, 2, 1, 2, 1, 2, 1, 2
    - Lägg ihop siffrorna om produkten > 9
    - Kontrollsiffra = (10 - summa % 10) % 10
    """
    if len(digits) != 9:
        raise ValueError("Måste ha exakt 9 siffror")
    
    multipliers = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    sum_digits = 0
    
    for i, digit in enumerate(digits):
        num = int(digit)
        product = num * multipliers[i]
        
        # Lägg ihop siffrorna om produkten > 9
        if product > 9:
            product = (product // 10) + (product % 10)
        
        sum_digits += product
    
    # Kontrollsiffra = (10 - summa % 10) % 10
    control = (10 - (sum_digits % 10)) % 10
    return control


def is_valid_personnummer(pnr: str) -> bool:
    """
    Kontrollerar om ett svenskt personnummer är giltigt
    
    Args:
        pnr: Personnummer som sträng (med eller utan formatering)
        
    Returns:
        bool: True om personnumret är giltigt, False annars
    """
    # Rensa personnummer
    clean_pnr = re.sub(r'[^\d]', '', pnr)
    
    # Kontrollera längd
    if len(clean_pnr) != 10:
        return False
    
    # Extrahera komponenter
    year = clean_pnr[:2]
    month = clean_pnr[2:4]
    day = clean_pnr[4:6]
    birth_number = clean_pnr[6:9]
    control_digit = clean_pnr[9]
    
    # Validera datum
    try:
        full_year = int(year)
        if full_year < 50:
            full_year += 2000
        else:
            full_year += 1900
        
        datetime(full_year, int(month), int(day))
    except ValueError:
        return False
    
    # Beräkna och kontrollera kontrollsiffra
    try:
        first_nine = clean_pnr[:9]
        calculated_control = calculate_control_digit(first_nine)
        actual_control = int(control_digit)
        
        return calculated_control == actual_control
    except ValueError:
        return False


def get_personnummer_info(pnr: str) -> dict:
    """
    Hämtar information om ett personnummer
    
    Args:
        pnr: Personnummer som sträng
        
    Returns:
        dict: Information om personnumret
    """
    if not is_valid_personnummer(pnr):
        return {'valid': False, 'error': 'Ogiltigt personnummer'}
    
    clean_pnr = re.sub(r'[^\d]', '', pnr)
    year = clean_pnr[:2]
    month = clean_pnr[2:4]
    day = clean_pnr[4:6]
    birth_number = clean_pnr[6:9]
    control_digit = clean_pnr[9]
    
    # Bestäm födelsedatum
    full_year = int(year)
    if full_year < 50:
        full_year += 2000
    else:
        full_year += 1900
    
    birth_date = f"{full_year}-{month}-{day}"
    
    # Bestäm kön (jämn siffra = kvinna, udda = man)
    last_birth_digit = int(birth_number[-1])
    gender = "Kvinna" if last_birth_digit % 2 == 0 else "Man"
    
    return {
        'valid': True,
        'birth_date': birth_date,
        'gender': gender,
        'formatted': f"{year}{month}{day}-{birth_number}{control_digit}"
    }


def generate_valid_personnummer(birth_date: str, gender: str = "Man") -> str:
    """
    Genererar ett giltigt personnummer för ett givet födelsedatum
    
    Args:
        birth_date: Födelsedatum i format YYYY-MM-DD
        gender: "Man" eller "Kvinna"
        
    Returns:
        str: Giltigt personnummer
    """
    try:
        # Parsa datum
        date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
        year = str(date_obj.year)[-2:]  # Sista två siffrorna
        month = f"{date_obj.month:02d}"
        day = f"{date_obj.day:02d}"
        
        # Generera födelsenummer baserat på kön
        if gender == "Man":
            # Udda siffror för män
            birth_number = "001"
        else:
            # Jämna siffror för kvinnor
            birth_number = "002"
        
        # Skapa första 9 siffrorna
        first_nine = year + month + day + birth_number
        
        # Beräkna kontrollsiffra
        control_digit = calculate_control_digit(first_nine)
        
        # Skapa personnummer
        personnummer = f"{year}{month}{day}-{birth_number}{control_digit}"
        
        return personnummer
        
    except Exception as e:
        return f"Fel vid generering: {e}"


def main():
    """Huvudfunktion för testning"""
    print("=== Fungerande Svensk Personnummer Validator ===")
    print()
    
    # Generera några giltiga personnummer för testning
    test_personnummer = [
        generate_valid_personnummer("1981-12-24", "Man"),
        generate_valid_personnummer("1985-01-01", "Kvinna"),
        generate_valid_personnummer("1990-01-01", "Man"),
    ]
    
    print("=== Genererade giltiga personnummer ===")
    for pnr in test_personnummer:
        print(f"Genererat: {pnr}")
        if is_valid_personnummer(pnr):
            info = get_personnummer_info(pnr)
            print(f"✅ Validerat: {info['formatted']}")
            print(f"   Födelsedatum: {info['birth_date']}")
            print(f"   Kön: {info['gender']}")
        else:
            print(f"❌ Validering misslyckades")
        print()
    
    # Testa med ogiltiga personnummer
    invalid_numbers = [
        "19811224-1235",  # Felaktig kontrollsiffra
        "123456-7890",    # Ogiltigt datum
        "19811224-123",   # För kort
        "19811224-12345", # För långt
    ]
    
    print("=== Test av ogiltiga personnummer ===")
    for pnr in invalid_numbers:
        if is_valid_personnummer(pnr):
            print(f"❌ {pnr} - Bör vara ogiltigt men validerades som giltigt")
        else:
            print(f"✅ {pnr} - Korrekt validerat som ogiltigt")
    print()


if __name__ == "__main__":
    main()