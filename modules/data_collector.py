"""
data_collector.py
Fetches reviews from:
1. Amazon / Flipkart (scraping)
2. Reddit (free, no key)
3. Google Shopping Reviews (free, no key)
4. YouTube Comments (needs free API key)
5. Twitter/X (needs free API key)
"""

import re
import time
import random
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, unquote, quote_plus

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
]


def _headers() -> Dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "DNT": "1",
    }


def _delay() -> None:
    time.sleep(random.uniform(1.5, 3.0))


def _expand_url(url: str) -> str:
    try:
        resp = requests.get(url, headers=_headers(), allow_redirects=True, timeout=10)
        return resp.url
    except Exception:
        return url


def detect_platform(url: str) -> str:
    if not url.startswith("http"):
        return "name"
    domain = urlparse(url).netloc.lower()
    if "amazon" in domain or "amzn.in" in domain or "amzn.to" in domain:
        return "amazon"
    if "flipkart" in domain:
        return "flipkart"
    return "name"


def _extract_asin(url: str) -> Optional[str]:
    for pattern in [r"/dp/([A-Z0-9]{10})", r"/product/([A-Z0-9]{10})", r"asin=([A-Z0-9]{10})"]:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


def extract_product_name_from_url(url: str, platform: str) -> str:
    try:
        path = urlparse(url).path
        parts = [p for p in path.split("/") if p]
        if platform == "amazon" and parts:
            name = unquote(parts[0]).replace("-", " ").replace("+", " ")
            name = re.sub(r"\b[A-Z0-9]{8,}\b", "", name)
            name = re.sub(r"\s+", " ", name).strip()
            if len(name) > 5:
                return name
        elif platform == "flipkart" and parts:
            name = unquote(parts[0]).replace("-", " ").replace("+", " ")
            name = re.sub(r"\s+", " ", name).strip()
            if len(name) > 5:
                return name
    except Exception:
        pass
    return ""


def fetch_product_name_from_page(url: str) -> str:
    try:
        _delay()
        resp = requests.get(url, headers=_headers(), timeout=12)
        soup = BeautifulSoup(resp.text, "html.parser")
        for selector in ["#productTitle", "span#productTitle", "span.B_NuCI", "h1.yhB1nd"]:
            el = soup.select_one(selector)
            if el:
                return el.get_text(strip=True)
        title_el = soup.find("title")
        if title_el:
            return title_el.text.strip().split(":")[0].split("|")[0].strip()
    except Exception as e:
        logger.warning(f"Could not fetch product page: {e}")
    return ""


# ═══════════════════════════════════════════════════════════════
# 1. AMAZON SCRAPER
# ═══════════════════════════════════════════════════════════════

