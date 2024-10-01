import os
import requests
import xml.etree.ElementTree as ET
from flask import Flask, render_template
from cohere import Client
from bs4 import BeautifulSoup  # Import BeautifulSoup
import time

INFO = "Nieuws Generator, gemaakt door: \nGoudantov Bers, Van Camp Loïc\n"
print(INFO)

# Initialiseer de Flask-app
app = Flask(__name__)

# Cohere API-sleutel in
cohere_client = Client('VhaJwiI2QQGmEIYHvE0L5h3aHuu9pftsXt5BQg6D')  # Vervang door je eigen (eventueel)

# Functie om een RSS-feed op te halen en te parseren
def fetch_and_parse_rss_feed(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Geeft een foutmelding bij onjuiste respons
    root = ET.fromstring(response.content)
    artikelen = []

    # Haal alleen de nieuwste items uit de RSS-feed
    for item in root.findall(".//item"):
        titel = item.find("title").text
        link = item.find("link").text
        beschrijving = item.find("description").text
        publicatie_datum = item.find("pubDate").text
        auteur = item.find("{http://purl.org/dc/elements/1.1/}creator").text
        afbeelding_url = item.find("{http://media.org/}content").get('url') if item.find("{http://media.org/}content") is not None else ''

        artikel = {
            "title": titel,
            "link": link,
            "description": beschrijving,
            "pub_date": publicatie_datum,
            "creator": auteur + ", Copyright © New York Times ",
            "image_url": afbeelding_url
        }
        artikelen.append(artikel)

    return artikelen


# Functie om de volledige inhoud van een artikel op te halen
def fetch_full_article(link, retries=3, delay=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(link, headers=headers, timeout=10)  # Set a timeout to avoid long waits
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Probeer de hoofdinhoud van het artikel te halen op basis van de structuur van de website
            content = soup.find('div', {'class': 'article-body'}) or soup.find('article')

            if content:
                return content.get_text(separator=' ', strip=True)
            
            # optie: retourneer alle paragrafen als de structuur niet overeenkomt
            paragrafen = soup.find_all('p')
            if paragrafen:
                return ' '.join([p.get_text(strip=True) for p in paragrafen if p.get_text(strip=True)])

            return "Geen artikelinhoud gevonden."

        except (requests.exceptions.HTTPError, requests.exceptions.Timeout) as e:
            print(f"Error fetching article at {link}: {str(e)}")
            if attempt < retries - 1:  # If retries are left, wait and retry
                print(f"Retrying... ({attempt + 1}/{retries})")
                time.sleep(delay)
            else:
                return f"Kon het artikel niet ophalen na {retries} pogingen."

    return "Onbekende fout opgetreden bij het ophalen van het artikel."


# Verwerkt artikelen en voegt samenvattingen toe
def process_articles(artikelen):
    verwerkte_artikelen = []
    
    for i, artikel in enumerate(artikelen[:6]):  # Update om meer artikelen te verwerken indien gewenst
        print(f"Verwerken artikel {i + 1}: {artikel['link']}")
        volledige_tekst = fetch_full_article(artikel['link'])

        # Bouw een prompt op basis van de titel en beschrijving van het artikel
        prompt = (
            f"Title: {artikel['title']}\n"
            f"Description: {artikel['description']}\n\n"
            f"Full Article: {volledige_tekst}\n\n"
            "Vat dit artikel gedetailleerd samen en geef inzichten in de mogelijke economische, politieke en wereldwijde implicaties in ten minste 10 regels."
        )

        # Gebruik Cohere API om de artikelanalyse te genereren
        ai_response = cohere_client.generate(
            prompt=prompt,
            model="command-nightly",
            max_tokens=1500,
            temperature=0.5,
            stop_sequences=["\n\n"],
        )
        
        # Controleer of de AI geldige inhoud heeft gegenereerd
        if ai_response.generations and ai_response.generations[0].text.strip():
            artikel['ai_output'] = ai_response.generations[0].text.strip()
        else:
            artikel['ai_output'] = "Geen inhoud gegenereerd."

        verwerkte_artikelen.append(artikel)
        
    return verwerkte_artikelen


# Functie om artikelen op te slaan als HTML
def save_article_to_html(artikelen):
    if not os.path.exists('artikelen'):
        os.makedirs('artikelen')
    else:
        for file in os.listdir('artikelen'):
            os.remove(os.path.join('artikelen', file))

    for artikel in artikelen:
        artikel_filename = f"{artikel['title'].replace(' ', '_').replace('/', '_')}.html"
        artikel['file_path'] = f"artikelen/{artikel_filename}"

        with app.app_context():
            html_content = render_template('article_template.html', article=artikel)
            file_path = f'artikelen/{artikel_filename}'
            with open(file_path, 'w', encoding='utf-8') as f:
                # Voeg metadata toe in HTML-opmerkingen
                metadata = f'<!-- Auteur: {artikel["creator"]} -->\n'
                metadata += f'<!-- Publicatiedatum: {artikel["pub_date"]} -->\n'
                f.write(metadata + html_content)
            print(f'Artikel opgeslagen in {file_path}')


# Hoofdfunctie om artikelen te maken en de server te starten
def create_and_serve_articles():
    # RSS-feed van Reuters Agency
    rss_url = "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best"
    
    artikelen = []  # Initialiseer een lege lijst voor artikelen
    
    # Check indien er bestaande artikelen zijn
    if os.path.exists('artikelen'):
        existing_files = [f for f in os.listdir('artikelen') if f.endswith('.html')]
        if existing_files:
            # Prompt de gebruiker om bestaande artikelen te gebruiken of nieuwe te verkrijgen
            serve_existing = input("Er zijn bestaande artikelen gevonden. Wilt u de Flask-server starten op deze artikelen? (ja/nee): ").strip().lower()
            if serve_existing == 'ja':
                print("Server wordt gestart op bestaande artikelen...")
                return  # Stop de server en gebruik bestaande artikelen
            else:
                print("Nieuwe artikelen worden opgehaald...")
    
    artikelen = fetch_and_parse_rss_feed(rss_url)
    verwerkte_artikelen = process_articles(artikelen)
    save_article_to_html(verwerkte_artikelen)


@app.route('/')
def homepage():
    artikelen = []  # Initialiseert een lege lijst

    # Lees artikelen uit de 'artikelen' directory
    if os.path.exists('artikelen'):
        for filename in os.listdir('artikelen'):
            if filename.endswith('.html'):
                titel = filename.replace('.html', '').replace('_', ' ')
                artikelen.append({
                    'title': titel,
                    'file_path': filename  # Sla het pad op
                })

    return render_template('homepage_template.html', artikelen=artikelen)  # Gebruik homepage template


@app.route('/artikel/<filename>')
def article(filename):
    file_path = f'artikelen/{filename}'

    if not os.path.exists(file_path):
        return "Artikel niet gevonden", 404

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Haal metadata uit de opmerkingen
    try:
        auteur = content.split("<!-- Auteur: ")[1].split(" -->")[0] if "<!-- Auteur: " in content else "Onbekend"
        publicatie_datum = content.split("<!-- Publicatiedatum: ")[1].split(" -->")[0] if "<!-- Publicatiedatum: " in content else "Onbekend"
        link = content.split('<a href="')[1].split('"')[0] if '<a href="' in content else "Geen link"

        # Haal de hoofdinhoud van het artikel op
        artikel_inhoud = content.split('<div class="content">')[1].split('</div>')[0]

        # Probeer de AI-samenvatting te uithalen
        if '<h2>Summary</h2>' in content:
            ai_output = content.split('<h2>Summary</h2>')[1].split('</p>')[0].replace('</p>', '').strip()
        elif '<h2>Summary:</h2>' in content:
            ai_output = content.split('<h2>Summary:</h2>')[1].split('</p>')[0].replace('</p>', '').strip()
        else:
            ai_output = "Geen samenvatting gevonden."
        
    except IndexError:
        return "Fout bij het verwerken van het artikelbestand", 500

    # Bereid de gegevens voor om weer te geven
    artikel_data = {
        'title': filename.replace('.html', '').replace('_', ' '),
        'content': artikel_inhoud,
        'creator': auteur,
        'pub_date': publicatie_datum,
        'link': link,
        'ai_output': ai_output
    }

    return render_template('article_template.html', article=artikel_data)


if __name__ == '__main__':
    print("Starten van de Flask webserver...")
    create_and_serve_articles()
    app.run(debug=False)  # Start de Flask-app