import os
import requests
import xml.etree.ElementTree as ET
from flask import Flask, render_template
from cohere import Client

# Initialize the Flask app
app = Flask(__name__)

# Set your Cohere API key
cohere_client = Client('VhaJwiI2QQGmEIYHvE0L5h3aHuu9pftsXt5BQg6D')  # Replace with your actual API key

def fetch_and_parse_rss_feed(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an error for bad responses
    root = ET.fromstring(response.content)
    articles = []

    # Fetch only the latest items from the RSS feed
    for item in root.findall(".//item"):
        title = item.find("title").text
        link = item.find("link").text
        description = item.find("description").text
        pub_date = item.find("pubDate").text
        creator = item.find("{http://purl.org/dc/elements/1.1/}creator").text
        image_url = item.find("{http://media.org/}content").get('url') if item.find("{http://media.org/}content") is not None else ''

        article = {
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "creator": creator,
            "image_url": image_url
        }
        articles.append(article)

    return articles

# Function to fetch the full article's content
def fetch_full_article(link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(link, headers=headers)
    response.raise_for_status()  # Raise an error for bad responses
    return response.text

def process_articles(articles):
    processed_articles = []
    
    # Process only the most recent article
    if articles:  # Check if there are any articles
        latest_article = articles[0]  # Assuming articles are sorted with the most recent first
        print(f"Processing full article from: {latest_article['link']}")
        full_text = fetch_full_article(latest_article['link'])

        # Use Cohere API to rewrite and translate the article to Dutch
        ai_response = cohere_client.generate(
            prompt=full_text + "\nRewrite and analyse the article more in detail, finally translate the resulted output to Dutch:",
            model="command-nightly",
            num_generations=1,
            max_tokens=800,
            temperature=0.5
        )
        latest_article['ai_output'] = ai_response.generations[0].text.strip()
        processed_articles.append(latest_article)
    
    return processed_articles

# Function to save the articles as HTML
def save_article_to_html(articles):
    # Clean up old articles
    if not os.path.exists('articles'):
        os.makedirs('articles')
    else:
        for file in os.listdir('articles'):
            os.remove(os.path.join('articles', file))

    for article in articles:
        # Create the file path manually
        article_filename = f"{article['title'].replace(' ', '_').replace('/', '_')}.html"  # Replace slashes to avoid issues
        article['file_path'] = f"articles/{article_filename}"

        with app.app_context():  # Ensure app context
            html_content = render_template('article_template.html', article=article)  # Use correct template
            file_path = f'articles/{article_filename}'
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f'Saved article to {file_path}')

@app.route('/')
def homepage():
    articles = []  # Initialize an empty list

    # Read articles from the 'articles' directory
    if os.path.exists('articles'):
        for filename in os.listdir('articles'):
            if filename.endswith('.html'):
                title = filename.replace('.html', '').replace('_', ' ')
                articles.append({
                    'title': title,
                    'file_path': filename  # Store the relative path
                })

    return render_template('homepage_template.html', articles=articles)  # Use homepage template

@app.route('/article/<filename>')
def article(filename):
    file_path = f'articles/{filename}'
    
    # Ensure the file exists
    if not os.path.exists(file_path):
        return "Article not found", 404
    
    # Read the article's content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create an article data dictionary
    article_data = {
        'title': filename.replace('.html', '').replace('_', ' '),
        'content': content  # This will be the HTML content of the article
    }

    # You may need to parse the content to extract creator, pub_date, etc., if they are needed.
    # Alternatively, you can keep the HTML content as it is and render it directly in your template.

    # Render the content with a specific template
    return render_template('article_template.html', article=article_data)  # Pass structured article data


# Main function to create and serve articles
def create_and_serve_articles():
    rss_url = "https://www.reutersagency.com/feed/?best-sectors=economy&post_type=best"
    articles = fetch_and_parse_rss_feed(rss_url)
    processed_articles = process_articles(articles)
    save_article_to_html(processed_articles)
    print("Starting the Flask web server...")
    app.run(debug=True)

if __name__ == '__main__':
    create_and_serve_articles()