def scrape_amazon(url: str, max_pages: int = 3) -> List[Dict[str, Any]]:
    if "amzn.in" in url or "amzn.to" in url:
        url = _expand_url(url)
    asin = _extract_asin(url)
    if not asin:
        return []

    reviews = []
    session = requests.Session()
    for page in range(1, max_pages + 1):
        review_url = (
            f"https://www.amazon.in/product-reviews/{asin}"
            f"?pageNumber={page}&sortBy=recent&reviewerType=all_reviews"
        )
        try:
            _delay()
            resp = session.get(review_url, headers=_headers(), timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            if "captcha" in resp.text.lower() or "robot" in resp.text.lower():
                break
            blocks = soup.find_all("div", {"data-hook": "review"})
            if not blocks:
                break
            for block in blocks:
                try:
                    rating_el = (
                        block.find("i", {"data-hook": "review-star-rating"}) or
                        block.find("i", {"data-hook": "cmps-review-star-rating"})
                    )
                    rating = float(rating_el.text.strip().split()[0]) if rating_el else 0.0
                    body_el = block.find("span", {"data-hook": "review-body"})
                    body = body_el.get_text(strip=True) if body_el else ""
                    date_el = block.find("span", {"data-hook": "review-date"})
                    date = date_el.text.strip() if date_el else ""
                    if body:
                        reviews.append({"source": "amazon", "text": body, "rating": rating, "date": date})
                except Exception:
                    continue
        except Exception:
            break
    return reviews


# ═══════════════════════════════════════════════════════════════
# 2. FLIPKART SCRAPER
# ═══════════════════════════════════════════════════════════════

def scrape_flipkart(url: str, max_pages: int = 3) -> List[Dict[str, Any]]:
    reviews = []
    session = requests.Session()
    for page in range(1, max_pages + 1):
        base = re.sub(r"\?.*", "", url)
        if "/product-reviews/" not in base:
            base = base.replace("/p/", "/product-reviews/")
        page_url = f"{base}?page={page}"
        try:
            _delay()
            resp = session.get(page_url, headers=_headers(), timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            if "Access Denied" in resp.text:
                break
            blocks = (
                soup.find_all("div", {"class": "_1AtVbE"}) or
                soup.find_all("div", {"class": "col _2wzgFH"}) or
                soup.select("div[class*='_6K-7Co']")
            )
            if not blocks:
                break
            for block in blocks:
                try:
                    rating_el = (
                        block.find("div", {"class": "_3LWZlK"}) or
                        block.find("div", {"class": "gQ6S4b"})
                    )
                    if not rating_el:
                        continue
                    rating = float(rating_el.text.strip())
                    if rating == 0.0:
                        continue
                    body_el = (
                        block.find("div", {"class": "t-ZTKy"}) or
                        block.find("div", {"class": "qwjRop"})
                    )
                    body = body_el.get_text(strip=True) if body_el else ""
                    date_el = block.find("p", {"class": "_2sc7ZR"}) or block.find("p", {"class": "MztJPv"})
                    date = date_el.text.strip() if date_el else ""
                    if body and len(body) > 10:
                        reviews.append({"source": "flipkart", "text": body, "rating": rating, "date": date})
                except Exception:
                    continue
        except Exception:
            break
    return reviews


# ═══════════════════════════════════════════════════════════════
# 3. REDDIT (FREE - NO KEY)
# ═══════════════════════════════════════════════════════════════

def fetch_reddit(product_name: str, limit: int = 60) -> List[Dict[str, Any]]:
    results = []
    # Search with "review" appended to get product-specific results
    query = quote_plus(f"{product_name} review")
    headers = {"User-Agent": "ReturnIQ/1.0 (product review analyzer)"}

    # Keywords that indicate a relevant product post
    review_keywords = [
        "review", "quality", "good", "bad", "worst", "best", "broke", "broken",
        "bought", "purchase", "ordered", "delivery", "returned", "refund",
        "recommend", "worth", "price", "product", "item", "works", "problem",
        "issue", "size", "fit", "color", "packaging", "shipping", "disappointed",
        "satisfied", "experience", "unboxing", "pros", "cons", "rating",
    ]
    product_words = [w for w in product_name.lower().split() if len(w) > 3]

    def is_product_relevant(text: str) -> bool:
        text_lower = text.lower()
        has_product = any(w in text_lower for w in product_words)
        has_review_kw = sum(1 for kw in review_keywords if kw in text_lower) >= 2
        return has_product or has_review_kw

    try:
        url = f"https://www.reddit.com/search.json?q={query}&sort=relevance&limit={limit}&type=link"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return results

        posts = resp.json().get("data", {}).get("children", [])
        relevant_posts = []

        for post in posts:
            d = post.get("data", {})
            text = (d.get("title", "") + " " + d.get("selftext", "")).strip()
            if text and len(text) > 15 and is_product_relevant(text):
                results.append({"source": "reddit", "text": text, "rating": 0.0, "date": ""})
                relevant_posts.append(post)

        # Fetch comments only from relevant posts
        for post in relevant_posts[:2]:
            permalink = post["data"].get("permalink", "")
            if not permalink:
                continue
            try:
                time.sleep(1.5)
                cresp = requests.get(
                    f"https://www.reddit.com{permalink}.json",
                    headers=headers, timeout=10
                )
                if cresp.status_code == 200:
                    cdata = cresp.json()
                    if len(cdata) > 1:
                        for c in cdata[1].get("data", {}).get("children", [])[:15]:
                            body = c.get("data", {}).get("body", "")
                            if body and len(body) > 20 and is_product_relevant(body):
                                results.append({"source": "reddit", "text": body, "rating": 0.0, "date": ""})
            except Exception:
                continue

    except Exception as e:
        logger.error(f"Reddit fetch failed: {e}")

    return results


# ═══════════════════════════════════════════════════════════════
# 4. GOOGLE SHOPPING REVIEWS (FREE - NO KEY)
# ═══════════════════════════════════════════════════════════════

def fetch_google_shopping(product_name: str) -> List[Dict[str, Any]]:
    """
    Scrapes review snippets from Google Shopping search results.
    No API key needed.
    """
    results = []
    query = quote_plus(f"{product_name} review")

    try:
        url = f"https://www.google.com/search?q={query}&tbm=shop"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract review snippets from Google Shopping cards
        for el in soup.select("div.sh-dgr__content, div.sh-pr__product-results"):
            text = el.get_text(separator=" ", strip=True)
            if len(text) > 30:
                results.append({
                    "source": "google_shopping",
                    "text": text[:300],
                    "rating": 0.0,
                    "date": "",
                })

        # Also extract from regular Google search snippets
        url2 = f"https://www.google.com/search?q={quote_plus(product_name + ' review problems complaints')}"
        resp2 = requests.get(url2, headers=headers, timeout=12)
        soup2 = BeautifulSoup(resp2.text, "html.parser")

        for el in soup2.select("div.VwiC3b, span.aCOpRe, div.s3v9rd"):
            text = el.get_text(strip=True)
            if len(text) > 40:
                results.append({
                    "source": "google_shopping",
                    "text": text,
                    "rating": 0.0,
                    "date": "",
                })

    except Exception as e:
        logger.error(f"Google Shopping fetch failed: {e}")

    return results[:30]


# ═══════════════════════════════════════════════════════════════
# 5. YOUTUBE COMMENTS (NEEDS FREE API KEY)
# ═══════════════════════════════════════════════════════════════

def fetch_youtube_comments(product_name: str, api_key: str, limit: int = 60) -> List[Dict[str, Any]]:
    """
    Fetches YouTube comments from product review videos.
    Get free API key from: https://console.cloud.google.com
    Enable: YouTube Data API v3 (free tier: 10,000 units/day)
    """
    results = []
    if not api_key:
        return results

    try:
        # Search for review videos
        search_resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": f"{product_name} review",
                "type": "video",
                "maxResults": 5,
                "key": api_key,
                "relevanceLanguage": "en",
                "order": "relevance",
            },
            timeout=10,
        )
        search_data = search_resp.json()

        if "error" in search_data:
            logger.error(f"YouTube API error: {search_data['error']['message']}")
            return results

        video_ids = [item["id"]["videoId"] for item in search_data.get("items", [])]

        for vid in video_ids[:3]:
            try:
                cresp = requests.get(
                    "https://www.googleapis.com/youtube/v3/commentThreads",
                    params={
                        "part": "snippet",
                        "videoId": vid,
                        "maxResults": limit // 3,
                        "key": api_key,
                        "textFormat": "plainText",
                        "order": "relevance",
                    },
                    timeout=10,
                )
                for item in cresp.json().get("items", []):
                    text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                    if text and len(text) > 15:
                        results.append({
                            "source": "youtube",
                            "text": text,
                            "rating": 0.0,
                            "date": "",
                        })
            except Exception:
                continue

    except Exception as e:
        logger.error(f"YouTube fetch failed: {e}")

    return results


