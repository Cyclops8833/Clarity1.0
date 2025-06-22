# data.py
import os
import json
from datetime import datetime, timedelta
from newsapi import NewsApiClient
import streamlit as st
import itertools

# Initialize NewsAPI client
# IMPORTANT: Set your API key as a Streamlit secret or environment variable
NEWS_API_KEY = os.environ.get('NEWS_API_KEY') or st.secrets.get('NEWS_API_KEY')
if not NEWS_API_KEY or NEWS_API_KEY == 'YOUR_API_KEY_HERE':
    st.error("NewsAPI key not found. Please add NEWS_API_KEY to your Streamlit secrets or environment variables.")
    newsapi = None # Set to None to prevent API calls
else:
    try:
        newsapi = NewsApiClient(api_key=NEWS_API_KEY)
    except Exception as e:
        st.error(f"Error initializing NewsAPI client: {e}")
        newsapi = None

# Source bias mappings based on AllSides and Media Bias Fact Check
# This is a simplified mapping for the MVP. A full database would be more accurate.
# Use a clear mapping to avoid sources appearing under multiple biases.
SOURCE_BIAS_MAP = {
    # Left-leaning sources
    'cnn': 'left', 'the-huffington-post': 'left', 'politico': 'left',
    'the-washington-post': 'left', 'the-new-york-times': 'left', 'vice-news': 'left',
    'msnbc': 'left', 'buzzfeed': 'left', 'nbc-news': 'left', 'the-guardian-uk': 'left',
    
    # Center sources (typically more fact-based/less opinionated)
    'reuters': 'center', 'associated-press': 'center', 'bbc-news': 'center',
    'usa-today': 'center', 'npr': 'center', 'the-hill': 'center', 'abc-news': 'center',
    'axios': 'center', 'bloomberg': 'center', 'cbs-news': 'center', 'sbs': 'center',
    'australian-financial-review': 'center', # Adding some AU sources
    
    # Right-leaning sources
    'fox-news': 'right', 'breitbart-news': 'right', 'newsmax': 'right',
    'the-wall-street-journal': 'right', 'the-washington-times': 'right',
    'daily-mail': 'right', 'new-york-post': 'right', 'the-australian': 'right', # Adding some AU sources
    'daily-telegraph': 'right',
}

# Cache configuration
CACHE_DIR = '.cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
CACHE_DURATION_MINUTES = 30  # Refresh news every 30 minutes

def get_source_bias(source_id):
    """Get bias rating for a news source. Defaults to 'center' if unknown."""
    if source_id:
        return SOURCE_BIAS_MAP.get(source_id.lower(), 'center')
    return 'center'

def extract_keywords(title, description=None):
    """Simple keyword extraction from text."""
    text = f"{title or ''} {description or ''}".lower()
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'have',
                  'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might', 'be', 'do', 'says'}
    
    words = text.split()
    keywords = [word.strip('.,!?;:"\'()[]{}') for word in words if len(word) > 3 and word not in stop_words and word.isalpha()]
    
    return list(set(keywords)) # Return unique keywords

def load_cache(cache_key):
    """Load cached news data if it exists and is fresh."""
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                cache_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
                if datetime.now() - cache_time < timedelta(minutes=CACHE_DURATION_MINUTES):
                    return cache_data.get('issues', [])
        except (json.JSONDecodeError, ValueError):
            pass # Cache is corrupted or invalid, ignore
    return None

def save_cache(cache_key, issues):
    """Save news data to cache."""
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    cache_data = {'timestamp': datetime.now().isoformat(), 'issues': issues}
    try:
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
    except IOError:
        pass # Fail silently if writing cache fails

@st.cache_data(ttl=CACHE_DURATION_MINUTES * 60, show_spinner=False)
def fetch_real_news(country_code='us'):
    """
    Fetch real news from NewsAPI, group by topic, and format for Clarity.
    Caches data in a file and in Streamlit's memory cache.
    """
    if not newsapi:
        return get_fallback_issues()

    cache_key = f"news_{country_code}"
    cached_issues = load_cache(cache_key)
    if cached_issues:
        return cached_issues
    
    try:
        st.write("Never ending news...")
        
        all_articles = []
        # Fetch global headlines (US)
        global_headlines = newsapi.get_top_headlines(language='en', country='us', page_size=20)
        all_articles.extend(global_headlines.get('articles', []))
        
        # Fetch country-specific headlines
        if country_code and country_code != 'us':
            local_headlines = newsapi.get_top_headlines(language='en', country=country_code, page_size=20)
            all_articles.extend(local_headlines.get('articles', []))
        
        # Group articles by a common headline/topic
        issues_map = {}
        for article in all_articles:
            if not article.get('title') or not article.get('url') or not article.get('source', {}).get('id'):
                continue
            
            # Use the first few words of the title as a topic key
            topic_key = " ".join(article['title'].lower().split()[:5])
            
            source_id = article['source']['id']
            source_name = article['source']['name']
            bias = get_source_bias(source_id)
            
            if topic_key not in issues_map:
                issues_map[topic_key] = {
                    'headline': article['title'],
                    'keywords': extract_keywords(article['title'], article.get('description', '')),
                    'articles': {'left': None, 'center': None, 'right': None} # Use a dictionary to store one article per bias
                }
            
            # Add article if we haven't found a source for this bias yet
            if issues_map[topic_key]['articles'][bias] is None:
                issues_map[topic_key]['articles'][bias] = {
                    'title': article['title'],
                    'source': source_name,
                    'bias': bias,
                    'url': article['url']
                }

        # Format the issues for display
        final_issues = []
        seen_urls = set()
        for i, (key, issue_data) in enumerate(issues_map.items()):
            # Filter out empty articles and duplicates
            articles = [art for art in issue_data['articles'].values() if art is not None]
            
            # Ensure unique URLs within the issue
            unique_articles = []
            for art in articles:
                if art['url'] not in seen_urls:
                    unique_articles.append(art)
                    seen_urls.add(art['url'])
            
            # Only add the issue if we have at least two different bias viewpoints
            biases_covered = set(art['bias'] for art in unique_articles)
            if len(biases_covered) >= 2:
                final_issues.append({
                    'id': i + 1,
                    'headline': issue_data['headline'],
                    'keywords': issue_data['keywords'],
                    'articles': unique_articles,
                    'biases_covered': sorted(list(biases_covered))
                })
        
        # Save to cache
        save_cache(cache_key, final_issues)
        
        # Limit to 10 issues for performance/UI
        return final_issues[:10]
        
    except Exception as e:
        st.error(f"Error fetching news: {str(e)}")
        return get_fallback_issues()

def get_fallback_issues():
    """Return fallback issues if API fails or no key is provided."""
    return [
        {
            "id": 1,
            "headline": "Unable to fetch live news",
            "keywords": ["api", "error", "connection"],
            "articles": [
                {"title": "Please check your NewsAPI key or internet connection.", "source": "System", "bias": "center", "url": "#"},
                {"title": "Displaying mock data instead.", "source": "System", "bias": "center", "url": "#"},
            ],
            'biases_covered': ['center']
        }
    ]

# Main data interface, remains the same
def get_articles_by_bias(issue, bias_preference):
    """Filter articles based on user bias preference."""
    articles = issue["articles"]
    if bias_preference == -1:
        # Show left and center articles
        return [a for a in articles if a["bias"] in ["left", "center"]]
    elif bias_preference == 1:
        # Show right and center articles
        return [a for a in articles if a["bias"] in ["right", "center"]]
    else:
        # Show all for center preference
        return articles
