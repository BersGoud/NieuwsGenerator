# Nieuws Automatisering Project

## Inhoud
- [Nieuws Automatisering Project](#nieuws-automatisering-project)
  - [Inhoud](#inhoud)
    - [Overzicht](#overzicht)
    - [Installatie](#installatie)
    - [Gebruik](#gebruik)
    - [Structuur van het project](#structuur-van-het-project)
    - [Technologieën](#technologieën)
    - [Ethische Overwegingen](#ethische-overwegingen)
      - [Accuraatheid van Informatie:](#accuraatheid-van-informatie)
      - [Copyright en Bronvermelding:](#copyright-en-bronvermelding)
      - [Transparantie van AI-gebruik:](#transparantie-van-ai-gebruik)
    - [Auteurs](#auteurs)

### Overzicht
Dit project automatiseert het proces van nieuws verzamelen, vertalen en publiceren op een nieuwssite. We gebruiken een RSS-feed om nieuwsartikelen te verzamelen, AI voor vertaling en samenvattingen, en Flask voor het hosten van een eenvoudige website met de artikelen.

### Installatie
Volg deze stappen om het project te installeren:
1. Clone de repository:
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```
2. Installeer de vereiste dependencies met:
    ```bash
    pip install -r requirements.txt
    ```

3. Zorg ervoor dat je een API-sleutel hebt voor de generative AI service (bijv. Cohere). Voeg deze sleutel toe in het Python-bestand.

### Gebruik
1. Start de Flask-webserver:
    ```bash
    python NewsGenerator.py
    ```

2. Open je browser en navigeer naar `http://localhost:5000` om de homepage te bekijken.

3. De nieuwsartikelen worden opgehaald, vertaald en samengevat. Elke samenvatting kan worden bekeken door op de links te klikken.

### Structuur van het project
- `NewsGenerator.py`: Het hoofdscript dat de server opzet, nieuwsartikelen verzamelt, vertaalt en publiceert.
- `artikelen/`: Hier worden de gegenereerde HTML-bestanden van de artikelen opgeslagen.
- `templates/`: Bevat HTML-templates voor de homepage en de individuele artikelen.
- `requirements.txt`: Lijst met alle benodigde Python-pakketten.

### Technologieën
- **Flask**: Voor het draaien van de webserver.
- **RSS-feeds**: Voor het verzamelen van nieuwsartikelen.
- **BeautifulSoup**: Voor het scrapen van volledige artikelen.
- **Cohere AI API**: Voor het genereren van samenvattingen en inzichten.

### Ethische Overwegingen

Bij de ontwikkeling van dit project hebben we expliciet rekening gehouden met enkele belangrijke ethische kwesties die naar voren komen bij het gebruik van nieuwsautomatisering en generative AI:

#### Accuraatheid van Informatie:

We begrijpen dat AI-modellen zoals Cohere krachtige hulpmiddelen zijn voor het samenvatten van nieuws, maar ze kunnen soms onnauwkeurigheden bevatten. Om dit te beperken, hebben we ervoor gezorgd dat de volledige tekst van het originele artikel beschikbaar blijft naast de AI-gegenereerde samenvatting, zodat gebruikers de originele bron altijd kunnen raadplegen. We moedigen lezers aan om AI-output kritisch te beoordelen en niet blindelings te vertrouwen.

#### Copyright en Bronvermelding:

We maken gebruik van openbare RSS-feeds en geven altijd de originele auteur en bron weer bij elk artikel. De bron wordt expliciet vermeld in de metadata van elk gegenereerd HTML-bestand en in de weergegeven artikelen op de website. Dit zorgt ervoor dat we voldoen aan copyrightregels en de auteurs de eer krijgen die hen toekomt.

#### Transparantie van AI-gebruik:

Het gebruik van AI wordt in alle gegenereerde artikelen expliciet vermeld. Lezers worden geïnformeerd dat bepaalde delen van de inhoud, zoals samenvattingen en analyses, door een AI zijn gegenereerd. Dit bevordert transparantie en zorgt ervoor dat gebruikers weten dat er geen menselijke journalist de samenvatting heeft geschreven.

### Auteurs
Dit project is gemaakt door Goudantov Bers en Van Camp Loïc.