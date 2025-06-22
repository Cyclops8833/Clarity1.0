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

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_real_news(country_code='us'):
    """Fetch news, cluster by primary keyword, and ensure at least 2 biases."""
    if not newsapi:
        return []

    try:
        # 1) Fetch country-specific headlines; fallback to global if empty
        resp = newsapi.get_top_headlines(
            country=country_code, language='en', page_size=100
        )
        articles = resp.get('articles') or []
        if not articles:
            resp = newsapi.get_top_headlines(language='en', page_size=100)
            articles = resp.get('articles') or []

        # 2) Preprocess articles
        processed = []
        seen_titles = set()
        for a in articles:
            title = a.get('title') or ""
            url   = a.get('url') or ""
            src   = a.get('source') or {}
            sid   = src.get('id') or ""
            sname = src.get('name') or "Unknown"
            if not title or not url:
                continue
            key = title.lower()[:60]
            if key in seen_titles:
                continue
            seen_titles.add(key)

            bias = get_source_bias(sid)
            processed.append({
                'title': title,
                'url': url,
                'source': sname,
                'bias': bias,
                'description': a.get('description') or ""
            })

        # 3) Cluster by primary keyword
        clusters = {}
        for art in processed:
            kws = extract_keywords(art['title'], art['description'])
            if not kws: 
                continue
            primary = kws[0]
            clusters.setdefault(primary, []).append(art)

        # 4) Build issues from clusters
        issues = []
        for idx, (kw, group) in enumerate(clusters.items(), start=1):
            biases = set(a['bias'] for a in group)
            if len(biases) < 2:
                continue

            # pick up to one article per bias
            sel = []
            for b in ['left', 'center', 'right']:
                for a in group:
                    if a['bias'] == b:
                        sel.append(a)
                        break

            # ensure at least two articles
            if len(sel) < 2:
                continue

            issues.append({
                'id': idx,
                'headline': group[0]['title'],
                'keywords': [kw],
                'articles': sel,
                'biases_covered': sorted(biases)
            })
            if len(issues) >= 10:
                break

        # 5) If still no issues, fallback to single-article issues
        if not issues:
            for idx, art in enumerate(processed[:8], start=1):
                issues.append({
                    'id': idx,
                    'headline': art['title'],
                    'keywords': extract_keywords(art['title'], art['description'])[:3],
                    'articles': [
                        art,
                        {   # placeholder opposite perspective
                            'title': f"[Other view on] {art['title']}",
                            'url': art['url'],
                            'source': "Various",
                            'bias': 'center',
                            'description': ""
                        }
                    ],
                    'biases_covered': [art['bias'], 'center']
                })
        return issues

    except Exception as e:
        st.error(f"Error fetching news: {e}")
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
