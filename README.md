# Nieuws Automatisering Project

## Inhoud
- [Overzicht](#overzicht)
- [Installatie](#installatie)
- [Gebruik](#gebruik)
- [Structuur van het project](#structuur-van-het-project)
- [Technologieën](#technologieën)
- [Ethische Overwegingen](#ethische-overwegingen)
  - [Accuraatheid van Informatie](#accuraatheid-van-informatie)
  - [Copyright en Bronvermelding](#copyright-en-bronvermelding)
  - [Transparantie van AI-gebruik](#transparantie-van-ai-gebruik)
- [Auteurs](#auteurs)

## Overzicht
Dit project automatiseert het verzamelen, verwerken en publiceren van nieuwsartikelen via RSS-feeds, AI, en publicatie op een WordPress-website of een lokale webserver via Flask. Er zijn twee versies beschikbaar:

- **NewsGenerator_Flask.py**: De Flask-gebaseerde versie die lokaal draait.
- **NewsGenerator_WordPress.py**: De WordPress-gebaseerde versie die artikelen direct naar een WordPress-site publiceert.

### Installatie
Volg deze stappen om het project te installeren:

1. **Clone de repository**:
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```
   
2. **Installeer de vereiste dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
   
3. **API-sleutel configuratie**:
    Voeg je generative AI-sleutel (zoals van Cohere) toe in de Python-bestanden (`NewsGenerator_Flask.py` en `NewsGenerator_WordPress.py`) om de AI-functionaliteiten te gebruiken.

### Gebruik

#### Flask-versie (`NewsGenerator_Flask.py`)
1. Start de Flask-webserver:
    ```bash
    python NewsGenerator_Flask.py
    ```
2. Open je browser en ga naar `http://localhost:5000` om de gegenereerde artikelen te bekijken. Deze worden lokaal weergegeven en bevatten AI-samenvattingen.

#### WordPress-versie (`NewsGenerator_WordPress.py`)
1. De WordPress-versie publiceert direct op een opgegeven WordPress-site. Voer het script uit:
    ```bash
    python NewsGenerator_WordPress.py
    ```
2. Voer het aantal artikelen in dat je wilt verwerken wanneer hierom wordt gevraagd.
3. De artikelen worden opgehaald, verwerkt, en gepubliceerd op je WordPress-site. Controleer je WordPress-dashboard voor de gegenereerde berichten.
4. Bezoek deze link om de artikelen te kunnen zien: [yapnews site](https://yapnews.meubel-centrum.be/)

### Structuur van het project
- **`NewsGenerator_Flask.py`**: Het script dat nieuwsartikelen verzamelt, samenvat en op een lokale server toont via Flask.
- **`NewsGenerator_WordPress.py`**: De WordPress-versie van de applicatie die de artikelen direct naar WordPress publiceert.
- **`templates/`**: Bevat de HTML-templates voor de Flask-interface.
- **`artikelen/`**: Opslag van lokaal gegenereerde artikelen in HTML.
- **`requirements.txt`**: Lijst van benodigde Python-pakketten.

### Technologieën
- **Flask**: Voor het draaien van de webserver in de lokale versie.
- **WordPress API**: Voor het publiceren van artikelen op een WordPress-site.
- **RSS-feeds**: Voor het verzamelen van nieuwsartikelen.
- **BeautifulSoup**: Voor het scrapen van volledige artikelen.
- **Cohere AI API**: Voor het genereren van samenvattingen en nieuwe titels.

### Ethische Overwegingen

#### Accuraatheid van Informatie
Hoewel AI krachtig is in het samenvatten van nieuws, is er een mogelijkheid dat het fouten maakt. Daarom blijft de originele bron beschikbaar zodat lezers deze kunnen vergelijken met de AI-gegenereerde tekst.

#### Copyright en Bronvermelding
De originele bron en auteur worden altijd vermeld, samen met een link naar het originele artikel. Dit verzekert dat we voldoen aan copyrightregels.

#### Transparantie van AI-gebruik
Lezers worden geïnformeerd wanneer een samenvatting of inzicht is gegenereerd door AI, zodat zij weten dat de tekst niet door een menselijke journalist is geschreven.

### Auteurs
Dit project is gemaakt door Goudantov Bers en Van Camp Loïc.
