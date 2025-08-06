from datetime import datetime
import pytz
import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup headless Chrome
firefox_options = Options()
firefox_options.add_argument("--headless")

driver = webdriver.Firefox(options=firefox_options)

webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

driver.get("https://www.forexfactory.com/calendar")

try:
    # Wait up to 15 seconds for the table to appear
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "calendar__table"))
    )
    html = driver.page_source
finally:
    driver.quit()

soup = BeautifulSoup(html, 'html.parser')
table = soup.find("table", class_="calendar__table")

texts = []

sg_tz = pytz.timezone("Asia/Singapore")
today_sg = datetime.now(sg_tz)

today_str = today_sg.strftime("%b %-d")
year_str = today_sg.strftime("%Y")

print(today_str, year_str)
print(table.prettify())

idx_0 = None
idx_1 = None

impact_dict = {
    'red': '🔴',
    'ora': '🟠',
    'yel': '🟡',
    'gra': '⚪'
}

for idx, row in enumerate(table.find_all('tr')):
    cls = row.get('class')
    if 'calendar__row--day-breaker' in cls:
        td = row.find("td")  # or from your list of td[0]
        weekday = td.contents[0].strip()
        span_text = td.find("span").get_text(strip=True)
        if span_text == today_str:
            idx_0 = idx
            continue
        if idx_0:
            idx_1 = idx
            break

texts.append(f"__**News for {today_str} {year_str}**__\n")
texts.append("\n")

for row in table.find_all('tr')[idx_0+1:idx_1]:
    if 'calendar__row--no-event' in row.get('class'):
        texts.append("NO NEWS")
        break
    
    currency_td = row.find("td", class_="calendar__currency")
    if currency_td:
        currency = currency_td.get_text(strip=True)
        if currency not in ["USD"]:
            continue

    time_td = row.find("td", class_="calendar__time")
    if time_td:
        t = time_td.get_text(strip=True)

    impact_td = row.find("td", class_="calendar__impact")
    if impact_td:
        span = impact_td.find("span")
        if span:
            classes = span.get("class", [])
            # Find the specific class that starts with 'icon--ff-impact'
            impact_class = next((cls for cls in classes if cls.startswith("icon--ff-impact")), None)
            impact_class = impact_class[-3:]
            impact = impact_dict[impact_class]
              # Output: icon--ff-impact-yel

    event_td = row.find("td", class_="calendar__event")
    if event_td:
        title_span = event_td.find("span", class_="calendar__event-title")
        if title_span:
            title = title_span.get_text(strip=True)

    forecast_td = row.find("td", class_="calendar__forecast")
    if forecast_td:
        forecast = forecast_td.get_text(strip=True)

    previous_td = row.find("td", class_="calendar__previous")
    if previous_td:
        span = previous_td.find("span")
        if span:
            previous = span.get_text(strip=True)

    texts.append(f"{impact} {currency} [{t:>7}] {title} [P: {previous if previous else '-'} | F: {forecast if forecast else '-'}]\n")

big_string = "".join(texts[:2]) + "```\n" + "".join(texts[2:]) + "\n```"
print(big_string)

# payload = {
#     "content": big_string
# }

# response = requests.post(webhook_url, json=payload)

# if response.status_code == 204:
#     print("✅ Message sent to Discord")
# else:
#     print(f"❌ Error: {response.status_code} - {response.text}")