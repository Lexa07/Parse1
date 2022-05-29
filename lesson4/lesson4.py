from lxml import html
import requests
from pymongo.errors import DuplicateKeyError as dke
from pymongo import MongoClient



url = 'https://lenta.ru/'
headers = {"user-agent":"Mozilla/5.0 (Windows NT 10.0; "
                        "Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47"}
response = requests.get(url, headers=headers)

news = html.fromstring(response.text)

items = news.xpath("//a[contains(@class, '_topnews')]")

list_items = []

for item in items:
    item_info = dict()

    link = item.xpath("./@href")[0]
    title = item.xpath(".//*[contains(@class, 'title') and not (contains(@class, 'titles'))]/text()")[0]
    time = item.xpath(".//time[contains(@class, 'date')]/text()")[0]


    item_info['source'] = 'Lenta.ru'  #название источника;
    item_info['title'] = title #наименование новости;
    item_info['link'] = f"(https://lenta.ru{link}"   #ссылку на новость;
    item_info['time'] = time   #дата публикации и время публикации
    list_items.append(item_info)

client = MongoClient('127.0.0.1', 27017)
db = client['GB']
N = db.News_Lenta.ru
for i in range(len(list_items)):
    try:
        N.insert_many(list_items)
    except dke:
        print(f'Повторяется {i}.Уже в базе')

client.close()

