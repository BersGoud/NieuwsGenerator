import os
import requests
import xml.etree.ElementTree as ET
from flask import Flask, render_template
from cohere import Client
from bs4 import BeautifulSoup  # Import BeautifulSoup

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
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Try to fetch the main article content based on the site's structure (adjust selectors as necessary)
    content = soup.find('div', {'class': 'article-body'}) or soup.find('article')

    if content:
        return content.get_text(separator=' ', strip=True)
    
    # Fallback: Return all paragraphs if the structure doesn't match
    paragraphs = soup.find_all('p')
    if paragraphs:
        return ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

    return "No article content found."


def process_articles(articles):
    processed_articles = []
    
    for i, article in enumerate(articles[:6]):  # Update to process more if desired
        print(f"Processing article {i + 1}: {article['link']}")
        full_text = fetch_full_article(article['link'])

        # Construct a prompt based on the actual article's title and description
        prompt = (
            f"Title: {article['title']}\n"
            f"Description: {article['description']}\n\n"
            f"Full Article: {full_text}\n\n"
            "Please summarize this article in detail and provide insights on potential economic, political, and global implications in atleast 10 lines."
        )

        # Use Cohere API to generate the article analysis
        ai_response = cohere_client.generate(
            prompt=prompt,
            model="command-nightly",
            max_tokens=1500,
            temperature=0.5,
            stop_sequences=["\n\n"],
        )
        
        # Check if the AI generated valid content
        if ai_response.generations and ai_response.generations[0].text.strip():
            article['ai_output'] = ai_response.generations[0].text.strip()
        else:
            article['ai_output'] = "No content generated."

        processed_articles.append(article)
        
    return processed_articles


# Function to save the articles as HTML
def save_article_to_html(articles):
    if not os.path.exists('articles'):
        os.makedirs('articles')
    else:
        for file in os.listdir('articles'):
            os.remove(os.path.join('articles', file))

    for article in articles:
        article_filename = f"{article['title'].replace(' ', '_').replace('/', '_')}.html"
        article['file_path'] = f"articles/{article_filename}"

        with app.app_context():
            html_content = render_template('article_template.html', article=article)
            file_path = f'articles/{article_filename}'
            with open(file_path, 'w', encoding='utf-8') as f:
                # Include metadata in HTML comments
                metadata = f'<!-- Author: {article["creator"]} -->\n'
                metadata += f'<!-- Pub Date: {article["pub_date"]} -->\n'
                f.write(metadata + html_content)
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

    if not os.path.exists(file_path):
        return "Article not found", 404

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract metadata from comments
    try:
        author = content.split("<!-- Author: ")[1].split(" -->")[0] if "<!-- Author: " in content else "Unknown"
        pub_date = content.split("<!-- Pub Date: ")[1].split(" -->")[0] if "<!-- Pub Date: " in content else "Unknown"
        link = content.split('<a href="')[1].split('"')[0] if '<a href="' in content else "No link"

        # Extract the main content of the article
        article_content = content.split('<div class="content">')[1].split('</div>')[0]

        # Try different ways to extract the AI summary
        if '<h2>Summary</h2>' in content:
            ai_output = content.split('<h2>Summary</h2>')[1].split('</p>')[0].replace('</p>', '').strip()
        elif '<h2>Samenvatting:</h2>' in content:
            ai_output = content.split('<h2>Samenvatting:</h2>')[1].split('</p>')[0].replace('</p>', '').strip()
        else:
            ai_output = "No summary found."
        

    except IndexError:
        return "Error processing the article file", 500

    # Prepare the article data for rendering
    article_data = {
        'title': filename.replace('.html', '').replace('_', ' '),
        'content': article_content,
        'creator': author,
        'pub_date': pub_date,
        'link': link,
        'ai_output': ai_output
    }

    return render_template('article_template.html', article=article_data)

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
