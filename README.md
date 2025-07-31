# Utgiftshanterare

Ett Python-program för att hantera utgifter och splitta dem mellan deltagare i grupper. Programmet stöder flera valutor och hämtar aktiva växelkurser från API.

## Funktioner

- **Grupphantering**: Skapa och hantera flera grupper
- **Deltagarhantering**: Lägg till och ta bort deltagare i grupper
- **Utgiftshantering**: Registrera utgifter med beskrivning, belopp och valuta
- **Flexibel delning**: Dela utgifter lika, manuellt eller bara betalaren
- **Valutakonvertering**: Automatisk konvertering mellan olika valutor
- **Saldoberäkning**: Visa saldon för alla deltagare
- **Optimala överföringar**: Beräkna rekommenderade överföringar för att balansera gruppen
- **Datahantering**: Spara och ladda gruppdata till/från filer

## Installation

1. Klona eller ladda ner projektet
2. Installera beroenden:
   ```bash
   pip install -r requirements.txt
   ```

## Användning

Kör programmet:
```bash
python expense_manager.py
```

### Huvudmeny

Programmet har en interaktiv meny med följande alternativ:

1. **Hantera grupper**
   - Skapa nya grupper
   - Välj aktiv grupp
   - Lista alla grupper

2. **Hantera deltagare**
   - Lägg till deltagare i aktuell grupp
   - Ta bort deltagare
   - Lista alla deltagare

3. **Hantera utgifter**
   - Lägg till nya utgifter
   - Lista alla utgifter i gruppen

4. **Visa saldon och överföringar**
   - Visa saldo för alla deltagare
   - Visa rekommenderade överföringar
   - Visa totala utgifter

5. **Spara/ladda data**
   - Spara alla grupper till filer
   - Ladda grupper från filer

### Exempel på användning

1. **Skapa en grupp och lägg till deltagare**
   - Välj "Hantera grupper" → "Skapa ny grupp"
   - Ange gruppnamn (t.ex. "Semester")
   - Välj "Hantera deltagare" → "Lägg till deltagare"
   - Lägg till deltagare (t.ex. Anna, Erik, Maria)

2. **Registrera utgifter**
   - Välj "Hantera utgifter" → "Lägg till utgift"
   - Ange beskrivning (t.ex. "Hotell")
   - Ange belopp (t.ex. 1500)
   - Ange valuta (t.ex. SEK)
   - Välj vem som betalade
   - Välj hur utgiften ska delas (lika, manuellt, eller bara betalaren)

3. **Visa saldon**
   - Välj "Visa saldon och överföringar"
   - Se saldo för varje deltagare
   - Se rekommenderade överföringar för att balansera gruppen

## Valutastöd

Programmet stöder flera valutor och hämtar aktiva växelkurser från [ExchangeRate-API](https://exchangerate-api.com/). Valutakurser cachas lokalt för bättre prestanda.

Stödda valutor inkluderar:
- SEK (Svenska kronor)
- USD (Amerikanska dollar)
- EUR (Euro)
- GBP (Brittiska pund)
- Och många fler...

## Filformat

Grupper sparas i JSON-format med följande struktur:
```json
{
  "name": "Gruppnamn",
  "participants": {
    "deltagarnamn": {
      "name": "Deltagarnamn",
      "email": "email@example.com"
    }
  },
  "expenses": [
    {
      "description": "Beskrivning",
      "amount": 100.0,
      "currency": "SEK",
      "paid_by": "deltagarnamn",
      "date": "2024-01-01T12:00:00",
      "category": "Kategori",
      "splits": [
        {
          "participant": "deltagarnamn",
          "share": 0.5
        }
      ]
    }
  ]
}
```

## Teknisk information

### Klasser

- **CurrencyConverter**: Hanterar valutakonvertering och API-anrop
- **Participant**: Representerar en deltagare med utgifter och saldon
- **Expense**: Representerar en utgift med delning mellan deltagare
- **Group**: Hanterar en grupp av deltagare och deras utgifter
- **ExpenseManager**: Huvudklass som hanterar flera grupper

### Beroenden

- `requests`: För API-anrop till valutakurser
- `python-dateutil`: För datumhantering
- `tabulate`: För snygga tabeller i terminalen
- `colorama`: För färgad output i terminalen

## Felsökning

### Vanliga problem

1. **API-fel för valutakurser**
   - Programmet använder fallback till 1.0 om API misslyckas
   - Kontrollera internetanslutning

2. **Filsparande misslyckas**
   - Kontrollera skrivbehörigheter i mappen
   - Kontrollera att filnamnet är giltigt

3. **Ogiltig input**
   - Programmet validerar all input
   - Följ instruktionerna på skärmen

## Utveckling

Programmet är skrivet i Python 3.7+ och följer PEP 8-kodstandarder. Koden är modulär och lätt att utöka med nya funktioner.

### Möjliga förbättringar

- GUI-gränssnitt
- Databashantering
- Export till Excel/CSV
- Notifikationer
- Backup-funktioner
- Mer avancerad rapportgenerering