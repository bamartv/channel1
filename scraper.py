import requests
from bs4 import BeautifulSoup
import json
import time

def get_matches_from_source(url, domain):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://www.google.com/',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        matches = []

        # ၁။ Featured Matches (အပေါ်က Slider ထဲက ပွဲစဉ်တွေ)
        featured_items = soup.find_all('div', class_='swiper-slide')
        for item in featured_items:
            try:
                link_tag = item.find('a')
                if not link_tag: continue
                
                href = link_tag['href']
                
                # အရေးကြီးဆုံးအပိုင်း - Predictions link ကို Match link ဖြစ်အောင်ပြောင်းခြင်း
                final_link = href.replace('/predictions/', '/match/')
                if not final_link.startswith('http'):
                    final_link = f"https://{domain}" + final_link
                
                league = item.find('div', class_='match-header').contents[0].strip()
                match_date = item.find('span', class_='match-date').text.strip()
                
                # အသင်းတံဆိပ် (Logos)
                imgs = item.find_all('img')
                h_logo = imgs[0]['src'] if len(imgs) > 0 else ""
                a_logo = imgs[1]['src'] if len(imgs) > 1 else ""
                
                # အသင်းနာမည် (Team Names)
                teams_text = item.find('div', class_='team-name').get_text(separator="|").split("|")
                h_team = teams_text[0].strip()
                a_team = teams_text[1].strip() if len(teams_text) > 1 else ""

                matches.append({
                    "league": league,
                    "title": f"{h_team} vs {a_team}",
                    "home_team": h_team,
                    "away_team": a_team,
                    "home_logo": h_logo if h_logo.startswith('http') else f"https://{domain}" + h_logo,
                    "away_logo": a_logo if a_logo.startswith('http') else f"https://{domain}" + a_logo,
                    "time": match_date,
                    "link": final_link, # Video တိုက်ရိုက်ကြည့်ရမဲ့ link
                    "is_live": True,
                    "is_featured": True
                })
            except: continue

        # ၂။ Normal Match List (အောက်က ပွဲစဉ်စာရင်းအားလုံး)
        rows = soup.find_all('div', class_='macthline')
        for row in rows:
            try:
                league = row.find('span', class_='league').text.strip()
                date_label = row.find('span', class_='date').text.strip()
                
                link_tag = row.find('a')
                href = link_tag['href']
                
                # Predictions link ကို Match link ဖြစ်အောင်ပြောင်းခြင်း
                final_link = href.replace('/predictions/', '/match/')
                if not final_link.startswith('http'):
                    final_link = f"https://{domain}" + final_link
                
                # xscore808 structure: a > div > span (Home, Time, Away)
                spans = link_tag.find('div').find_all('span')
                h_team = spans[0].text.strip()
                m_time = spans[1].text.strip()
                a_team = spans[2].text.strip()
                
                # Live ဖြစ်မဖြစ် စစ်ဆေးခြင်း
                is_live = "today" in spans[1].get('class', []) or "live" in spans[1].get('class', [])

                matches.append({
                    "league": league,
                    "title": f"{h_team} vs {a_team}",
                    "home_team": h_team,
                    "away_team": a_team,
                    "home_logo": "", 
                    "away_logo": "",
                    "time": f"{date_label} {m_time}",
                    "link": final_link, # Video တိုက်ရိုက်ကြည့်ရမဲ့ link
                    "is_live": is_live,
                    "is_featured": False
                })
            except: continue

        return matches
    except Exception as e:
        print(f"Error while scraping {domain}: {e}")
        return []

def main():
    print("Scraper starting to fetch match data...")
    
    # ymovies.top မှ အရင်ယူမယ်
    final_data = get_matches_from_source("https://ymovies.top/soccerstreams/", "ymovies.top")
    
    # မရရင် xscore808 မှ ထပ်ယူမယ်
    if not final_data:
        print("Ymovies failed, switching to backup: xscore808.com")
        final_data = get_matches_from_source("https://xscore808.com/home/", "xscore808.com")

    # ရလာတဲ့ data အားလုံးကို matches.json ထဲ သိမ်းမယ်
    with open('matches.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)
    
    print(f"Scrape completed! {len(final_data)} matches saved with Direct Video Links.")

if __name__ == "__main__":
    main()
