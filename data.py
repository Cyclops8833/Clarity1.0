# data.py
import os
import json
from datetime import datetime, timedelta
from newsapi import NewsApiClient
import streamlit as st

# Initialize NewsAPI client with proper error handling
try:
    NEWS_API_KEY = st.secrets.get("NEWS_API_KEY")
    if not NEWS_API_KEY:
        st.error("NewsAPI key not found in Streamlit secrets!")
        newsapi = None
    else:
        newsapi = NewsApiClient(api_key=NEWS_API_KEY)
except Exception as e:
    st.error(f"Error accessing NewsAPI key: {str(e)}")
    newsapi = None

# Source bias mappings
SOURCE_BIAS_MAP = {
    # Left-leaning sources
    'cnn': 'left',
    'msnbc': 'left',
    'the-guardian': 'left',
    'the-guardian-au': 'left',
    'the-guardian-uk': 'left',
    'abc-news-au': 'left',
    'abc-news': 'left',
    'the-new-york-times': 'left',
    'the-washington-post': 'left',
    'politico': 'left',
    'huffpost': 'left',
    'vice-news': 'left',
    'buzzfeed': 'left',
    'nbc-news': 'left',
    
    # Center sources
    'reuters': 'center',
    'associated-press': 'center',
    'bbc-news': 'center',
    'bloomberg': 'center',
    'axios': 'center',
    'the-hill': 'center',
    'usa-today': 'center',
    'npr': 'center',
    'cbs-news': 'center',
    'australian-financial-review': 'center',
    
    # Right-leaning sources
    'fox-news': 'right',
    'breitbart-news': 'right',
    'the-wall-street-journal': 'right',
    'newsmax': 'right',
    'daily-mail': 'right',
    'the-washington-times': 'right',
    'new-york-post': 'right',
    'the-australian': 'right',
    'sky-news-au': 'right',
}

def get_source_bias(source_id):
    """Get bias rating for a news source with proper None handling"""
    if source_id and isinstance(source_id, str):
        return SOURCE_BIAS_MAP.get(source_id.lower(), 'center')
    return 'center'

def extract_keywords(title, description):
    """Extract keywords with proper None handling"""
    # Ensure title and description are strings
    title = str(title) if title else ""
    description = str(description) if description else ""
    
    text = f"{title} {description}".lower()
    words = text.split()
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'have',
                  'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might', 'be', 
                  'do', 'says', 'said', 'new', 'news', '-'}
    
    keywords = []
    seen = set()
    for word in words:
        # Clean the word
        word = ''.join(c for c in word if c.isalnum()).lower()
        if (len(word) > 3 and 
            word not in stop_words and 
            word not in seen and
            word.isalpha()):
            keywords.append(word)
            seen.add(word)
            if len(keywords) >= 5:
                break
    
    return keywords

@st.cache_data(ttl=1800, show_spinner=False)  # Cache for 30 minutes
def fetch_real_news(country_code='us'):
    """Fetch news from NewsAPI with comprehensive error handling"""
    if not newsapi:
        return []
    
    try:
        # Debug information
        st.write(f"Fetching news for country: {country_code}")
        
        # Try to get top headlines
        response = newsapi.get_top_headlines(
            country=country_code,
            language='en',
            page_size=100
        )
        
        # Debug the response
        st.write(f"API Status: {response.get('status', 'Unknown')}")
        st.write(f"Total Results: {response.get('totalResults', 0)}")
        
        articles = response.get('articles', [])
        if not articles:
            # Try without country restriction
            st.write("No country-specific news found, trying global English news...")
            response = newsapi.get_top_headlines(
                language='en',
                page_size=100
            )
            articles = response.get('articles', [])
        
        # Process articles
        processed_articles = []
        seen_titles = set()
        
        for article in articles:
            # Skip if essential fields are missing
            if not article or not isinstance(article, dict):
                continue
                
            title = article.get('title')
            url = article.get('url')
            source = article.get('source', {})
            
            if not title or not url or not source:
                continue
            
            # Skip duplicates
            title_key = title.lower()[:60]
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            
            # Get source information safely
            source_id = source.get('id') if isinstance(source, dict) else None
            source_name = source.get('name', 'Unknown Source') if isinstance(source, dict) else 'Unknown Source'
            
            # Get bias rating
            bias = get_source_bias(source_id)
            
            processed_articles.append({
                'title': title,
                'source': source_name,
                'source_id': source_id or 'unknown',
                'bias': bias,
                'url': url,
                'description': article.get('description', ''),
                'publishedAt': article.get('publishedAt', '')
            })
        
        st.write(f"Processed {len(processed_articles)} articles")
        
        # Group articles into issues
        issues = []
        used_urls = set()
        
        for i, main_article in enumerate(processed_articles):
            if main_article['url'] in used_urls:
                continue
            
            # Create an issue with this article
            issue_articles = [main_article]
            used_urls.add(main_article['url'])
            
            # Find related articles with different biases
            main_keywords = set(extract_keywords(main_article['title'], main_article['description']))
            
            for other_article in processed_articles:
                if other_article['url'] in used_urls:
                    continue
                
                # Check if it's from a different bias
                if other_article['bias'] == main_article['bias']:
                    continue
                
                # Check for keyword similarity
                other_keywords = set(extract_keywords(other_article['title'], other_article['description']))
                common_keywords = main_keywords & other_keywords
                
                if len(common_keywords) >= 2:  # At least 2 common keywords
                    issue_articles.append(other_article)
                    used_urls.add(other_article['url'])
                    
                    # Try to get one from each bias
                    biases = set(a['bias'] for a in issue_articles)
                    if len(biases) >= 3:
                        break
            
            # Only create issue if we have multiple perspectives
            biases = set(a['bias'] for a in issue_articles)
            if len(biases) >= 2:
                issues.append({
                    'id': len(issues) + 1,
                    'headline': main_article['title'],
                    'keywords': list(main_keywords)[:5],
                    'articles': issue_articles,
                    'biases_covered': sorted(list(biases))
                })
            
            # Limit number of issues
            if len(issues) >= 10:
                break
        
        st.write(f"Created {len(issues)} issues with multiple perspectives")
        return issues
        
    except Exception as e:
        st.error(f"Error fetching news: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return []

def get_articles_by_bias(issue, bias_preference):
    """Filter articles based on user bias preference"""
    if not issue or 'articles' not in issue:
        return []
        
    articles = issue["articles"]
    if bias_preference == -1:
        return [a for a in articles if a["bias"] in ["left", "center"]]
    elif bias_preference == 1:
        return [a for a in articles if a["bias"] in ["right", "center"]]
    else:
        return articles
