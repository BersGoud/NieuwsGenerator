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

    # Parse the HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Attempt to find the article's main content using a more precise selector
    content_div = soup.find('div', class_='article-body')  # Change this based on the actual class
    if content_div:
        return content_div.get_text(separator=' ', strip=True)
    
    # Fallback: look for all paragraphs, but this should be last resort
    paragraphs = soup.find_all('p')
    if paragraphs:
        return ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

    return "No article content found."

def process_articles(articles):
    processed_articles = []
    
    # Process the first three latest articles
    for i, article in enumerate(articles[:3]):  # Update to process more if desired
        print(f"Processing article {i + 1} of 3: {article['link']}")
        full_text = fetch_full_article(article['link'])

        # Use Cohere API to rewrite and translate the article to Dutch
        ai_response = cohere_client.generate(
            prompt=(  
                f"{full_text}\n\n"
                "Based on the information provided, write an in-depth analysis of the situation involving Nippon Steel's acquisition of U.S. Steel. "
                "Consider the potential national security risks and how this acquisition may impact the American steel industry. "
                "Include insights on historical precedents, similar cases, and possible implications for the economy and workforce. "
                "Discuss any political or economic ramifications, and elaborate on how public opinion might be influenced by such developments. "
                "Your output should not only summarize the details of the article but also provide a comprehensive perspective on the broader implications of this situation."
            ),
            model="command-nightly",
            max_tokens=10000,  # Increased to allow for more content
            temperature=0.5,
            stop_sequences=["\n\n"],
        )
        
        # Ensure AI output captures more of the full content
        if ai_response.generations and ai_response.generations[0].text.strip():
            article['ai_output'] = ai_response.generations[0].text.strip()
        else:
            article['ai_output'] = "No content generated."  # Fallback if no content returned

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
        author = content.split("<!-- Author: ")[1].split(" -->")[0]
        pub_date = content.split("<!-- Pub Date: ")[1].split(" -->")[0]

        # Extract the main content of the article
        article_content = content.split('<div class="content">')[1].split('</div>')[0]

        # Extract AI output
        ai_output = content.split('<h2>Samenvatting:</h2>')[1].split('</p>')[0].replace('</p>', '')  # Ensure to handle HTML correctly
        
        # Extract the original link if available
        link = content.split('<a href="')[1].split('"')[0]
    except IndexError:
        return "Error processing the article file", 500

    # Prepare the article data for rendering
    article_data = {
        'title': filename.replace('.html', '').replace('_', ' '),
        'content': article_content,
        'creator': author,
        'pub_date': pub_date,
        'link': link,  # Include the link to the original article
        'ai_output': ai_output  # Include the AI-generated output
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