# ═══════════════════════════════════════════════════════════════
# 6. TWITTER/X (NEEDS FREE API KEY)
# ═══════════════════════════════════════════════════════════════

def fetch_twitter(product_name: str, bearer_token: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetches tweets about the product.
    Get free Bearer Token from: https://developer.twitter.com
    Free tier: 500,000 tweets/month
    """
    results = []
    if not bearer_token:
        return results

    try:
        query = f"{product_name} (review OR bad OR good OR quality OR return OR problem) -is:retweet lang:en"
        resp = requests.get(
            "https://api.twitter.com/2/tweets/search/recent",
            headers={"Authorization": f"Bearer {bearer_token}"},
            params={
                "query": query,
                "max_results": min(limit, 100),
                "tweet.fields": "text,created_at,public_metrics",
            },
            timeout=10,
        )
        data = resp.json()

        if "errors" in data:
            logger.error(f"Twitter API error: {data['errors']}")
            return results

        for tweet in data.get("data", []):
            text = tweet.get("text", "")
            if text and len(text) > 20:
                results.append({
                    "source": "twitter",
                    "text": text,
                    "rating": 0.0,
                    "date": tweet.get("created_at", ""),
                })

    except Exception as e:
        logger.error(f"Twitter fetch failed: {e}")

    return results


# ═══════════════════════════════════════════════════════════════
# MAIN COLLECTOR
# ═══════════════════════════════════════════════════════════════

def collect_all(
    input_text: str,
    max_pages: int = 3,
    use_reddit: bool = True,
    use_google: bool = True,
    youtube_api_key: str = "",
    twitter_bearer_token: str = "",
) -> Dict[str, Any]:
    """
    Main entry point.
    Paste Amazon/Flipkart URL → extracts product name → fetches from all sources.
    """
    all_reviews = []
    platform = detect_platform(input_text)
    product_name = ""

    # ── STEP 1: Get product name ──────────────────────────────
    if platform in ("amazon", "flipkart"):
        url = input_text
        if "amzn.in" in url or "amzn.to" in url:
            url = _expand_url(url)

        # Try fetching title from product page
        product_name = fetch_product_name_from_page(url)

        # Fallback: extract from URL path
        if not product_name or len(product_name) < 5:
            product_name = extract_product_name_from_url(url, platform)

        # Fallback: use ASIN
        if not product_name:
            product_name = _extract_asin(url) or input_text

        # ── STEP 2: Try scraping reviews ──────────────────────
        if platform == "amazon":
            scraped = scrape_amazon(url, max_pages=max_pages)
        else:
            scraped = scrape_flipkart(url, max_pages=max_pages)

        all_reviews.extend(scraped)

    else:
        # Direct product name input
        product_name = input_text

    # ── STEP 3: Reddit ────────────────────────────────────────
    if use_reddit and product_name:
        reddit_data = fetch_reddit(product_name, limit=60)
        all_reviews.extend(reddit_data)

    # ── STEP 4: Google Shopping ───────────────────────────────
    if use_google and product_name:
        google_data = fetch_google_shopping(product_name)
        all_reviews.extend(google_data)

    # ── STEP 5: YouTube ───────────────────────────────────────
    if youtube_api_key and product_name:
        yt_data = fetch_youtube_comments(product_name, api_key=youtube_api_key, limit=60)
        all_reviews.extend(yt_data)

    # ── STEP 6: Twitter/X ─────────────────────────────────────
    if twitter_bearer_token and product_name:
        tw_data = fetch_twitter(product_name, bearer_token=twitter_bearer_token, limit=50)
        all_reviews.extend(tw_data)

    # Source breakdown
    sources = {}
    for r in all_reviews:
        s = r.get("source", "unknown")
        sources[s] = sources.get(s, 0) + 1

    return {
        "product_name": product_name,
        "platform": platform,
        "reviews": all_reviews,
        "total": len(all_reviews),
        "sources": sources,
    }