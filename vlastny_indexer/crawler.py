import asyncio
import aiohttp
from urllib.parse import urljoin
import time
import re
import json

    
def extract_links_regex(html):
    """Extract href links using regex"""
    # Pattern to match <a href="..."> tags
    link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>'
    links = re.findall(link_pattern, html, re.IGNORECASE)
    return links

VISITED = set()
PROCESSED = set()
BASE_URL = "https://rawg.io"
WAIT_BETWEEN_REQUESTS = 0
USER_AGENT = "EducationCrawler/1.0 (https://www.fiit.stuba.sk/; xborzik@stuba.sk)"

DISALLOWED_PATHS = set()

def is_url_disallowed(url):
    """Check if URL matches any disallowed pattern using regex"""
    for pattern in DISALLOWED_PATHS:
        if re.match(pattern, url):
            return True
    return False

def is_valid_game_url(url):
    """Check if URL matches the pattern /games/game-name (nothing else follows)"""
    game_url_pattern = r'^https?://[^/]+/games/[^/?#]+/?$'
    return re.match(game_url_pattern, url) is not None

async def fetch(session : aiohttp.ClientSession, url):
    try:
        async with session.get(url, headers={"User-Agent": USER_AGENT}, timeout=5) as resp:
            if resp.status != 200:
                return None
            html = await resp.text()
            return html
    except Exception as e:
        print("Error fetching:", url, e)
        return None
    
async def get_robots_txt(session : aiohttp.ClientSession):
    """Fetch robots.txt and return set of disallowed regex patterns"""
    disallowed_patterns = set()
    
    try:
        async with session.get(urljoin(
            BASE_URL,
            "/robots.txt"),
            headers={"User-Agent": USER_AGENT},
            timeout=5) as resp:
            
            if resp.status != 200:
                print(f"Failed to fetch robots.txt: {resp.status}")
                return disallowed_patterns
                
            text = await resp.text()
            
            # Parse robots.txt and extract disallowed paths
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('Disallow:'):
                    path = line.replace('Disallow:', '').strip()
                    if path and path != '/':
                        # Convert robots.txt wildcard pattern to regex
                        full_url = urljoin(BASE_URL, path)
                        # Escape special regex characters except *
                        regex_pattern = re.escape(full_url).replace('\\\\*', '.*')
                        disallowed_patterns.add(regex_pattern)
            
            return disallowed_patterns
        
    except Exception as e:
        print("Error fetching robots.txt:", e)
        return disallowed_patterns
    
def load_visited_urls():
    global VISITED
    
    with open("crawler_queue_state.json", "r", encoding="utf-8") as statefile:
        state = json.load(statefile)
        VISITED = set(state.get("visited", []))
        queue_list = state.get("queue", [])
        processed = set(state.get("processed", []))
        return VISITED, queue_list, processed

async def crawl(start_url, max_pages=1000000):
    global VISITED, WAIT_BETWEEN_REQUESTS, DISALLOWED_PATHS, PROCESSED, BASE_URL
    
    VISITED, queue_list, PROCESSED = load_visited_urls()
    queue = asyncio.Queue()
    
    for url in queue_list:
        await queue.put(url)
    
    print(f"Resumed crawl: {len(VISITED)} visited URLs, {queue.qsize()} URLs in queue")
    
    if queue.qsize() == 0:
        await queue.put(start_url)
    
    start_time = time.time()
    pages_processed = 0
    last_stats_time = start_time
    url = ""  # Initialize url variable for stats display
    
    async with aiohttp.ClientSession() as temp_session:
        DISALLOWED_PATHS = await get_robots_txt(temp_session)
    
    print(f"Loaded {len(DISALLOWED_PATHS)} disallowed patterns")

    async with aiohttp.ClientSession() as session:
        with open("data_regex.json", "a", encoding="utf-8") as jsonfile:
            while not queue.empty() and len(VISITED) < max_pages:
                
                # Display statistics every 2 seconds
                current_time = time.time()
                if current_time - last_stats_time >= 2:
                    elapsed_time = current_time - start_time
                    elapsed_minutes = int(elapsed_time // 60)
                    elapsed_seconds = int(elapsed_time % 60)
                    queue_size = queue.qsize()
                    
                    print(f"\r Queue: {queue_size:,} | "
                        f"Processed: {pages_processed:,} | Time: {elapsed_minutes}:{elapsed_seconds:02d} | Current URL: {url[:60]}...", 
                        end="", flush=True)
                    last_stats_time = current_time
                
                await asyncio.sleep(WAIT_BETWEEN_REQUESTS)               
                
                url = await queue.get()
                
                if url in PROCESSED:
                    continue
                    
                if is_url_disallowed(url) or BASE_URL not in url or "/games" not in url:
                    continue
                
                if url != start_url and not is_valid_game_url(url):
                    continue
                
                html = await fetch(session, url)
                if not html:
                    continue
                
                pages_processed += 1
                
                # Processing only href links using regex
                links = extract_links_regex(html)
                
                for link in links:
                    try:
                        absolute_link = urljoin(BASE_URL, link)
                        if absolute_link not in VISITED:
                            VISITED.add(url)
                            await queue.put(absolute_link)
                    except (ValueError, Exception):
                        # Skip invalid URLs
                        continue
                
                # Save HTML data and url into JSON file
                record = {
                    "url": url,
                    "html_body": html
                }
                                
                jsonfile.write(json.dumps(record) + "\n") 
                PROCESSED.add(url)
                
                # Save queue satate every 100 processed pages
                if pages_processed % 100 == 0:
                    with open("crawler_queue_state.json", "w", encoding="utf-8") as statefile:
                        state = {
                            "visited": list(VISITED),
                            "queue": list(queue._queue),
                            "processed": list(PROCESSED)
                        }
                        json.dump(state, statefile)
                                          
# Run it
asyncio.run(crawl(f"{BASE_URL}/games"))