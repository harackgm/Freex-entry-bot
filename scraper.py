import os
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random

# ==========================================
# ブログ エントリーリスト抽出 テスト専用設定
# ==========================================
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")

LOGO_URL = "https://raw.githubusercontent.com/harackgm/Freex-entry-bot/main/freexlogo.png"

# 対象のブログ記事URL
BLOG_URL = "https://freex-areatrout.com/blog/%e3%80%909-3%e6%9b%b4%e6%96%b0%e3%80%91freex-japan-open-%e5%90%84%e5%a4%a7%e4%bc%9a%e3%82%a8%e3%83%b3%e3%83%88%e3%83%aa%e3%83%bc%e3%83%aa%e3%82%b9%e3%83%88%e4%b8%80%e8%a6%a7%ef%bc%88%e9%9a%8f%e6%99%82/"

HEADERS_BASE = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def safe_encode_url(url, bust_cache=False):
    if not url: return ""
    parsed = urllib.parse.urlparse(url)
    encoded_path = urllib.parse.quote(parsed.path)
    query = parsed.query
    if bust_cache:
        timestamp = int(time.time())
        query = f"{query}&t={timestamp}" if query else f"t={timestamp}"
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, encoded_path, parsed.params, query, parsed.fragment))

def send_line_payload(messages_payload):
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("[エラー] トークン未設定")
        return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {"to": LINE_USER_ID, "messages": messages_payload}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        print("LINE通知（テスト）の送信に成功しました。")
    except Exception as e:
        print(f"LINE通知エラー: {e}")

def send_entry_list_flex(match_name, img_url, blog_url):
    """エントリーリスト画像用のFlex Message"""
    # キャッシュ回避用スタンプを付与
    safe_img_url = safe_encode_url(img_url, bust_cache=True)
    
    flex_payload = [{
        "type": "flex",
        "altText": f"📋 エントリーリスト公開: {match_name}",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box", "layout": "vertical", "paddingAll": "none", "backgroundColor": "#0B2545",
                "contents": [
                    {"type": "image", "url": LOGO_URL, "size": "full", "aspectRatio": "20:7", "aspectMode": "cover"},
                    {
                        "type": "box", "layout": "vertical", "paddingAll": "md",
                        "contents": [{"type": "text", "text": "📋 エントリーリスト公開", "weight": "bold", "color": "#FFFFFF", "size": "sm"}]
                    }
                ]
            },
            "hero": {
                # 画像をタップすると全画面で確認できるようにする
                "type": "image", "url": safe_img_url, "size": "full", "aspectRatio": "3:4", "aspectMode": "fit",
                "action": {"type": "uri", "uri": safe_img_url}
            },
            "body": {
                "type": "box", "layout": "vertical",
                "contents": [
                    {"type": "text", "text": match_name, "weight": "bold", "size": "md", "wrap": True, "align": "center"}
                ]
            },
            "footer": {
                "type": "box", "layout": "vertical",
                "contents": [{"type": "button", "action": {"type": "uri", "label": "ブログページで確認する", "uri": blog_url}, "style": "primary", "color": "#0B2545", "height": "sm"}]
            }
        }
    }]
    send_line_payload(flex_payload)

def fetch_html(url):
    time.sleep(random.uniform(2.0, 4.0))
    try:
        response = requests.get(url, headers=HEADERS_BASE, timeout=12)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"取得エラー: {e}")
        return None

def test_scrape_entry_list():
    html = fetch_html(BLOG_URL)
    if not html:
        return

    soup = BeautifulSoup(html, "html.parser")
    
    # 抽出テスト用：すでに画像がある「キングフィッシャー戦」を探す
    target_keyword = "キングフィッシャー戦"
    
    for p_tag in soup.find_all("p"):
        text = p_tag.get_text(strip=True)
        if target_keyword in text:
            # 大会名の次の要素が <figure>（画像） かどうかを確認
            next_sibling = p_tag.find_next_sibling()
            if next_sibling and next_sibling.name == "figure":
                img_tag = next_sibling.find("img")
                if img_tag:
                    img_url = img_tag.get("src")
                    print(f"【抽出成功】{text}")
                    print(f"【画像URL】{img_url}")
                    
                    # LINEへテスト通知
                    send_entry_list_flex(text, img_url, BLOG_URL)
                    return
    
    print("指定した大会の画像が見つかりませんでした。")

def main():
    print("【ブログ画像抽出・テスト通知を開始します】")
    test_scrape_entry_list()

if __name__ == "__main__":
    main()
