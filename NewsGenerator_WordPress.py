import os
import requests
import xml.etree.ElementTree as ET
from cohere import Client
from bs4 import BeautifulSoup
import time
from requests.auth import HTTPBasicAuth

INFO = "Nieuws Generator, gemaakt door: \nGoudantov Bers, Van Camp Loïc\n"
print(INFO)

# Cohere API key
cohere_client = Client('VhaJwiI2QQGmEIYHvE0L5h3aHuu9pftsXt5BQg6D') # maandelijkse limiet bereikt :/

# WordPress API details
WP_URL = "https://yapnews.meubel-centrum.be/wp-json/wp/v2/posts"  # Wordpress url
WP_MEDIA_URL = "https://yapnews.meubel-centrum.be/wp-json/wp/v2/media"  # Media endpoint
WP_USER = "yapperyap"
WP_PASSWORD = "EZFN vKP0 AbV3 PMbI As4T vP2o"  # Applicatie password

# Functie om titel te genereren
def generate_sensational_title(original_title):
    prompt = f"Transformeer de volgende titel in een sensationele titel: '{original_title}'"
    response = cohere_client.generate(
        prompt=prompt,
        model="command-nightly",
        max_tokens=50,
        temperature=0.5,
        stop_sequences=["\n"],
    )
    return response.generations[0].text.strip() if response.generations else original_title

# Functie om RSS op te halen
def fetch_and_parse_rss_feed(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  
    root = ET.fromstring(response.content)
    articles = []

    for item in root.findall(".//item"):
        title = item.find("title").text
        link = item.find("link").text
        description = item.find("description").text
        publication_date = item.find("pubDate").text
        creator = item.find("{http://purl.org/dc/elements/1.1/}creator").text

        article = {
            "title": title,
            "link": link,
            "description": description,
            "pub_date": publication_date,
            "creator": creator + ", Copyright © Reuters ",
            "image_url": None,
        }
        articles.append(article)

    return articles

# Functie om volledige artikel te webcrawlen
def fetch_full_article(link, retries=2, delay=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(retries):
        try:
            print(f"Fetching article from {link}, attempt {attempt + 1}/{retries}")
            response = requests.get(link, headers=headers, timeout=30)  
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.find('div', {'id': 'main-content'})  

            if content:
                img_tag = content.find('img', {'decoding': 'async'})
                image_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else None
                return content.get_text(separator=' ', strip=True), image_url
            else:
                print("Content not found. Returning fallback content.")
                return "Inhoud niet gevonden.", None

        except (requests.exceptions.HTTPError, requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(f"Error fetching article at {link}: {str(e)}")
            if attempt < retries - 1:
                print(f"Retrying... ({attempt + 1}/{retries})")
                time.sleep(delay * (attempt + 1))  
            else:
                return f"Failed to fetch after {retries} attempts.", None

    return "Unknown error occurred.", None

# Function om foto van het nieuwsbron op te halen
def upload_image_to_wordpress(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()  
        
        media_data = {
            'file': response.content,
            'caption': 'Image from article'
        }
        headers = {
            'Content-Disposition': f'attachment; filename="{os.path.basename(image_url)}"',
            'Content-Type': response.headers.get('Content-Type', 'application/octet-stream')
        }

        media_response = requests.post(
            WP_MEDIA_URL,
            auth=HTTPBasicAuth(WP_USER, WP_PASSWORD),
            headers=headers,
            files=media_data
        )

        if media_response.status_code == 201:
            return media_response.json().get('id')  
        else:
            print(f"Fout bij het uploaden van afbeelding: {media_response.text}")
            print(f"Status code: {media_response.status_code}, Headers: {media_response.headers}")
            return None
    except Exception as e:
        print(f"Fout bij het ophalen van afbeelding: {str(e)}")
        return None

# Functie om het artikel te ontbinden en doorgeven aan het LLM om zo tot een nieuwe artikel te genereren
def process_articles(articles, number_of_articles):
    processed_articles = []
    
    for i, article in enumerate(articles[:number_of_articles]):  
        print(f"Verwerken artikel {i + 1}: {article['link']}")

        start_time = time.time()  
        full_text, image_url = fetch_full_article(article['link'])

        # titel generatie
        sensational_title = generate_sensational_title(article['title'])
        article['title'] = sensational_title

        prompt = (
            f"Title: {article['title']}\n"
            f"Description: {article['description']}\n"
            f"Author: {article['creator']}\n"
            f"Publication Date: {article['pub_date']}\n\n"
            f"Full Article: {full_text}\n\n"
            "Vat dit artikel gedetailleerd samen en genereer een nieuwe artikel terug. Geef inzichten in de mogelijke economische, politieke en wereldwijde implicaties in ten minste 5 regels tot maximum 20 regels."
        )

        # Gebruik Cohere API om calls uit te voeren
        ai_response = cohere_client.generate(
            prompt=prompt,
            model="command-nightly",
            max_tokens=1500,
            temperature=0.5,
            stop_sequences=["\n\n"],
        )
        
        # Check indien de AI output deftig output geeft
        if ai_response.generations and ai_response.generations[0].text.strip():
            article['ai_output'] = ai_response.generations[0].text.strip()
        else:
            article['ai_output'] = "Geen inhoud gegenereerd."

        article['image_url'] = image_url

        processed_articles.append(article)

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Artikel {i + 1} gegenereerd in {elapsed_time:.2f} seconden.")

    return processed_articles

# Functie om de verwerkte gegevens up te loaden naar de wordpress website
def post_to_wordpress(articles):
    for article in articles:
        media_id = None
        if article['image_url']:
            media_id = upload_image_to_wordpress(article['image_url'])

        # Bereid data voor publishen
        data = {
            'title': article['title'],
            'content': f"<h2>{article['title']}</h2><p><strong>Auteur:</strong> {article['creator']}</p><p><strong>Publicatie Datum:</strong> {article['pub_date']}</p><p>{article['ai_output']}</p><p>Origineel Artikel: <a href='{article['link']}'>Link</a></p>",
            'status': 'publish',  
            'featured_media': media_id,  
        }

        # Post naar Wordpress
        response = requests.post(
            WP_URL,
            auth=HTTPBasicAuth(WP_USER, WP_PASSWORD),
            json=data
        )

        if response.status_code == 201:
            print(f"Artikel '{article['title']}' succesvol gepubliceerd op WordPress.")

# Applicatie gebruik
def main():
    rss_feed_url = "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best"  # Reuters RSS feed
    
    # Prompt de gebruiker voor het aantal artikels
    try:
        number_of_articles = int(input("Hoeveel artikels wilt u verwerken? Voer een nummer in: "))
    except ValueError:
        print("Ongeldige invoer. Het aantal wordt standaard ingesteld op 5.")
        number_of_articles = 5  

    # Fetch RSS feed en verwerk artikels
    articles = fetch_and_parse_rss_feed(rss_feed_url)
    processed_articles = process_articles(articles, number_of_articles)

    # Post artikels op WordPress
    post_to_wordpress(processed_articles)

if __name__ == "__main__":
    main()