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
cohere_client = Client('VhaJwiI2QQGmEIYHvE0L5h3aHuu9pftsXt5BQg6D')

# WordPress API details
WP_URL = "https://yapnews.meubel-centrum.be/wp-json/wp/v2/posts"  # Change to your WordPress site URL
WP_MEDIA_URL = "https://yapnews.meubel-centrum.be/wp-json/wp/v2/media"  # Media endpoint
WP_USER = "yapperyap"
WP_PASSWORD = "EZFN vKP0 AbV3 PMbI As4T vP2o"  # Application password

# Function to generate a sensational title
def generate_sensational_title(original_title):
    # Use Cohere AI to generate a sensational title
    prompt = f"Transformeer de volgende titel in een sensationele titel: '{original_title}'"
    response = cohere_client.generate(
        prompt=prompt,
        model="command-nightly",
        max_tokens=50,
        temperature=0.5,
        stop_sequences=["\n"],
    )
    return response.generations[0].text.strip() if response.generations else original_title

# Function to fetch and parse RSS feed
# Function to fetch and parse RSS feed
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
        
        # Extract sectors information from item description
        sectors = extract_sectors_from_description(description)  # New helper function

        article = {
            "title": title,
            "link": link,
            "description": description,
            "pub_date": publication_date,
            "creator": creator + ", Copyright © Reuters ",
            "image_url": None,
            "category": sectors  # Store sectors in category field
        }
        articles.append(article)

    return articles

# Helper function to extract sectors from the description
def extract_sectors_from_description(description):
    # Implement a method to extract sectors from the description
    # This is a placeholder and may need to be customized depending on the description format
    if "Sectors:" in description:
        start_index = description.index("Sectors:") + len("Sectors:")
        end_index = description.find("\n", start_index)  # Find the next line break
        sectors = description[start_index:end_index].strip()  # Get sectors and trim whitespace
        return sectors.split(", ")  # Split into a list if multiple sectors
    return None

