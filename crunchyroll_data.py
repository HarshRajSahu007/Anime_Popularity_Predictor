import requests
from bs4 import BeautifulSoup
import csv
import time
import random
from urllib.parse import urljoin
import re
import json

class EnhancedCrunchyrollScraper:
    def __init__(self):
        self.base_url = "https://www.crunchyroll.com"
        self.session = requests.Session()
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        })
    
    def get_page_with_session(self, url):
        """Try to get page with session cookies"""
        try:

            self.session.get("https://www.crunchyroll.com")
            time.sleep(2)
            

            response = self.session.get(url, timeout=15)
            return response
        except Exception as e:
            print(f"Session approach failed: {e}")
            return None


class AlternativeAnimeScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def scrape_myanimelist(self, num_pages=400):
        """Scrape from MyAnimeList (more scraping-friendly)"""
        all_anime_data = []
        
        for page in range(1, num_pages + 1):
            url = f"https://myanimelist.net/topanime.php?limit={50 * (page - 1)}"
            print(f"Scraping MAL page: {url}")
            
            try:
                response = self.session.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                

                anime_rows = soup.find_all('tr', class_='ranking-list')
                
                for row in anime_rows:
                    try:
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
                        

                        title_elem = row.find('a', class_='hoverinfo_trigger')
                        if title_elem:
                            anime_data['title'] = title_elem.get_text(strip=True)
                        

                        info_elem = row.find('div', class_='information')
                        if info_elem:
                            info_text = info_elem.get_text()
                            

                            ep_match = re.search(r'(\d+) eps', info_text)
                            if ep_match:
                                anime_data['number_of_episodes'] = ep_match.group(1)
                            

                            year_match = re.search(r'(19|20)\d{2}', info_text)
                            if year_match:
                                anime_data['release_date'] = year_match.group(0)
                            

                            if 'TV' in info_text:
                                anime_data['content_type'] = 'TV Series'
                            elif 'Movie' in info_text:
                                anime_data['content_type'] = 'Movie'
                            elif 'OVA' in info_text:
                                anime_data['content_type'] = 'OVA'
                        

                        score_elem = row.find('span', class_='text')
                        if score_elem:
                            anime_data['viewer_reviews'] = score_elem.get_text(strip=True)
                        
                        if anime_data['title']:
                            all_anime_data.append(anime_data)
                        
                    except Exception as e:
                        print(f"Error processing anime row: {e}")
                        continue
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"Error scraping MAL page {page}: {e}")
                continue
        
    def scrape_myanimelist_comprehensive(self, max_anime=10000):
        """Scrape comprehensive anime data from multiple MAL categories"""
        all_anime_data = []
        seen_titles = set() 
        

        categories = [
            'topanime.php',  
            'topanime.php?type=bypopularity',  
            'topanime.php?type=upcoming', 
            'topanime.php?type=airing', 
            'topanime.php?type=tv', 
            'topanime.php?type=movie', 
            'topanime.php?type=ova',  
            'topanime.php?type=special' 
        ]
        
        for category in categories:
            print(f"Scraping category: {category}")
            
            page = 1
            consecutive_empty_pages = 0
            
            while len(all_anime_data) < max_anime and consecutive_empty_pages < 3:
                url = f"https://myanimelist.net/{category}&limit={50 * (page - 1)}"
                print(f"  Page {page}: {url}")
                
                try:
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    anime_rows = soup.find_all('tr', class_='ranking-list')
                    
                    if not anime_rows:
                        consecutive_empty_pages += 1
                        print(f"    No anime found on page {page}")
                        page += 1
                        continue
                    
                    consecutive_empty_pages = 0
                    found_new_anime = False
                    
                    for row in anime_rows:
                        try:
                            anime_data = self.extract_mal_anime_data(row)
                            
                            if anime_data['title'] and anime_data['title'] not in seen_titles:
                                seen_titles.add(anime_data['title'])
                                all_anime_data.append(anime_data)
                                found_new_anime = True
                                
                                if len(all_anime_data) >= max_anime:
                                    break
                        
                        except Exception as e:
                            print(f"    Error processing anime: {e}")
                            continue
                    
                    print(f"    Found {len([r for r in anime_rows if r])} anime on this page")
                    print(f"    Total unique anime so far: {len(all_anime_data)}")
                    
                    if not found_new_anime:
                        consecutive_empty_pages += 1
                    
                    # Rate limiting
                    time.sleep(random.uniform(1, 3))
                    page += 1
                    
                except Exception as e:
                    print(f"    Error scraping page {page}: {e}")
                    consecutive_empty_pages += 1
                    time.sleep(5) 
                    page += 1
                    continue
            
            print(f"Finished category {category}. Total anime: {len(all_anime_data)}")
            
            if len(all_anime_data) >= max_anime:
                break
        
    def scrape_myanimelist_simple(self, max_pages=100): 
        """Simple reliable MyAnimeList scraper for 5000 anime"""
        all_anime_data = []
        base_url = "https://myanimelist.net/topanime.php"
        
        for page in range(0, max_pages):
            limit = page * 50
            url = f"{base_url}?limit={limit}"
            
            print(f"Scraping page {page + 1}/{max_pages}: {url}")
            
            try:

                time.sleep(random.uniform(2, 5))
                
                response = self.session.get(url, timeout=15) 
                if response.status_code != 200:
                    print(f"  Status code: {response.status_code}")
                    if response.status_code == 429: 
                        print("  Rate limited, waiting 30 seconds...")
                        time.sleep(30)
                        continue
                    else:
                        print("  Non-429 error, skipping page")
                        continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                

                anime_rows = soup.find_all('tr', class_='ranking-list')
                
                if not anime_rows:
                    print(f"  No anime found on page {page + 1}")
                    break  
                
                page_count = 0
                for row in anime_rows:
                    try:
                        anime_data = self.extract_mal_anime_data(row)
                        if anime_data['title']:
                            all_anime_data.append(anime_data)
                            page_count += 1
                    except Exception as e:
                        print(f"    Error extracting anime: {e}")
                        continue
                
                print(f"  Found {page_count} anime on this page. Total: {len(all_anime_data)}")
                

                if len(all_anime_data) >= 5000:
                    print("Reached target of 5000 anime")
                    break
                    
            except Exception as e:
                print(f"  Error on page {page + 1}: {e}")
                time.sleep(10) 
                continue
        
        return all_anime_data[:5000]  
    
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
        

        title_elem = row.find('a', class_='hoverinfo_trigger')
        if title_elem:
            anime_data['title'] = title_elem.get_text(strip=True)
        

        info_elem = row.find('div', class_='information')
        if info_elem:
            info_text = info_elem.get_text()
            

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
    
    def scrape_anilist_api(self, max_pages=20):
        """Use AniList GraphQL API (public and free) - Get more data"""
        url = 'https://graphql.anilist.co'
        
        query = '''
        query ($page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                }
                media(type: ANIME, sort: POPULARITY_DESC) {
                    title {
                        romaji
                        english
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
                    }
                    format
                    averageScore
                    meanScore
                }
            }
        }
        '''
        
        all_anime_data = []
        
        for page in range(1, max_pages + 1): 
            variables = {
                'page': page,
                'perPage': 50
            }
            
            try:
                response = requests.post(url, json={'query': query, 'variables': variables})
                response.raise_for_status()
                data = response.json()
                
                if 'data' in data and 'Page' in data['data']:
                    page_data = data['data']['Page']
                    
                    if not page_data['media']:
                        print(f"No more data on page {page}")
                        break
                    
                    for anime in page_data['media']:
                        anime_data = {
                            'title': anime['title']['english'] or anime['title']['romaji'],
                            'genre': ', '.join(anime['genres']) if anime['genres'] else '',
                            'studio': anime['studios']['nodes'][0]['name'] if anime['studios']['nodes'] else '',
                            'number_of_episodes': str(anime['episodes']) if anime['episodes'] else '',
                            'release_date': str(anime['startDate']['year']) if anime['startDate'] and anime['startDate']['year'] else '',
                            'content_type': anime['format'] if anime['format'] else '',
                            'viewer_reviews': str(anime['averageScore']) if anime['averageScore'] else '',
                            'source': 'AniList'
                        }
                        all_anime_data.append(anime_data)
                    
                    print(f"Page {page}: Added {len(page_data['media'])} anime. Total: {len(all_anime_data)}")
                    

                    if not page_data['pageInfo']['hasNextPage']:
                        print("Reached last page")
                        break
                
                time.sleep(1) 
                
            except Exception as e:
                print(f"Error with AniList API page {page}: {e}")
                continue
        
        return all_anime_data


