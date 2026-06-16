import requests
from django.conf import settings

class YouTubeService:
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')

    def search_videos(self, skill_name, limit=3):
        """Поиск видеоуроков по навыку"""
        url = f"https://www.googleapis.com/y
outube/v3/search?part=snippet&q={skill_name}+tutorial&type=video&maxResults={limit}&key={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200: 
            data = response.json()
            return [
                {
                    "title": item['snippet']['title'],
                    "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                }
                for item in data.get('items', [])
            ]
        return []