# Function to fetch the full article content
# Function to fetch the full article content with increased timeout and improved retry logic
def fetch_full_article(link, retries=2, delay=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(retries):
        try:
            print(f"Fetching article from {link}, attempt {attempt + 1}/{retries}")
            response = requests.get(link, headers=headers, timeout=30)  # Increased timeout
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.find('div', {'id': 'main-content'})  # Change to use id instead of class

            if content:
                img_tag = content.find('img', {'decoding': 'async'})
                image_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else None
                return content.get_text(separator=' ', strip=True), image_url
            else:
                print("Content not found. Returning fallback content.")
                return "Inhoud niet gevonden.", None  # Return default text

        except (requests.exceptions.HTTPError, requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(f"Error fetching article at {link}: {str(e)}")
            if attempt < retries - 1:
                print(f"Retrying... ({attempt + 1}/{retries})")
                time.sleep(delay * (attempt + 1))  # Increased delay for retries
            else:
                return f"Failed to fetch after {retries} attempts.", None

    return "Unknown error occurred.", None


# Function to upload image to WordPress and get media ID
def upload_image_to_wordpress(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()  # Ensure the image URL is valid
        
        media_data = {
            'file': response.content,
            'caption': 'Image from article'
        }
        headers = {
            'Content-Disposition': f'attachment; filename="{os.path.basename(image_url)}"',
            'Content-Type': response.headers.get('Content-Type', 'application/octet-stream')  # Ensure correct content type
        }

        media_response = requests.post(
            WP_MEDIA_URL,
            auth=HTTPBasicAuth(WP_USER, WP_PASSWORD),
            headers=headers,
            files=media_data
        )

        if media_response.status_code == 201:
            return media_response.json().get('id')  # Get the media ID
        else:
            print(f"Fout bij het uploaden van afbeelding: {media_response.text}")
            print(f"Status code: {media_response.status_code}, Headers: {media_response.headers}")
            return None
    except Exception as e:
        print(f"Fout bij het ophalen van afbeelding: {str(e)}")
        return None

# Function to extract category from the article URL
def extract_category_from_url(url):
    # Assuming the category can be derived from the URL path
    category = url.split('/')[4]  # Adjust this index according to your URL structure
    return category

# Function to process articles and add summaries
def process_articles(articles, number_of_articles):
    processed_articles = []
    
    for i, article in enumerate(articles[:number_of_articles]):  # User-defined number of articles
        print(f"Verwerken artikel {i + 1}: {article['link']}")

        start_time = time.time()  # Start time for the article
        full_text, image_url = fetch_full_article(article['link'])

        # Generate a sensational title
        sensational_title = generate_sensational_title(article['title'])
        article['title'] = sensational_title

        # Extract category from the URL
        article['category'] = extract_category_from_url(article['link'])

        prompt = (
            f"Title: {article['title']}\n"
            f"Description: {article['description']}\n"
            f"Author: {article['creator']}\n"
            f"Publication Date: {article['pub_date']}\n\n"
            f"Full Article: {full_text}\n\n"
            "Vat dit artikel gedetailleerd samen en genereer een nieuwe artikel terug. Geef inzichten in de mogelijke economische, politieke en wereldwijde implicaties in ten minste 5 regels tot maximum 20 regels."
        )

        # Use Cohere API to generate the article analysis
        ai_response = cohere_client.generate(
            prompt=prompt,
            model="command-nightly",
            max_tokens=1500,
            temperature=0.5,
            stop_sequences=["\n\n"],
        )
        
        # Check if the AI has generated valid content
        if ai_response.generations and ai_response.generations[0].text.strip():
            article['ai_output'] = ai_response.generations[0].text.strip()
        else:
            article['ai_output'] = "Geen inhoud gegenereerd."

        # Set the image URL to the article dictionary
        article['image_url'] = image_url

        processed_articles.append(article)

        # Calculate the time for generating the article
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Artikel {i + 1} gegenereerd in {elapsed_time:.2f} seconden.")

    return processed_articles

# Function to fetch existing tags from WordPress
def fetch_existing_tags():
    response = requests.get(
        WP_URL.replace('/posts', '/tags'),  # Adjust endpoint to fetch tags
        auth=HTTPBasicAuth(WP_USER, WP_PASSWORD)
    )
    if response.status_code == 200:
        return {tag['name']: tag['id'] for tag in response.json()}  # Create a dictionary of tag names and IDs
    else:
        print(f"Fout bij het ophalen van tags: {response.text}")
        return {}

# Function to create a new tag in WordPress and return its ID
def create_tag(tag_name):
    data = {'name': tag_name}
    response = requests.post(
        WP_URL.replace('/posts', '/tags'),  # Adjust endpoint to create a new tag
        auth=HTTPBasicAuth(WP_USER, WP_PASSWORD),
        json=data
    )
    if response.status_code == 201:
        return response.json().get('id')  # Return the new tag ID
    else:
        print(f"Fout bij het aanmaken van tag '{tag_name}': {response.text}")
        return None

# Function to post articles to WordPress
def post_to_wordpress(articles):
    existing_tags = fetch_existing_tags()  # Get existing tags at the start
    for article in articles:
        media_id = None
        if article['image_url']:
            media_id = upload_image_to_wordpress(article['image_url'])

        # Check if the author tag exists, create if not
        author_tag_name = article['creator']
        tag_id = existing_tags.get(author_tag_name)

        if not tag_id:  # If tag does not exist, create it
            tag_id = create_tag(author_tag_name)

        # Prepare data for WordPress
        data = {
            'title': article['title'],
            'content': f"<h2>{article['title']}</h2><p><strong>Auteur:</strong> {article['creator']}</p><p><strong>Publicatie Datum:</strong> {article['pub_date']}</p><p><strong>Categorie:</strong> {article['category']}</p><p>{article['ai_output']}</p><p>Origineel Artikel: <a href='{article['link']}'>Link</a></p>",
            'status': 'publish',  # Publish immediately, can also use 'draft' to save as draft
            # WIP 'featured_media': media_id,  # Use the media ID if available
            # WIP 'tags': [tag_id] if tag_id else [],  # Use the tag ID
            'categories': article['category']
        }

        # Post to WordPress
        response = requests.post(
            WP_URL,
            auth=HTTPBasicAuth(WP_USER, WP_PASSWORD),
            json=data
        )

        if response.status_code == 201:
            print(f"Artikel '{article['title']}' succesvol gepubliceerd op WordPress.")
        else:
            print(f"Fout bij het publiceren van artikel '{article['title']}': {response.text}")

# Main function to create and publish articles
def create_and_publish_articles():
    rss_url = "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best"
    
    articles = []  # Initialize an empty list for articles
    
    articles = fetch_and_parse_rss_feed(rss_url)

    # Ask the user for the number of articles to generate
    try:
        number_of_articles = int(input("Hoeveel artikelen wilt u genereren? (Waarschuwing hoe meer artikelen, hoe langer het duurt.): "))
    except ValueError:
        print("Ongeldige invoer, standaard naar 6 artikelen.")
        number_of_articles = 6

    start_total_time = time.time()  # Start the total time
    processed_articles = process_articles(articles, number_of_articles)

    # Publish articles to WordPress
    post_to_wordpress(processed_articles)
    
    total_time = time.time() - start_total_time  # Total time for article generation
    print(f"Totaal tijd voor het genereren en publiceren van {number_of_articles} artikelen: {total_time:.2f} seconden")

if __name__ == '__main__':
    print("Start het genereren en publiceren van artikelen...")
    create_and_publish_articles()