def create_selenium_scraper():
    """Instructions for Selenium-based scraping"""
    selenium_code = '''
# Install: pip install selenium webdriver-manager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def selenium_crunchyroll_scraper():
    # Setup Chrome options
    options = Options()
    options.add_argument('--headless')  # Run in background
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    # Initialize driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get("https://www.crunchyroll.com/videos/anime/popular")
        time.sleep(5)  # Wait for page load
        
        # Extract anime links
        anime_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/series/']")
        
        for element in anime_elements[:10]:  # Limit for demo
            anime_url = element.get_attribute('href')
            print(f"Found anime: {anime_url}")
            
    finally:
        driver.quit()
'''
    return selenium_code

# Main execution function
def main():
    print("Crunchyroll Direct Scraping Failed - Using Alternative Approaches")
    print("=" * 60)
    
    # Approach 1: Try MyAnimeList
    print("\\n1. Trying MyAnimeList scraper...")
    alt_scraper = AlternativeAnimeScraper()
    
    try:
        mal_data = alt_scraper.scrape_myanimelist(num_pages=100)  # This will get ~5000 anime
        if mal_data:
            print(f"Successfully scraped {len(mal_data)} entries from MyAnimeList")
            save_to_csv(mal_data, 'newanimelist_data.csv')
            display_sample_data(mal_data, "MyAnimeList")
    except Exception as e:
        print(f"MyAnimeList scraping failed: {e}")
    
    # Approach 2: Try AniList API
    print("\\n2. Trying AniList API...")
    try:
        anilist_data = alt_scraper.scrape_anilist_api()
        if anilist_data:
            print(f"Successfully fetched {len(anilist_data)} entries from AniList API")
            save_to_csv(anilist_data, 'anilist_data.csv')
            display_sample_data(anilist_data, "AniList")
    except Exception as e:
        print(f"AniList API failed: {e}")
    
    # Approach 3: Provide Selenium instructions
    print("\\n3. For Crunchyroll specifically, consider using Selenium:")
    print("Run: pip install selenium webdriver-manager")
    print("Then use the selenium approach shown in the comments.")

def save_to_csv(data, filename):
    """Save data to CSV file"""
    if not data:
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
    
    print(f"Data saved to {filename}")

def display_sample_data(data, source_name):
    """Display sample scraped data"""
    print(f"\\nSample data from {source_name}:")
    for i, anime in enumerate(data[:3]):
        print(f"\\n{i+1}. {anime.get('title', 'N/A')}")
        print(f"   Genre: {anime.get('genre', 'N/A')}")
        print(f"   Studio: {anime.get('studio', 'N/A')}")
        print(f"   Episodes: {anime.get('number_of_episodes', 'N/A')}")
        print(f"   Release Date: {anime.get('release_date', 'N/A')}")
        print(f"   Content Type: {anime.get('content_type', 'N/A')}")
        print(f"   Rating: {anime.get('viewer_reviews', 'N/A')}")

if __name__ == "__main__":
    main()