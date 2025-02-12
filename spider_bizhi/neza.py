import requests
from bs4 import BeautifulSoup

url = "https://www.maoyan.com/board/1/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
}
req = requests.get(url,headers=headers)
#req.encoding = "utf-8"
html = req.text
print(html)
# soup = BeautifulSoup(html, 'html.parser')
# print(soup)
# piaofang = soup.find('p', class_='realtime').find('span').find('span').text
# print(piaofang)