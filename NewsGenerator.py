import requests
import xml.etree.ElementTree as ET
from flask import Flask, render_template, jsonify, Response
from cohere import Client
from playwright.async_api import async_playwright
import asyncio

# Initialize the Flask app
app = Flask(__name__)

# Set your Cohere API key
cohere_client = Client('VhaJwiI2QQGmEIYHvE0L5h3aHuu9pftsXt5BQg6D')

# Global variable to store articles
articles_data = []

# Function to fetch the full content of an article using Playwright
async def fetch_full_article(link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(link)
        await page.wait_for_timeout(1000)  # Wait for content to load

        # Extract relevant text (e.g., paragraphs and headlines)
        content = await page.query_selector_all('p, h1, h2, h3')
        full_text = "\n".join([await p.inner_text() for p in content])

        await browser.close()  # Close the browser
        return full_text

# Function to fetch and parse the RSS feed
def fetch_and_parse_rss_feed(url):
    response = requests.get(url)
    root = ET.fromstring(response.content)
    articles = []

    # Assuming you want to get only the latest article
    item = root.find(".//item")  # Get the first item (latest article)
    if item is not None:
        title = item.find("title").text
        link = item.find("link").text
        description = item.find("description").text
        pub_date = item.find("pubDate").text
        creator = item.find("{http://purl.org/dc/elements/1.1/}creator").text + " (New York Times, NYT)"
        
        # Attempt to find an image URL
        image_url = item.find("{http://media.org/}thumbnail").get('url') if item.find("{http://media.org/}thumbnail") is not None else ''

        article = {
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "creator": creator,
            "full_text": "",  # Will be filled later
            "image_url": image_url  # Add image URL to article
        }
        articles.append(article)

    return articles

# Function to process articles
async def process_articles(articles):
    processed_articles = []
    for article in articles:
        # Fetch full article content
        article['full_text'] = await fetch_full_article(article['link'])
        processed_articles.append(article)
    return processed_articles

# Function to stream rewrite using Cohere API
async def stream_rewrite(article_id):
    article = articles_data[article_id]  # Get the article
    full_text = article['full_text']

    # Configure your parameters here
    response = cohere_client.generate_stream(
        prompt=full_text,
        model="command-nightly",  # Specify your model
        num_generations=1,
        max_tokens=200,  # Increased tokens for a better rewrite
        temperature=0.7,  # Adjusted for more coherent output
    )

    for chunk in response:
        yield f"data: {chunk.text.strip()}\n\n"  # Send the generated text

@app.route('/')
def homepage():
    return render_template('index.html')

@app.route('/fetch_articles')
async def fetch_articles():
    # Fetch and parse RSS feed
    rss_url = "https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml"
    global articles_data
    articles = fetch_and_parse_rss_feed(rss_url)
    articles_data = await process_articles(articles)  # Store processed articles

    return jsonify(articles=articles_data)

@app.route('/stream_rewrite/<int:article_id>')
def stream_rewrite_route(article_id):
    return Response(run_async(stream_rewrite, article_id), content_type='text/event-stream')

# Helper to run async functions
def run_async(func, *args):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(func(*args))

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
