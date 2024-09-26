import requests
import xml.etree.ElementTree as ET
from flask import Flask, render_template
from cohere import Client
from playwright.sync_api import sync_playwright  # Changed to synchronous API
import os

# Initialize the Flask app
app = Flask(__name__)

# Set your Cohere API key
cohere_client = Client('VhaJwiI2QQGmEIYHvE0L5h3aHuu9pftsXt5BQg6D')

# Function to fetch the full content of an article using Playwright
def fetch_full_article(link):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(link)
        page.wait_for_timeout(1000)  # Wait for content to load

        content = page.query_selector_all('p, h1, h2, h3')
        full_text = "\n".join([p.inner_text() for p in content])

        browser.close()
        return full_text

# Function to fetch and parse the RSS feed
def fetch_and_parse_rss_feed(url):
    response = requests.get(url)
    root = ET.fromstring(response.content)
    articles = []

    item = root.find(".//item")  
    if item is not None:
        title = item.find("title").text
        link = item.find("link").text
        description = item.find("description").text
        pub_date = item.find("pubDate").text
        creator = item.find("{http://purl.org/dc/elements/1.1/}creator").text + " (New York Times, NYT)"
        image_url = item.find("{http://media.org/}thumbnail").get('url') if item.find("{http://media.org/}thumbnail") is not None else ''

        article = {
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "creator": creator,
            "full_text": "",
            "image_url": image_url
        }
        articles.append(article)

    return articles

# Function to process articles
def process_articles(articles):
    processed_articles = []
    for article in articles:
        article['full_text'] = fetch_full_article(article['link'])

        ai_response = cohere_client.generate(
            prompt=article['full_text'] + ", Rewrite this article to your own but translate it to Dutch",
            model="command-nightly",
            num_generations=1,
            max_tokens=1000,
            temperature=0.7
        )
        article['ai_output'] = ai_response.generations[0].text.strip()
        processed_articles.append(article)
    return processed_articles

# Function to save articles as HTML
def save_article_to_html(articles):
    if not os.path.exists('articles'):
        os.makedirs('articles')

    for article in articles:
        with app.app_context():  # Ensure app context
            html_content = render_template('article_list.html', articles=[article])
            file_path = f'articles/{article["title"].replace(" ", "_")}.html'
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f'Saved article to {file_path}')

@app.route('/')
def homepage():
    articles = []
    try:
        articles = os.listdir('articles')
    except FileNotFoundError:
        pass  

    if not articles:
        return "<h1>No articles available. Please create an article first.</h1>"

    return render_template('article_list.html', articles=articles)

# Function to run the Flask app
def run_flask():
    app.run(debug=True, threaded=True)

def create_articles():  # Make this synchronous
    print("Fetching articles...")
    rss_url = "https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml"
    articles = fetch_and_parse_rss_feed(rss_url)
    articles_data = process_articles(articles)  # No need to run async function
    save_article_to_html(articles_data)  

def main_menu():
    while True:
        print("\n=== Menu ===")
        print("1. Create Article")
        print("2. Run Web Server")
        print("3. Exit")
        choice = input("Select an option: ")

        if choice == '1':
            create_articles()  # Call the sync function to create articles
        elif choice == '2':
            if os.path.exists('articles') and os.listdir('articles'):
                print("Starting the Flask web server...")
                run_flask()
            else:
                print("No articles exist. Please create an article first.")
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main_menu()