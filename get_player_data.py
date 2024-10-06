from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor, as_completed
import time 
import cassiopeia as cass
import os
from dotenv import load_dotenv
import json
import random

load_dotenv()

cass.set_riot_api_key(os.getenv('RIOT_API_KEY'))
cass.apply_settings({'logging': {'print_calls': False}})

SVGdict = {
    'Top': 'M10.4613 6.1538H6.15357V10.4615H10.4613V6.1538ZM13.5382 4.30765V13.5384H4.31603L1.85449 15.9999H15.9997V1.85596L13.5382 4.30765Z',
    'Jungle': 'M11.6308 0C10.4522 1.88571 8.78012 3.91486 7.77268 6.55371C8.20601 7.58 8.56983 8.63606 8.86154 9.71429C9.01436 9.13244 9.19928 8.56008 9.41538 8C9.41538 5.156 10.4433 3.01543 11.6308 0ZM4.98462 9.71429C4.16049 7.15029 2.34831 5.73371 0 4.57143C2.14228 6.36343 2.44911 8.86857 2.76923 11.4286L4.84228 13.3211C5.65754 14.2383 6.93803 15.6863 7.2 16C9.72277 10.6029 5.33575 4.11429 2.76923 0C4.248 3.756 5.38172 5.90971 4.98462 9.71429ZM9.41538 12.5714C9.43959 12.952 9.43959 13.3337 9.41538 13.7143L11.6308 11.4286C11.9509 8.86857 12.2577 6.36343 14.4 4.57143C11.4713 6.02114 10.0434 9.05943 9.41538 12.5714Z',
    'Mid': 'M15.9995 5.51877L13.5331 7.98031L13.538 13.5385H7.99951L5.53797 16H15.9995V5.51877ZM7.98659 2.46154L10.4611 0H-0.000488281V10.4474L2.46105 8V2.46154H7.98782H7.98659Z',
    'Adc': 'M5.53797 9.84615H9.84566V5.53846H5.53797V9.84615ZM-0.000488281 0V14.144L2.43336 11.6825L2.46105 2.46154H11.6832L14.1447 0H-0.000488281Z',
    'Support': 'M15.2941 5.71429C17.3735 5.71429 20 3.42857 20 3.42857H13.5294L11.7647 5.14286L12.9412 9.14286L15.8824 8L14.1176 5.71429H15.2941ZM12.9412 1.14286L12.2512 0H7.68353L7.05882 1.14286L10 4.57143L12.9412 1.14286ZM10 6.28571L9.41177 5.71429L7.64706 14.2857L10 16L12.3529 14.2857L10.5882 5.71429L10 6.28571ZM6.47059 3.42857H0C0 3.42857 2.62647 5.71429 4.70588 5.71429H5.88235L4.11765 8L7.05882 9.14286L8.23529 5.14286L6.47059 3.42857Z'
}
        
def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options)

def get_player_data(url, driver):
    try:
        driver.get(url)
        time.sleep(random.uniform(1, 3))
    
        player_data = {}
        
        # Player Info
        # player country
        flag_img = driver.find_element(By.XPATH, '//img[contains(@src, "flag-icons")]')
        img_src = flag_img.get_attribute('src')
        country_code = img_src.split('/')[-1].split('.')[0]

        # player name
        name_div = flag_img.find_element(By.XPATH, '../following-sibling::div[1]')
        player_name = name_div.text
        
        # player role
        path_element = flag_img.find_element(By.XPATH, '../following-sibling::div[2]')
        d_value = path_element.find_element(By.TAG_NAME, 'path').get_attribute('d')
        role = list(SVGdict.keys())[list(SVGdict.values()).index(d_value)]
        
        # player socials
        social_links = driver.find_elements(By.XPATH, '//ul/li/a[contains(@href, "fandom") or\
        contains(@href, "twitter") or contains(@href, "x") or\
        contains(@href, "youtube") or contains(@href, "twitch") or\
        contains(@href, "instagram")]')
        socials = {}
        for link in social_links:
            href = link.get_attribute('href')
            if 'youtube' in href and 'youtube' not in socials:
                socials['youtube'] = href
            elif ('twitter' in href or 'x.com' in href) and ('x' or 'twitter' not in socials):
                socials['twitter'] = href
            elif 'twitch' in href and 'twitch' not in socials:
                socials['twitch'] = href
            elif 'instagram' in href and 'instagram' not in socials:
                socials['instagram'] = href
            elif ('fandom' in href or 'leaguepedia' in href) and ('leaguepedia' or 'fandom' not in socials):
                socials['leaguepedia'] = href
        
        # Accounts
        opgg_links = driver.find_elements(By.XPATH, '//a[contains(@href, "op.gg")]')
        accounts = []
        for link in opgg_links:
            href = link.get_attribute('href')
            parts = href.split('/') # e.g ['https:', '', 'op.gg', 'summoners', 'LAN', 'StepZ-LAN']
            region = parts[4]
            
            if region not in ["EUW", "NA", "BR", "KR"]:
                continue
            
            name_tagline = parts[5].split('-')
            name = name_tagline[0]
            tagline = name_tagline[1]
            
            try:
                account = cass.get_account(name=name, tagline=tagline, region=region)
                puuid = account.summoner.puuid
                account_id = account.summoner.account_id
                accounts.append({
                    "puuid": puuid,
                    "account_id": account_id,
                    "region": region
                })
            except Exception as e:
                print(f"Error fetching account data for {name}#{tagline} in {region}: {str(e)}")
        
        if not accounts:
            return None
        
        player_data['name'] = player_name
        player_data['country_code'] = country_code
        player_data['role'] = role
        player_data['socials'] = socials
        player_data['accounts'] = accounts
        
        return player_data
    except Exception as e:
        print(f"Error fetching player data for {url}: {str(e)}")
        return None


def scrape_players(player_urls, num_threads=5):
    results = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        drivers = [create_driver() for _ in range(num_threads)]
        future_to_url = {executor.submit(get_player_data, url, drivers[i % num_threads]): url for i, url in enumerate(player_urls)}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                data = future.result()
                if data:
                    results.append(data)
            except Exception as exc:
                print(f'{url} generated an exception: {exc}')
    
    for driver in drivers:
        driver.quit()
    
    return results

# fetch urls from href_links.txt, clean them up and scrape the data
with open('href_links.txt', 'r') as file:
    player_urls = file.readlines()
player_urls = [url.strip() for url in player_urls]

player_data = scrape_players(player_urls)

with open('player_data.json', 'w') as file:
    json.dump(player_data, file, indent=2)