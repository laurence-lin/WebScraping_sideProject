# WebScraping_sideProject
WebScraping side project for Facebook Reel video data extraction
選取一個 Facebook Reel 短影片, 抓取評論數等資料

操作步驟:

1. Install dependencies:
pip install -r requirements.txt

2. Run web scraping:
python3 webscraping.py

會得到 Reel 影片的 meta data, 輸出兩個檔案: all_comments.json, static_content.json

其中
Reel 所有評論: all_comments.json

Reel 評論數, 表情數, 發文者, 分享數: static_content.json