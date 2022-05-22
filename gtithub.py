import requests

params = {"name": "DataBase", "node_id": "MDEwOlJlcG9zaXRvcnkzNDE1MzQ3NTY="}
url = 'https://api.github.com/users/Lexa07/repos'

response = requests.get(url, params=params)

text = response.json()

print(text)