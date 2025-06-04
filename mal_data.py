import requests
from bs4 import BeautifulSoup
import csv
import time
import random
from urllib.parse import urljoin
import re
import json

class AlternativeAnimeScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def scrape_myanimelist_enhanced(self, target_count=5000):
        """Enhanced MyAnimeList scraper to get exactly 5000 anime"""
        all_anime_data = []
        seen_titles = set()  # Avoid duplicates
        base_url = "https://myanimelist.net/topanime.php"
        
        # Calculate pages needed (50 anime per page, so 100 pages for 5000)
        pages_needed = (target_count // 50) + 1
        
        print(f"Targeting {target_count} anime from MyAnimeList...")
        print(f"Will scrape {pages_needed} pages (50 anime per page)")
        
        consecutive_failures = 0
        max_failures = 10
        
        for page in range(0, pages_needed):
            if len(all_anime_data) >= target_count:
                print(f"Reached target of {target_count} anime!")
                break
                
            limit = page * 50
            url = f"{base_url}?limit={limit}"
            
            print(f"Scraping page {page + 1}/{pages_needed}: offset {limit}")
            
            try:
                # Random delay between 2-6 seconds to avoid rate limiting
                time.sleep(random.uniform(2, 6))
                
                response = self.session.get(url, timeout=20)
                
                if response.status_code == 429:  # Rate limited
                    wait_time = 60 + random.uniform(10, 30)
                    print(f"  Rate limited, waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code != 200:
                    print(f"  Status code: {response.status_code}, skipping...")
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        print("Too many consecutive failures, stopping...")
                        break
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                anime_rows = soup.find_all('tr', class_='ranking-list')
                
                if not anime_rows:
                    print(f"  No anime found on page {page + 1}")
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        print("No more anime found, stopping...")
                        break
                    continue
                
                consecutive_failures = 0  # Reset failure count
                page_count = 0
                
                for row in anime_rows:
                    try:
                        anime_data = self.extract_mal_anime_data(row)
                        
                        if anime_data['title'] and anime_data['title'] not in seen_titles:
                            seen_titles.add(anime_data['title'])
                            all_anime_data.append(anime_data)
                            page_count += 1
                            
                            if len(all_anime_data) >= target_count:
                                break
                                
                    except Exception as e:
                        print(f"    Error extracting anime: {e}")
                        continue
                
                print(f"  Found {page_count} new anime. Total unique: {len(all_anime_data)}")
                
            except Exception as e:
                print(f"  Error on page {page + 1}: {e}")
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    print("Too many errors, stopping...")
                    break
                time.sleep(15)  # Longer wait on error
                continue
        
        print(f"\nScraping complete! Got {len(all_anime_data)} anime from MyAnimeList")
        return all_anime_data[:target_count]  # Ensure exact count
    
    def scrape_anilist_api_enhanced(self, target_count=5000):
        """Enhanced AniList GraphQL API scraper to get 5000 anime"""
        url = 'https://graphql.anilist.co'
        
        query = '''
        query ($page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    total
                    currentPage
                }
                media(type: ANIME, sort: POPULARITY_DESC) {
                    title {
                        romaji
                        english
                        native
                    }
                    genres
                    studios {
                        nodes {
                            name
                        }
                    }
                    episodes
                    startDate {
                        year
                        month
                    }
                    format
                    averageScore
                    meanScore
                    status
                    season
                    seasonYear
                }
            }
        }
        '''
        
        all_anime_data = []
        seen_titles = set()
        per_page = 50  # Maximum allowed by AniList
        pages_needed = (target_count // per_page) + 1
        
        print(f"Fetching {target_count} anime from AniList API...")
        print(f"Will fetch {pages_needed} pages ({per_page} anime per page)")
        
        for page in range(1, pages_needed + 1):
            if len(all_anime_data) >= target_count:
                print(f"Reached target of {target_count} anime!")
                break
                
            variables = {
                'page': page,
                'perPage': per_page
            }
            
            print(f"Fetching page {page}/{pages_needed}...")
            
            try:
                response = requests.post(url, json={'query': query, 'variables': variables}, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                
                if 'errors' in data:
                    print(f"  GraphQL errors: {data['errors']}")
                    time.sleep(5)
                    continue
                
                if 'data' not in data or 'Page' not in data['data']:
                    print(f"  Invalid response structure")
                    continue
                
                page_data = data['data']['Page']
                
                if not page_data['media']:
                    print(f"  No media found on page {page}")
                    break
                
                page_count = 0
                for anime in page_data['media']:
                    try:
                        # Use the best available title
                        title = (anime['title']['english'] or 
                                anime['title']['romaji'] or 
                                anime['title']['native'] or 
                                'Unknown Title')
                        
                        if title in seen_titles:
                            continue  # Skip duplicates
                        
                        seen_titles.add(title)
                        
                        # Format release date
                        release_date = ''
                        if anime['startDate'] and anime['startDate']['year']:
                            release_date = str(anime['startDate']['year'])
                            if anime['startDate']['month']:
                                release_date += f"-{anime['startDate']['month']:02d}"
                        
                        # Clean up content type
                        content_type = anime['format'] if anime['format'] else 'Unknown'
                        if content_type:
                            content_type = content_type.replace('_', ' ').title()
                        
                        anime_data = {
                            'title': title,
                            'genre': ', '.join(anime['genres']) if anime['genres'] else '',
                            'studio': anime['studios']['nodes'][0]['name'] if anime['studios']['nodes'] else '',
                            'number_of_episodes': str(anime['episodes']) if anime['episodes'] else '',
                            'release_date': release_date,
                            'content_type': content_type,
                            'viewer_reviews': str(anime['averageScore']) if anime['averageScore'] else '',
                            'source': 'AniList'
                        }
                        
                        all_anime_data.append(anime_data)
                        page_count += 1
                        
                        if len(all_anime_data) >= target_count:
                            break
                            
                    except Exception as e:
                        print(f"    Error processing anime: {e}")
                        continue
                
                print(f"  Added {page_count} new anime. Total: {len(all_anime_data)}")
                
                # Check if there's a next page
                if not page_data['pageInfo']['hasNextPage']:
                    print("  Reached last page")
                    break
                
                # Rate limiting - AniList allows ~90 requests per minute
                time.sleep(1)
                
            except Exception as e:
                print(f"  Error with AniList API page {page}: {e}")
                time.sleep(5)
                continue
        
        print(f"\nAniList scraping complete! Got {len(all_anime_data)} anime")
        return all_anime_data[:target_count]  # Ensure exact count
    
    def scrape_combined_sources(self, target_count=5000):
        """Combine multiple sources to get 5000 anime"""
        all_anime_data = []
        seen_titles = set()
        
        print(f"Combining multiple sources to get {target_count} anime...")
        
        # First, get data from AniList (faster and more reliable)
        print("\n1. Fetching from AniList API...")
        try:
            anilist_data = self.scrape_anilist_api_enhanced(target_count // 2)  # Get half from AniList
            for anime in anilist_data:
                if anime['title'] not in seen_titles:
                    seen_titles.add(anime['title'])
                    all_anime_data.append(anime)
            print(f"Got {len(anilist_data)} anime from AniList")
        except Exception as e:
            print(f"AniList failed: {e}")
        
        # If we still need more, get from MyAnimeList
        remaining_needed = target_count - len(all_anime_data)
        if remaining_needed > 0:
            print(f"\n2. Need {remaining_needed} more anime, fetching from MyAnimeList...")
            try:
                mal_data = self.scrape_myanimelist_enhanced(remaining_needed + 500)  # Get extra to account for duplicates
                
                added_count = 0
                for anime in mal_data:
                    if anime['title'] not in seen_titles and len(all_anime_data) < target_count:
                        seen_titles.add(anime['title'])
                        all_anime_data.append(anime)
                        added_count += 1
                
                print(f"Added {added_count} new anime from MyAnimeList")
            except Exception as e:
                print(f"MyAnimeList failed: {e}")
        
        print(f"\nTotal anime collected: {len(all_anime_data)}")
        return all_anime_data[:target_count]  # Ensure exact count
    
    def extract_mal_anime_data(self, row):
        """Extract anime data from a MAL row element"""
        anime_data = {
            'title': '',
            'genre': '',
            'studio': '',
            'number_of_episodes': '',
            'release_date': '',
            'content_type': '',
            'viewer_reviews': '',
            'source': 'MyAnimeList'
        }
        
        # Extract title
        title_elem = row.find('a', class_='hoverinfo_trigger')
        if title_elem:
            anime_data['title'] = title_elem.get_text(strip=True)
        
        # Extract additional info
        info_elem = row.find('div', class_='information')
        if info_elem:
            info_text = info_elem.get_text()
            
            # Extract episodes
            ep_match = re.search(r'(\d+) eps', info_text)
            if ep_match:
                anime_data['number_of_episodes'] = ep_match.group(1)
            elif 'Movie' in info_text:
                anime_data['number_of_episodes'] = '1'
            
            # Extract year
            year_match = re.search(r'(19|20)\d{2}', info_text)
            if year_match:
                anime_data['release_date'] = year_match.group(0)
            
            # Content type
            if 'TV' in info_text:
                anime_data['content_type'] = 'TV Series'
            elif 'Movie' in info_text:
                anime_data['content_type'] = 'Movie'
            elif 'OVA' in info_text:
                anime_data['content_type'] = 'OVA'
            elif 'Special' in info_text:
                anime_data['content_type'] = 'Special'
            else:
                anime_data['content_type'] = 'TV Series'  # Default
        
        # Extract score
        score_elem = row.find('span', class_='text')
        if score_elem:
            anime_data['viewer_reviews'] = score_elem.get_text(strip=True)
        
        return anime_data

def save_to_csv(data, filename):
    """Save data to CSV file"""
    if not data:
        print("No data to save!")
        return
    
    fieldnames = ['title', 'genre', 'studio', 'number_of_episodes', 
                 'release_date', 'content_type', 'viewer_reviews', 'source']
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for anime in data:
            cleaned_anime = {}
            for key, value in anime.items():
                if key in fieldnames:
                    cleaned_anime[key] = str(value).strip() if value else ''
            writer.writerow(cleaned_anime)
    
    print(f"✅ Data saved to {filename}")

def display_sample_data(data, source_name):
    """Display sample scraped data"""
    if not data:
        print(f"No data from {source_name}")
        return
        
    print(f"\n📊 Sample data from {source_name} ({len(data)} total):")
    print("=" * 50)
    
    for i, anime in enumerate(data[:5]):  # Show 5 examples
        print(f"\n{i+1}. {anime.get('title', 'N/A')}")
        print(f"   🎭 Genre: {anime.get('genre', 'N/A')}")
        print(f"   🏢 Studio: {anime.get('studio', 'N/A')}")
        print(f"   📺 Episodes: {anime.get('number_of_episodes', 'N/A')}")
        print(f"   📅 Release: {anime.get('release_date', 'N/A')}")
        print(f"   📋 Type: {anime.get('content_type', 'N/A')}")
        print(f"   ⭐ Rating: {anime.get('viewer_reviews', 'N/A')}")
        print(f"   🔗 Source: {anime.get('source', 'N/A')}")

def main():
    print("🎌 Enhanced Anime Scraper - Targeting 5000 Anime")
    print("=" * 60)
    
    scraper = AlternativeAnimeScraper()
    
    # Method 1: Try combined sources (recommended)
    print("\n🚀 Method 1: Combined sources (AniList + MyAnimeList)")
    try:
        combined_data = scraper.scrape_combined_sources(5000)
        if combined_data:
            print(f"✅ Successfully collected {len(combined_data)} entries from combined sources")
            save_to_csv(combined_data, '5000_anime_combined.csv')
            display_sample_data(combined_data, "Combined Sources")
            return  # Success, exit here
    except Exception as e:
        print(f"❌ Combined approach failed: {e}")
    
    # Method 2: Try AniList only
    print("\n🚀 Method 2: AniList API only")
    try:
        anilist_data = scraper.scrape_anilist_api_enhanced(5000)
        if anilist_data and len(anilist_data) >= 1000:  # At least 1000
            print(f"✅ Successfully collected {len(anilist_data)} entries from AniList")
            save_to_csv(anilist_data, '5000_anime_anilist.csv')
            display_sample_data(anilist_data, "AniList")
            return  # Success
    except Exception as e:
        print(f"❌ AniList approach failed: {e}")
    
    # Method 3: Try MyAnimeList only
    print("\n🚀 Method 3: MyAnimeList only")
    try:
        mal_data = scraper.scrape_myanimelist_enhanced(5000)
        if mal_data:
            print(f"✅ Successfully collected {len(mal_data)} entries from MyAnimeList")
            save_to_csv(mal_data, '5000_anime_mal.csv')
            display_sample_data(mal_data, "MyAnimeList")
    except Exception as e:
        print(f"❌ MyAnimeList approach failed: {e}")
    
    print("\n📝 If all methods fail, consider:")
    print("1. Using a VPN to change your IP address")
    print("2. Running the script at different times of day")
    print("3. Using Selenium with browser automation")
    print("4. Using anime dataset files from Kaggle")

if __name__ == "__main__":
    main()