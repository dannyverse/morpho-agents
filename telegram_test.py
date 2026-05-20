import requests

TOKEN = "8872667197:AAFC-2F7mr29f10kv3CGKGg5AiCDcoxj0wg"

url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

response = requests.get(url)

print(response.json())