import pandas as pd
import random
import requests
from bs4 import BeautifulSoup
from urllib.error import URLError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ← 金鑰（要加雙引號）
API_KEY = "AIzaSyD41pjpNTOBZNbb9Y5BaizeDEugqySY8oI"

# 初始化 YouTube API client
youtube = build("youtube", "v3", developerKey=API_KEY)

# 範圍設定
years = list(range(2000, 2025))
billboard_base = "https://en.wikipedia.org/wiki/Billboard_Year-End_Hot_100_singles_of_{}"
kkbox_base    = "https://kma.kkbox.com/charts/yearly/song?terr=tw&lang=tc&year={}"

# 1. 抓 Billboard 年終榜
dfs_en = []
for y in years:
    try:
        df_year = pd.read_html(billboard_base.format(y), header=0)[0]
        if 'Title' in df_year.columns and 'Artist(s)' in df_year.columns:
            df_year = df_year[['Title', 'Artist(s)']].rename(
                columns={'Title':'title','Artist(s)':'artist'}
            )
            dfs_en.append(df_year)
    except (ValueError, URLError):
        continue
df_en = pd.concat(dfs_en, ignore_index=True)

# 2. 抓 KKBOX 年度風雲榜
dfs_cn = []
for y in years:
    try:
        df_year = pd.read_html(kkbox_base.format(y), header=0)[0]
        if '歌曲' in df_year.columns and '演唱' in df_year.columns:
            df_year = df_year[['歌曲','演唱']].head(50).rename(
                columns={'歌曲':'title','演唱':'artist'}
            )
            dfs_cn.append(df_year)
    except (ValueError, URLError):
        continue
df_cn = pd.concat(dfs_cn, ignore_index=True) if dfs_cn else pd.DataFrame(columns=['title','artist'])

# 3. 合併並去重
df = pd.concat([df_en, df_cn], ignore_index=True) \
       .drop_duplicates(subset=['title','artist']) \
       .reset_index(drop=True)

# 4. 隨機抽樣 1000 首
df = df.sample(n=1000, random_state=42).reset_index(drop=True)

# 5. 隨機套用情緒、時間、活動標籤
moods = ["Joyful","Cathartic","Calm","Comforting","Empowering",
         "Romantic","Melancholic","Nostalgic","Excited","Mysterious"]
times = ["morning","afternoon","evening","night"]
acts  = ["relaxing","reflecting","commuting","cooking","date","exercising","journaling"]

df['mood']        = [random.choice(moods) for _ in range(len(df))]
df['time_of_day'] = [random.choice(times) for _ in range(len(df))]
df['activity']    = [random.choice(acts)  for _ in range(len(df))]

# ─── 安裝前置套件 ────────────────────────────────
# python3 -m pip install youtube-search-python

from youtubesearchpython import VideosSearch

# ─── 6. 使用 youtube-search-python 取得真實連結 ────────
def fetch_video_link(query: str) -> str:
    """使用 VideosSearch 抓取第一支影片連結"""
    vs = VideosSearch(query, limit=1)
    results = vs.result().get('result', [])
    if results:
        video_id = results[0]['id']
        return f"https://www.youtube.com/watch?v={video_id}"
    return ""

links = []
total = len(df)
for i, row in enumerate(df.itertuples(), 1):
    link = fetch_video_link(f"{row.title} {row.artist}")
    links.append(link)
    if i % 100 == 0 or i == total:
        print(f"🔗 已處理 {i}/{total} 首歌的連結")
df['youtube_link'] = links

# 7. 加上編號並輸出 CSV
df.insert(0, 'song_id', range(1, len(df)+1))
df.to_csv('music_1000_with_links.csv', index=False, encoding='utf-8-sig')

print("✅ 已生成 music_1000_with_links.csv，含 1000 首歌曲與正確影片連結")
