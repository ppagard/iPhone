#!/usr/bin/env python3
"""
Enkel svensk personnummer validator
Enklare version för snabb validering
"""

import re
from datetime import datetime


def is_valid_personnummer(pnr: str) -> bool:
    """
    Kontrollerar om ett svenskt personnummer är giltigt
    
    Args:
        pnr: Personnummer som sträng
        
    Returns:
        bool: True om personnumret är giltigt, False annars
    """
    # Rensa personnummer
    clean_pnr = re.sub(r'[^\d]', '', pnr)
    
    # Kontrollera längd
    if len(clean_pnr) != 10:
        return False
    
    # Kontrollera format (YYMMDD-XXXX)
    if not re.match(r'^\d{6}\d{3}\d$', clean_pnr):
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
    
    # Beräkna kontrollsiffra (svensk algoritm)
    first_nine = clean_pnr[:9]
    multiplied = []
    
    # För svenska personnummer: multiplicera med 2, 1, 2, 1, 2, 1, 2, 1, 2
    multipliers = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    
    for i, digit in enumerate(first_nine):
        num = int(digit)
        product = num * multipliers[i]
        if product > 9:
            product = (product // 10) + (product % 10)
        multiplied.append(product)
    
    total = sum(multiplied)
    calculated_control = (10 - (total % 10)) % 10
    actual_control = int(control_digit)
    
    return calculated_control == actual_control


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
    
    # Bestäm kön
    last_birth_digit = int(birth_number[-1])
    gender = "Kvinna" if last_birth_digit % 2 == 0 else "Man"
    
    return {
        'valid': True,
        'birth_date': birth_date,
        'gender': gender,
        'formatted': f"{year}{month}{day}-{birth_number}{control_digit}"
    }


def main():
    """Enkel testfunktion"""
    print("=== Enkel Personnummer Validator ===")
    
    # Test med riktiga svenska personnummer (anonymiserade)
    test_numbers = [
        "811224-0018",  # Giltigt personnummer
        "850101-0022",  # Giltigt personnummer
        "900101-0017",  # Giltigt personnummer
        "811224-0019",  # Felaktig kontrollsiffra
        "123456-7890",  # Ogiltigt datum
        "811224-001",   # För kort
        "811224-00180", # För långt
    ]
    
    for pnr in test_numbers:
        if is_valid_personnummer(pnr):
            info = get_personnummer_info(pnr)
            print(f"✅ {pnr} - Giltigt")
            print(f"   Födelsedatum: {info['birth_date']}")
            print(f"   Kön: {info['gender']}")
        else:
            print(f"❌ {pnr} - Ogiltigt")
        print()


if __name__ == "__main__":
    main()