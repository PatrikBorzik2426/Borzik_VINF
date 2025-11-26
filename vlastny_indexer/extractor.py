
from datetime import datetime
import re
import json
import csv

MEAT_TO_OBTAIN = [
    "description",
    "gamePlatform",
    "genre",
    "datePublished",
    "keywords",
    "publisher"
]

def parse_date_to_dd_mm_yyyy(date_string):
    """Convert date from 'Sep 17, 2013' format to 'DD-MM-YYYY' format"""
    if not date_string or date_string.strip() == "":
        return ""
    
    try:
        # Parse the date in format "Sep 17, 2013" or "September 17, 2013"
        parsed_date = datetime.strptime(date_string.strip(), "%b %d, %Y")
        # Return in DD-MM-YYYY format
        return parsed_date.strftime("%d-%m-%Y")
    except ValueError:
        try:
            # Try full month name format "September 17, 2013"
            parsed_date = datetime.strptime(date_string.strip(), "%B %d, %Y")
            return parsed_date.strftime("%d-%m-%Y")
        except ValueError:
            # If parsing fails, return original string
            return date_string.strip()

def extract_h1_regex(html):
    """Extract h1 text using regex"""
    # Pattern to match <h1>...</h1> tags
    h1_pattern = r'<h1[^>]*>(.*?)</h1>'
    matches = re.findall(h1_pattern, html, re.IGNORECASE | re.DOTALL)
    if matches:
        # Remove HTML tags from the content
        text = re.sub(r'<[^>]+>', '', matches[0])
        return text.strip()
    return "No H1"

def extract_metascore_regex(html):
    """Extract metascore using regex"""
    # Pattern to match div with title="Metascore"
    metascore_pattern = r'<div[^>]+title=["\']Metascore["\'][^>]*>(.*?)</div>'
    matches = re.findall(metascore_pattern, html, re.IGNORECASE | re.DOTALL)
    if matches:
        # Remove HTML tags and extract text
        text = re.sub(r'<[^>]+>', '', matches[0])
        return text.strip()
    return -1

def extract_buy_platforms_regex(html):
    """Extract buy platforms using regex"""
    # Pattern to match div with class="game__availability-item"
    platform_pattern = r'<div[^>]+class=["\'][^"\']*game__availability-item[^"\']*["\'][^>]*>(.*?)</div>'
    matches = re.findall(platform_pattern, html, re.IGNORECASE | re.DOTALL)
    platforms = []
    for match in matches:
        # Remove HTML tags and extract text
        text = re.sub(r'<[^>]+>', '', match)
        platforms.append(text.strip())
    return platforms

def extract_itemprops_regex(html):
    """Extract itemprop metadata using regex"""
    itemprops = []
    
    # Pattern to match tags with itemprop attribute
    itemprop_pattern = r'<[^>]+itemprop=["\']([^"\']+)["\'][^>]*(?:content=["\']([^"\']*)["\'])?[^>]*>(.*?)</[^>]+>'
    matches = re.findall(itemprop_pattern, html, re.IGNORECASE | re.DOTALL)
    
    for match in matches:
        itemprop, content_attr, inner_content = match
        if itemprop in MEAT_TO_OBTAIN:
            # Use content attribute if available, otherwise use inner text
            content = content_attr if content_attr else re.sub(r'<[^>]+>', '', inner_content).strip()
            itemprops.append({
                "itemprop": itemprop,
                "content": content
            })
    
    # Also check for self-closing tags with content attribute
    self_closing_pattern = r'<[^>]+itemprop=["\']([^"\']+)["\'][^>]*content=["\']([^"\']*)["\'][^>]*/?>'
    self_closing_matches = re.findall(self_closing_pattern, html, re.IGNORECASE)
    
    for itemprop, content in self_closing_matches:
        if itemprop in MEAT_TO_OBTAIN:
            itemprops.append({
                "itemprop": itemprop,
                "content": content
            })
    
    return itemprops

def process_item(item, csvfile, writer, line_num):
    """Process a single item and write to CSV"""
    try:
        html = item.get("html_body", "")
        url = item.get("url", "")
        
        # Processing only h1 header using regex
        header1 = extract_h1_regex(html)
        
        # Processing meta score using regex
        metascore = extract_metascore_regex(html)
        
        # Processing where to buy the game using regex
        buy_platforms = extract_buy_platforms_regex(html)
        
        # Processing all metadata using regex
        itemprops = extract_itemprops_regex(html)

        # CSV object data
        raw_date = next((prop["content"] for prop in itemprops if prop["itemprop"] == "datePublished"), "").replace("\n", " ").replace("\r", " ").strip()
        formatted_date = parse_date_to_dd_mm_yyyy(raw_date)
        
        data = {
            "full_name": header1,
            "url": url,
            "description": next((prop["content"] for prop in itemprops if prop["itemprop"] == "description"), "").replace("\n", " ").replace("\r", " ").strip(),
            "platform": [prop["content"] for prop in itemprops if prop["itemprop"] == "gamePlatform"],
            "genre": [prop["content"] for prop in itemprops if prop["itemprop"] == "genre"],
            "datePublished": formatted_date,
            "keywords": [prop["content"].split(",") for prop in itemprops if prop["itemprop"] == "keywords"],
            "publisher": next((prop["content"] for prop in itemprops if prop["itemprop"] == "publisher"), "").replace("\n", " ").replace("\r", " ").strip(),
            "metascore": metascore,
            "buy_platforms": buy_platforms  
        }   
        
        # Write data to CSV file
        writer.writerow(data)
        
        # Print progress every 100 items
        if line_num % 100 == 0:
            print(f"Processed {line_num} items...")
            
    except Exception as e:
        print(f"Error processing item {line_num}: {e}")

def main():
    processed_count = 0
    
    # Open CSV file once for writing
    with open("data_regex2.csv", "w", encoding="utf-8", newline="") as csvfile:
        fieldnames = ["full_name", "url", "description", "platform", "genre", "datePublished", "keywords", "publisher","metascore", "buy_platforms"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        
        # Stream process JSON file line by line
        with open("data_regex.json", "r", encoding="utf-8") as jsonfile:
            for line_num, line in enumerate(jsonfile, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    process_item(item, csvfile, writer, line_num)
                    processed_count += 1
                except json.JSONDecodeError as e:
                    print(f"Error parsing line {line_num}: {e}")
                    continue
    
    print(f"\nTotal processed: {processed_count} items")

main()