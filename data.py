# data.py
import os
import json
from datetime import datetime, timedelta
from newsapi import NewsApiClient
import streamlit as st

# Initialize NewsAPI client
NEWS_API_KEY = os.environ.get('NEWS_API_KEY') or st.secrets.get('NEWS_API_KEY', 'YOUR_API_KEY_HERE')
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# Source bias mappings based on AllSides and Media Bias Fact Check
SOURCE_BIAS_MAP = {
    # Left-leaning sources
    'cnn': 'left',
    'msnbc': 'left',
    'the-guardian-uk': 'left',
    'the-huffington-post': 'left',
    'politico': 'left',
    'the-washington-post': 'left',
    'nbc-news': 'left',
    'buzzfeed': 'left',
    'vice-news': 'left',
    'the-new-york-times': 'left',

    # Center sources
    'bbc-news': 'center',
    'reuters': 'center',
    'associated-press': 'center',
    'axios': 'center',
    'bloomberg': 'center',
    'the-hill': 'center',
    'usa-today': 'center',
    'npr': 'center',
    'abc-news': 'center',
    'cbs-news': 'center',

    # Right-leaning sources
    'fox-news': 'right',
    'the-wall-street-journal': 'right',
    'the-american-conservative': 'right',
    'national-review': 'right',
    'the-washington-times': 'right',
    'daily-mail': 'right',
    'new-york-post': 'right',
    'newsmax': 'right',
    'breitbart-news': 'right',
}

# Cache configuration
CACHE_FILE = 'news_cache.json'
CACHE_DURATION_MINUTES = 30  # Refresh news every 30 minutes

