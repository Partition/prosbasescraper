from selenium import webdriver
from selenium.webdriver.common.by import By
import json

driver = webdriver.Chrome()

# could have just used robot.txt's sitemap to get the urls
page = 1
with open('href_links.txt', 'a') as file:
    while True:
        url = f"https://prosbase.com/?page={page}"
        driver.get(url)
        table = driver.find_element(By.CSS_SELECTOR, "table.table-auto.min-w-full.w-auto.rounded")
        if table.find_element(By.TAG_NAME, "td").text == "No Result":
            print("No more results, last page was: ", page)
            break
        for row in table.find_elements(By.TAG_NAME, "tr"):
            for cell in row.find_elements(By.TAG_NAME, "td"):
                try:
                    a_tag = cell.find_element(By.XPATH, './/a[contains(@class, "flex") and contains(@href, "/lol/player/")]')
                    
                    href_value = a_tag.get_attribute("href")
                    
                    print(href_value)                
                    file.write(href_value + '\n')
                except:
                    continue
        page += 1
driver.quit()