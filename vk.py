import requests
from tok_key import toki



params = f'{toki}' \
         f'extended=1&' \
         f'expires_in=0&' \
         f'order=name&' \
         f'fields=nickname&' \
         f'name_case=gen&' \
         f'user_id=75072907&' \
         f'v=5.131' \
         f'ref'
haders = {"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47"}

url = 'https://api.vk.com/method/friends.get'

response = requests.get(url, params=params, headers=haders)


with open('page.html', 'wb') as f:
    f.write(response.content)