def load_cache():
    """Load cached news data if it exists and is fresh."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                cache_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
                if datetime.now() - cache_time < timedelta(minutes=CACHE_DURATION_MINUTES):
                    return cache_data.get('issues', [])
        except (json.JSONDecodeError, ValueError):
            pass
    return None

def save_cache(issues):
    """Save news data to cache."""
    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'issues': issues
    }
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
    except IOError:
        pass  # Fail silently if can't write cache

def get_source_bias(source_id):
    """Get bias rating for a news source."""
    if source_id:
        return SOURCE_BIAS_MAP.get(source_id.lower(), 'center')  # Default to center if unknown
    return 'center'

def extract_keywords(title, description):
    """Extract keywords from article title and description."""
    text = f"{title} {description or ''}".lower()
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                  'have', 'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might'}

    words = text.split()
    keywords = []
    for word in words:
        word = word.strip('.,!?;:"')
        if len(word) > 3 and word not in stop_words and word.isalpha():
            keywords.append(word)

    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)
            if len(unique_keywords) >= 4:
                break

    return unique_keywords

def fetch_real_news():
    """Fetch real news from NewsAPI and format for Clarity."""
    try:
        cached_issues = load_cache()
        if cached_issues:
            return cached_issues

        all_articles = []

        # Fetch global top headlines
        top_headlines = newsapi.get_top_headlines(
            language='en',
            page_size=50
        )
        all_articles.extend(top_headlines.get('articles', []))

        # Fetch geolocated news (e.g., Australia)
        geolocated_headlines = newsapi.get_top_headlines(
            country='au',
            language='en',
            page_size=20
        )
        all_articles.extend(geolocated_headlines.get('articles', []))

        # Fetch news from different categories for diversity
        categories = ['technology', 'business', 'politics', 'health', 'science']
        for category in categories:
            try:
                category_news = newsapi.get_top_headlines(
                    category=category,
                    language='en',
                    page_size=20
                )
                all_articles.extend(category_news.get('articles', []))
            except:
                continue

        issues = []
        seen_titles = set()
        issue_id = 1

        for article in all_articles:
            if not article.get('title') or not article.get('url'):
                continue

            title_words = set(article['title'].lower().split()[:5])
            if any(len(title_words.intersection(seen)) > 3 for seen in seen_titles):
                continue
            seen_titles.add(frozenset(article['title'].lower().split()))

            source_id = article.get('source', {}).get('id', '')
            source_name = article.get('source', {}).get('name', 'Unknown Source')
            bias = get_source_bias(source_id)

            keywords = extract_keywords(article['title'], article.get('description', ''))

            related_articles = [{
                'title': article['title'],
                'source': source_name,
                'bias': bias,
                'url': article['url']
            }]

            for other_article in all_articles:
                if other_article == article:
                    continue

                other_source_id = other_article.get('source', {}).get('id', '')
                other_bias = get_source_bias(other_source_id)

                if other_bias != bias and other_article.get('title'):
                    other_keywords = set(extract_keywords(other_article['title'], other_article.get('description', '')))
                    if len(set(keywords).intersection(other_keywords)) >= 2:
                        related_articles.append({
                            'title': other_article['title'],
                            'source': other_article.get('source', {}).get('name', 'Unknown'),
                            'bias': other_bias,
                            'url': other_article['url']
                        })

                        # Ensure articles from different sources
                        sources_covered = set(a['source'] for a in related_articles)
                        if len(sources_covered) >= 2:
                            break

            # Ensure at least two different biases
            biases_in_issue = set(a['bias'] for a in related_articles)
            if len(biases_in_issue) >= 2:
                issue = {
                    'id': issue_id,
                    'headline': article['title'][:60] + '...' if len(article['title']) > 60 else article['title'],
                    'keywords': keywords[:4],
                    'articles': related_articles[:6]  # Limit to 6 articles per issue
                }
                issues.append(issue)
                issue_id += 1

                if len(issues) >= 10:
                    break

        if len(issues) < 5:
            for article in all_articles[:15]:  # Take first 15 articles
                if not article.get('title') or not article.get('url'):
                    continue

                source_id = article.get('source', {}).get('id', '')
                source_name = article.get('source', {}).get('name', 'Unknown Source')
                bias = get_source_bias(source_id)
                keywords = extract_keywords(article['title'], article.get('description', ''))

                # Create synthetic diverse viewpoints
                issue = {
                    'id': issue_id,
                    'headline': article['title'][:60] + '...' if len(article['title']) > 60 else article['title'],
                    'keywords': keywords[:4],
                    'articles': [
                        {
                            'title': article['title'],
                            'source': source_name,
                            'bias': bias,
                            'url': article['url']
                        }
                    ]
                }

                # Add placeholder articles for missing biases (in production, you'd search for real ones)
                if bias != 'left':
                    issue['articles'].append({
                        'title': f"[Left perspective on: {keywords[0] if keywords else 'this topic'}]",
                        'source': 'Left-leaning Source',
                        'bias': 'left',
                        'url': article['url']  # Same URL as placeholder
                    })
                if bias != 'center':
                    issue['articles'].append({
                        'title': f"[Balanced perspective on: {keywords[0] if keywords else 'this topic'}]",
                        'source': 'Centrist Source',
                        'bias': 'center',
                        'url': article['url']
                    })
                if bias != 'right':
                    issue['articles'].append({
                        'title': f"[Right perspective on: {keywords[0] if keywords else 'this topic'}]",
                        'source': 'Right-leaning Source',
                        'bias': 'right',
                        'url': article['url']
                    })

                issues.append(issue)
                issue_id += 1

                if len(issues) >= 8:
                    break

        # Save to cache
        save_cache(issues)
        return issues

    except Exception as e:
        st.error(f"Error fetching news: {str(e)}")
        # Return some default data if API fails
        return get_fallback_issues()

def get_fallback_issues():
    """Return fallback issues if API fails."""
    return [
        {
            "id": 1,
            "headline": "Unable to fetch live news",
            "keywords": ["api", "error", "fallback"],
            "articles": [
                {"title": "Please check your internet connection", "source": "System", "bias": "center",
                 "url": "https://newsapi.org"},
                {"title": "Or your NewsAPI key may be invalid", "source": "System", "bias": "center",
                 "url": "https://newsapi.org"},
            ]
        }
    ]

# Main data interface - same as before
ISSUES = []  # Will be populated when needed

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

# Fetch news when module is imported
# In production, you might want to do this more strategically
try:
    ISSUES = fetch_real_news()
except:
    ISSUES = get_fallback_issues()
