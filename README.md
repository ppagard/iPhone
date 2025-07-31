# Svensk Personnummer Validator

Ett Python-program som kontrollerar svenska personnummer enligt officiella regler.

## Funktioner

- ✅ Validerar svenska personnummer med kontrollsiffra
- 📅 Kontrollerar giltiga födelsedatum
- 👥 Bestämmer kön baserat på personnummer
- 🔧 Stöder olika format (med eller utan bindestreck/plus)
- 📊 Ger detaljerad information om personnumret

## Filformat

Programmet innehåller två versioner:

### 1. `personnummer_validator.py` - Komplett version
- Fullständig klass-baserad implementation
- Detaljerad felhantering
- Interaktivt läge
- Omfattande validering

### 2. `simple_validator.py` - Enkel version
- Enkla funktioner för snabb validering
- Lätt att integrera i andra projekt
- Grundläggande funktionalitet

## Användning

### Kör programmet direkt:
```bash
python personnummer_validator.py
```

### Använd som modul:
```python
from simple_validator import is_valid_personnummer, get_personnummer_info

# Snabb validering
if is_valid_personnummer("19811224-1234"):
    print("Giltigt personnummer!")

# Hämta information
info = get_personnummer_info("19811224-1234")
print(f"Födelsedatum: {info['birth_date']}")
print(f"Kön: {info['gender']}")
```

### Använd den kompletta versionen:
```python
from personnummer_validator import PersonnummerValidator

validator = PersonnummerValidator()
result = validator.validate_personnummer("19811224-1234")

if result['valid']:
    print(f"Giltigt! Födelsedatum: {result['birth_date']}")
else:
    print(f"Ogiltigt: {result['error']}")
```

## Personnummer-format

Svenska personnummer följer formatet: **YYMMDD-XXXX**

- **YY**: År (två siffror)
- **MM**: Månad (01-12)
- **DD**: Dag (01-31)
- **XXXX**: Födelsenummer + kontrollsiffra

### Exempel på giltiga format:
- `19811224-1234`
- `850101-1234`
- `900101+1234` (plus för personer över 100 år)

## Validering

Programmet kontrollerar:

1. **Format**: Korrekt längd och struktur
2. **Datum**: Giltigt födelsedatum
3. **Kontrollsiffra**: Beräknad med Luhn-algoritmen
4. **Århundrade**: Automatisk hantering av 1900/2000-tal

## Kontrollsiffra

Kontrollsiffran beräknas med Luhn-algoritmen:
1. Multiplicera varannan siffra med 2
2. Lägg ihop siffrorna om produkten > 9
3. Summera alla siffror
4. Kontrollsiffra = (10 - summa % 10) % 10

## Kön

Kön bestäms av den sista siffran i födelsenumret:
- **Jämn siffra**: Kvinna
- **Udda siffra**: Man

## Krav

- Python 3.6+
- Inga externa beroenden (endast standardbibliotek)

## Test

Kör test med exempel:
```bash
python simple_validator.py
```

## Licens

Fritt att använda för utbildnings- och personliga projekt.