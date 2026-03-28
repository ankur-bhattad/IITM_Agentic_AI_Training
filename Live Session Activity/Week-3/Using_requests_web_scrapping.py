#If not available --
#!pip3 install beautifulsoup4
import requests
from bs4 import BeautifulSoup

url = "https://blogs.worldbank.org/en/opendata/understanding-country-income--world-bank-group-income-classifica"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Get title
title = soup.find("h1").get_text(strip=True)

# Get main content (paragraphs)
content = []
for p in soup.find_all("p"):
    text = p.get_text(strip=True)
    if text:
        content.append(text)

print("TITLE:\n", title)
print("\nCONTENT:\n")
print("\n".join(content[:5]))  # print first few paragraphs