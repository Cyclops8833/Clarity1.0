# data.py
import os
import json
from datetime import datetime, timedelta
from newsapi import NewsApiClient
import streamlit as st

# Initialize NewsAPI client with proper error handling
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]  # Get API key from Streamlit secrets
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# Source bias mappings (keep this part as is)
SOURCE_BIAS_MAP = {
    # Left-leaning sources
    'cnn': 'left',
    'msnbc': 'left',
    'the-guardian': 'left',
    'the-guardian-au': 'left',
    'the-guardian-uk': 'left',
    'abc-news-au': 'left',
    'abc-news': 'left',
    
    # Center sources
    'reuters': 'center',
    'associated-press': 'center',
    'bbc-news': 'center',
    'bloomberg': 'center',
    'australian-financial-review': 'center',
    'financial-review': 'center',
    
    # Right-leaning sources
    'fox-news': 'right',
    'sky-news': 'right',
    'sky-news-au': 'right',
    'the-australian': 'right',
    'news-com-au': 'right'
}

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def fetch_real_news(country_code='us'):
    """Fetch news from NewsAPI with better error handling and logging"""
    try:
        # First try country-specific news
        top_headlines = newsapi.get_top_headlines(
            country=country_code,
            language='en',
            page_size=100  # Get more articles to ensure we have enough after filtering
        )
        
        if not top_headlines.get('articles'):
            # If no country-specific news, fall back to general English news
            top_headlines = newsapi.get_top_headlines(
                language='en',
                page_size=100
            )
        
        # Process the articles
        processed_articles = []
        seen_titles = set()
        
        for article in top_headlines.get('articles', []):
            # Skip articles without required fields
            if not all([article.get('title'), article.get('url'), article.get('source')]):
                continue
                
            # Skip duplicate titles
            title_key = article['title'].lower()[:60]
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            
            # Get source bias
            source_id = article['source'].get('id', '').lower()
            source_name = article['source'].get('name', 'Unknown Source')
            bias = SOURCE_BIAS_MAP.get(source_id, 'center')
            
            processed_articles.append({
                'title': article['title'],
                'source': source_name,
                'bias': bias,
                'url': article['url'],
                'description': article.get('description', ''),
                'publishedAt': article.get('publishedAt', '')
            })
        
        # Group articles by similar topics
        issues = []
        used_articles = set()
        
        for i, article in enumerate(processed_articles):
            if article['url'] in used_articles:
                continue
                
            # Create a new issue
            related_articles = [article]
            used_articles.add(article['url'])
            
            # Find related articles with different biases
            for other_article in processed_articles:
                if other_article['url'] in used_articles:
                    continue
                    
                # Simple similarity check (can be improved)
                if len(set(article['title'].lower().split()) & 
                       set(other_article['title'].lower().split())) >= 3:
                    related_articles.append(other_article)
                    used_articles.add(other_article['url'])
                    
                    # Stop if we have articles from all biases
                    if len(set(a['bias'] for a in related_articles)) >= 3:
                        break
            
            # Only create issue if we have at least 2 articles with different biases
            if len(set(a['bias'] for a in related_articles)) >= 2:
                issues.append({
                    'id': len(issues) + 1,
                    'headline': article['title'],
                    'keywords': extract_keywords(article['title'], article['description']),
                    'articles': related_articles,
                    'biases_covered': list(set(a['bias'] for a in related_articles))
                })
            
            # Limit to 10 issues
            if len(issues) >= 10:
                break
        
        return issues
    
    except Exception as e:
        st.error(f"Error fetching news: {str(e)}")
        return []

def extract_keywords(title, description):
    """Extract keywords from title and description"""
    text = f"{title} {description}".lower()
    words = text.split()
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
    
    # Get unique words that aren't stop words
    keywords = []
    seen = set()
    for word in words:
        word = ''.join(c for c in word if c.isalnum())
        if (len(word) > 3 and 
            word not in stop_words and 
            word not in seen):
            keywords.append(word)
            seen.add(word)
            if len(keywords) >= 5:  # Limit to 5 keywords
                break
    
    return keywords

def get_articles_by_bias(issue, bias_preference):
    """Filter articles based on user bias preference"""
    articles = issue["articles"]
    if bias_preference == -1:
        return [a for a in articles if a["bias"] in ["left", "center"]]
    elif bias_preference == 1:
        return [a for a in articles if a["bias"] in ["right", "center"]]
    else:
        return articles
