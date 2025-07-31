#!/usr/bin/env python3
"""
Test-script för svenska personnummer
Använder riktiga svenska personnummer för att testa valideringen
"""

from simple_validator import is_valid_personnummer, get_personnummer_info


def test_personnummer():
    """Testar med riktiga svenska personnummer"""
    
    # Riktiga svenska personnummer (anonymiserade)
    test_cases = [
        # Giltiga personnummer
        ("19811224-1234", True),
        ("850101-1234", True),
        ("900101+1234", True),  # Plus för personer över 100
        ("19811224-1235", False),  # Felaktig kontrollsiffra
        ("123456-7890", False),  # Ogiltigt datum
        ("19811224-123", False),  # För kort
        ("19811224-12345", False),  # För långt
    ]
    
    print("=== Test av Svenska Personnummer ===")
    print()
    
    for pnr, expected in test_cases:
        result = is_valid_personnummer(pnr)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        valid_text = "GILTIGT" if result else "OGILTIGT"
        expected_text = "GILTIGT" if expected else "OGILTIGT"
        
        print(f"{pnr}: {valid_text} (förväntat: {expected_text}) - {status}")
        
        if result:
            info = get_personnummer_info(pnr)
            print(f"  Födelsedatum: {info['birth_date']}")
            print(f"  Kön: {info['gender']}")
        
        print()


def test_control_digit_calculation():
    """Testar kontrollsiffra-beräkningen"""
    print("=== Test av Kontrollsiffra-beräkning ===")
    print()
    
    # Test med kända värden
    test_digits = "198112241"  # Första 9 siffrorna
    expected_control = 4  # Förväntad kontrollsiffra
    
    # Beräkna kontrollsiffra
    multipliers = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    multiplied = []
    
    for i, digit in enumerate(test_digits):
        num = int(digit)
        product = num * multipliers[i]
        if product > 9:
            product = (product // 10) + (product % 10)
        multiplied.append(product)
    
    total = sum(multiplied)
    calculated_control = (10 - (total % 10)) % 10
    
    print(f"Test-siffror: {test_digits}")
    print(f"Multiplicerade värden: {multiplied}")
    print(f"Summa: {total}")
    print(f"Beräknad kontrollsiffra: {calculated_control}")
    print(f"Förväntad kontrollsiffra: {expected_control}")
    print(f"Matchar: {'✅' if calculated_control == expected_control else '❌'}")
    print()


if __name__ == "__main__":
    test_control_digit_calculation()
    test_personnummer()