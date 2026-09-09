import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
import urllib.parse
import re
from datetime import datetime, timedelta, timezone

# ==========================================
# 設定項目（★一般公開・全員配信モード★）
# ==========================================
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
STATE_FILE = "freex_state.json"
MAX_NOTIFY_LIMIT = 5  # 大量誤通知ストッパー

LOGO_URL = "https://raw.githubusercontent.com/harackgm/Freex-entry-bot/main/freexlogo.png"
FALLBACK_IMG = "https://freex-areatrout.com/wp-content/themes/theme/ogp_img.jpg"
JST = timezone(timedelta(hours=+9), 'JST')

URLS = {
    "schedule": "https://freex-areatrout.com/event/area-trout-championship-2026/schedule/",
    "result": "https://freex-areatrout.com/event/area-trout-championship-2026/result/",
    "blog_entry": "https://freex-areatrout.com/blog/%e3%80%909-3%e6%9b%b4%e6%96%b0%e3%80%91freex-japan-open-%e5%90%84%e5%a4%a7%e4%bc%9a%e3%82%a8%e3%83%b3%e3%83%88%e3%83%aa%e3%83%bc%e3%83%aa%e3%82%b9%e3%83%88%e4%b8%80%e8%a6%a7%ef%bc%88%e9%9a%8f%e6%99%82/"
}

HEADERS_BASE = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1"
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

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
    """LINE Messaging API (Broadcast Message) - 登録者全員へ一斉送信"""
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("[エラー] トークンが未設定です")
        return
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    # 宛先(to)を指定せず、messagesのみを送ることで全員配信になる
    data = {"messages": messages_payload}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        print("-> LINE通知（全員配信）の送信に成功しました。")
    except Exception as e:
        print(f"-> LINE通知エラー: {e}")

def send_entry_flex(match_name, info, timing_msg="🔔 エントリー状況更新"):
    status_text = info.get("status", "ステータス更新")
    form_url = info.get("form_url", URLS["schedule"])
    flex_payload = [{
        "type": "flex", "altText": f"{timing_msg}: {match_name}",
        "contents": {
            "type": "bubble",
            "header": {"type": "box", "layout": "vertical", "paddingAll": "none", "backgroundColor": "#0B2545", "contents": [{"type": "image", "url": LOGO_URL, "size": "full", "aspectRatio": "20:7", "aspectMode": "cover"}, {"type": "box", "layout": "vertical", "paddingAll": "md", "contents": [{"type": "text", "text": timing_msg, "weight": "bold", "color": "#FFFFFF", "size": "sm"}]}]},
            "body": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": match_name, "weight": "bold", "size": "xl", "wrap": True}, {"type": "box", "layout": "vertical", "margin": "lg", "spacing": "sm", "contents": [{"type": "box", "layout": "baseline", "contents": [{"type": "text", "text": "状態", "color": "#aaaaaa", "size": "sm", "flex": 2}, {"type": "text", "text": status_text, "weight": "bold", "color": "#E53935", "size": "sm", "flex": 5, "wrap": True}]}, {"type": "box", "layout": "baseline", "contents": [{"type": "text", "text": "開催日", "color": "#aaaaaa", "size": "sm", "flex": 2}, {"type": "text", "text": info.get("date", "-"), "color": "#666666", "size": "sm", "flex": 5, "wrap": True}]}, {"type": "box", "layout": "baseline", "contents": [{"type": "text", "text": "会場", "color": "#aaaaaa", "size": "sm", "flex": 2}, {"type": "text", "text": info.get("location", "-"), "color": "#666666", "size": "sm", "flex": 5, "wrap": True}]}, {"type": "box", "layout": "baseline", "contents": [{"type": "text", "text": "受付期間", "color": "#aaaaaa", "size": "sm", "flex": 2}, {"type": "text", "text": info.get("accept_period", "-"), "color": "#666666", "size": "sm", "flex": 5, "wrap": True}]}]}]},
            "footer": {"type": "box", "layout": "vertical", "contents": [{"type": "button", "action": {"type": "uri", "label": "エントリーページを開く", "uri": form_url}, "style": "primary", "color": "#0B2545", "height": "sm"}]}
        }
    }]
    send_line_payload(flex_payload)

def send_result_carousel(match_name, results, match_url, timing_msg="🏆 大会結果速報"):
    bubbles = []
    for idx, player in enumerate(results[:10]):
        rank_label = "🥇 優勝" if idx == 0 else "🥈 第2位" if idx == 1 else "🥉 第3位" if idx == 2 else f"第{idx+1}位"
        raw_img_url = player.get("image", "")
        img_url = safe_encode_url(raw_img_url, bust_cache=True) if raw_img_url else safe_encode_url(FALLBACK_IMG, bust_cache=False)
        bubble = {
            "type": "bubble",
            "header": {"type": "box", "layout": "vertical", "paddingAll": "none", "backgroundColor": "#0B2545", "contents": [{"type": "image", "url": LOGO_URL, "size": "full", "aspectRatio": "20:7", "aspectMode": "cover"}, {"type": "box", "layout": "vertical", "paddingAll": "sm", "paddingStart": "md", "contents": [{"type": "text", "text": timing_msg, "weight": "bold", "color": "#FFFFFF", "size": "xs"}]}]},
            "hero": {"type": "image", "url": img_url, "size": "full", "aspectRatio": "1:1", "aspectMode": "cover"},
            "body": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": rank_label, "weight": "bold", "size": "sm", "color": "#1DB446"}, {"type": "text", "text": player.get("name", "選手名未設定"), "weight": "bold", "size": "lg", "margin": "xs", "wrap": True}, {"type": "text", "text": match_name, "size": "xs", "color": "#888888", "margin": "sm", "wrap": True}]},
            "footer": {"type": "box", "layout": "vertical", "contents": [{"type": "button", "action": {"type": "uri", "label": "結果詳細を見る", "uri": match_url}, "style": "primary", "color": "#0B2545", "height": "sm"}]}
        }
        bubbles.append(bubble)
    if bubbles:
        send_line_payload([{"type": "flex", "altText": f"{timing_msg}: {match_name}", "contents": {"type": "carousel", "contents": bubbles}}])

def send_entry_list_flex(match_name, img_url, blog_url):
    safe_img_url = safe_encode_url(img_url, bust_cache=True)
    flex_payload = [{
        "type": "flex", "altText": f"📋 エントリーリスト更新: {match_name}",
        "contents": {
            "type": "bubble",
            "header": {"type": "box", "layout": "vertical", "paddingAll": "none", "backgroundColor": "#0B2545", "contents": [{"type": "image", "url": LOGO_URL, "size": "full", "aspectRatio": "20:7", "aspectMode": "cover"}, {"type": "box", "layout": "vertical", "paddingAll": "md", "contents": [{"type": "text", "text": "📋 エントリーリスト更新", "weight": "bold", "color": "#FFFFFF", "size": "sm"}]}]},
            "hero": {"type": "image", "url": safe_img_url, "size": "full", "aspectRatio": "3:4", "aspectMode": "fit", "action": {"type": "uri", "uri": safe_img_url}},
            "body": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": match_name, "weight": "bold", "size": "md", "wrap": True, "align": "center"}]},
            "footer": {"type": "box", "layout": "vertical", "contents": [{"type": "button", "action": {"type": "uri", "label": "ブログページで確認する", "uri": blog_url}, "style": "primary", "color": "#0B2545", "height": "sm"}]}
        }
    }]
    send_line_payload(flex_payload)

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"schedule": {}, "result": {}, "blog_entry_list": {}}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

def fetch_html(url, label):
    print(f"[{label}] 取得開始...")
    headers = HEADERS_BASE.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    max_retries = 3
    for attempt in range(max_retries):
        time.sleep(random.uniform(2.0, 5.0))
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            print(f"[{label}] 取得成功！")
            return response.text
        except Exception as e:
            print(f"[{label}] 取得エラー（{attempt + 1}回目）: {e}")
            if attempt == max_retries - 1:
                print(f"[{label}] 最大リトライ到達。スキップします。")
                return None
            time.sleep(random.uniform(5.0, 10.0))

def get_image_info(url):
    if not url: return {"url": None, "size": None}
    headers = HEADERS_BASE.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    try:
        response = requests.head(url, headers=headers, timeout=15, allow_redirects=True)
        if response.status_code in [405, 403]:
            response = requests.get(url, headers=headers, timeout=15, stream=True)
        size = response.headers.get("Content-Length")
        return {"url": url, "size": size}
    except Exception as e:
        print(f"画像サイズ取得エラー ({url}): {e}")
        return {"url": url, "size": None}

def parse_entry_start(accept_period):
    if not accept_period: return None
    match = re.search(r'(\d{4}-\d{2}-\d{2})', accept_period)
    if match:
        try:
            dt = datetime.strptime(f"{match.group(1)} 19:00:00", "%Y-%m-%d %H:%M:%S")
            return dt.replace(tzinfo=JST)
        except ValueError:
            pass
    return None

def scrape_schedule(html):
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    table = soup.find("table", class_="schedules-table")
    if not table: return data
    tbody = table.find("tbody")
    if not tbody: return data
    for row in tbody.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) >= 5:
            try:
                match_name = cols[0].get_text(strip=True)
                accept_col = cols[4]
                status_badge = accept_col.find("span", class_="status-badge")
                link_tag = accept_col.find("a")
                data[match_name] = {
                    "date": cols[1].get_text(strip=True),
                    "location": cols[2].get_text(strip=True),
                    "accept_period": accept_col.get_text(strip=True).split('\n')[0].strip(),
                    "status": status_badge.get_text(strip=True) if status_badge else "ステータス不明",
                    "form_url": link_tag.get("href") if link_tag else URLS["schedule"]
                }
            except Exception:
                continue
    return data

def scrape_result(html):
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    for title in soup.find_all("h3", class_="result-item-title"):
        match_name = title.get_text(strip=True)
        results = []
        result_list = title.find_next_sibling("div", class_="result-list")
        if result_list:
            for item in result_list.find_all("div", class_="result-item"):
                try:
                    img = item.find("img")
                    name = item.find("h3")
                    if img and name:
                        results.append({"name": name.get_text(strip=True), "image": img.get("src")})
                except Exception:
                    continue
        data[match_name] = results
    return data

def scrape_blog_entry_list(html):
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    for p_tag in soup.find_all("p"):
        text = p_tag.get_text(strip=True)
        if "戦" in text and ("月" in text or "日" in text):
            img_url = None
            next_node = p_tag.find_next_sibling()
            if next_node and next_node.name == "figure":
                img = next_node.find("img")
                if img:
                    img_url = img.get("src")
            data[text] = img_url
    return data

def has_valid_photo(players):
    if not players: return False
    for p in players:
        img_url = p.get("image", "")
        if img_url and "ogp_img" not in img_url and "no_image" not in img_url:
            return True
    return False

def main():
    now = datetime.now(JST)
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 監視を開始します。")
    old_state = load_state()
    new_state = {"schedule": {}, "result": {}, "blog_entry_list": {}}
    notifications = []

    # 1. スケジュール（エントリー）の監視
    html_schedule = fetch_html(URLS["schedule"], "スケジュール")
    if html_schedule:
        new_state["schedule"] = scrape_schedule(html_schedule)
        for match, info in new_state["schedule"].items():
            old_info = old_state["schedule"].get(match, {})
            entry_start_dt = parse_entry_start(info.get("accept_period", ""))
            
            if "notified" not in old_info:
                if entry_start_dt:
                    notified_flags = {"24h": now >= entry_start_dt - timedelta(hours=24), "15m": now >= entry_start_dt - timedelta(minutes=15), "0m": now >= entry_start_dt, "next_m": now >= entry_start_dt + timedelta(hours=14)}
                else:
                    notified_flags = {"24h": True, "15m": True, "0m": True, "next_m": True}
            else:
                notified_flags = old_info["notified"]

            if entry_start_dt:
                if now >= entry_start_dt - timedelta(hours=24) and not notified_flags["24h"]:
                    notifications.append({"type": "schedule", "match_name": match, "info": info, "timing_msg": "🔔 【予告】エントリー開始24時間前"})
                    notified_flags["24h"] = True
                if now >= entry_start_dt - timedelta(minutes=15) and not notified_flags["15m"]:
                    notifications.append({"type": "schedule", "match_name": match, "info": info, "timing_msg": "🔔 【直前】エントリー開始15分前"})
                    notified_flags["15m"] = True
                if now >= entry_start_dt and not notified_flags["0m"]:
                    notifications.append({"type": "schedule", "match_name": match, "info": info, "timing_msg": "🔔 【開始】エントリー受付開始"})
                    notified_flags["0m"] = True
                if now >= entry_start_dt + timedelta(hours=14) and not notified_flags["next_m"]:
                    notifications.append({"type": "schedule", "match_name": match, "info": info, "timing_msg": "🔔 【確認】エントリーはお済みですか？"})
                    notified_flags["next_m"] = True
            info["notified"] = notified_flags
    else:
        new_state["schedule"] = old_state.get("schedule", {})

    # 2. 大会結果の監視
    html_result = fetch_html(URLS["result"], "大会結果")
    if html_result:
        scraped_results = scrape_result(html_result)
        for match, current_players in scraped_results.items():
            old_match_data = old_state.get("result", {}).get(match, {})
            old_players = old_match_data.get("players", [])
            first_detected = old_match_data.get("first_detected", now.isoformat())
            photo_notified = old_match_data.get("photo_notified", True)

            is_new_or_updated = len(current_players) > len(old_players)
            has_photo = has_valid_photo(current_players)
            should_notify = False
            timing_msg = "🏆 大会結果速報"

            if is_new_or_updated:
                should_notify = True
                first_detected = now.isoformat()
                photo_notified = has_photo
            elif not photo_notified:
                first_det_dt = datetime.fromisoformat(first_detected)
                if now < first_det_dt + timedelta(hours=48):
                    if has_photo:
                        should_notify = True
                        photo_notified = True
                        timing_msg = "📸 写真が追加されました"
                else:
                    photo_notified = True

            if should_notify:
                notifications.append({"type": "result_carousel", "match_name": match, "results": current_players, "url": URLS["result"], "timing_msg": timing_msg})

            new_state["result"][match] = {"players": current_players, "first_detected": first_detected, "photo_notified": photo_notified}
    else:
        new_state["result"] = old_state.get("result", {})

    # 3. エントリーリスト（ブログ）の監視
    html_blog = fetch_html(URLS["blog_entry"], "ブログ")
    if html_blog:
        scraped_blog = scrape_blog_entry_list(html_blog)
        old_blog_state = old_state.get("blog_entry_list", {})
        
        for match_name, img_url in scraped_blog.items():
            old_data = old_blog_state.get(match_name)
            img_info = get_image_info(img_url) if img_url else {"url": img_url, "size": None}
            
            if not old_data:
                new_state["blog_entry_list"][match_name] = img_info
            else:
                if isinstance(old_data, str):
                    old_url = old_data
                    old_size = None
                else:
                    old_url = old_data.get("url")
                    old_size = old_data.get("size")
                
                is_updated = False
                if img_url and img_url != old_url:
                    is_updated = True
                elif img_url and img_url == old_url and img_info["size"] and img_info["size"] != old_size:
                    is_updated = True
                    print(f"[{match_name}] 同名ファイルの画像上書き更新を検知しました。")
                
                if is_updated:
                    notifications.append({"type": "blog_entry_list", "match_name": match_name, "img_url": img_url, "blog_url": URLS["blog_entry"]})
                
                new_state["blog_entry_list"][match_name] = img_info
    else:
        new_state["blog_entry_list"] = old_state.get("blog_entry_list", {})

    # ==========================================
    # 大量通知ストッパー（MAX_LIMIT制御）
    # ==========================================
    print(f"\n-> 検知した変更通知件数: {len(notifications)} 件")
    if len(notifications) > MAX_NOTIFY_LIMIT:
        print(f"⚠️ 検知数が上限（{MAX_NOTIFY_LIMIT}件）を超えました。LINE送信をスキップし、DBのみ更新します。")
    else:
        for item in notifications:
            if item["type"] == "schedule":
                send_entry_flex(item["match_name"], item["info"], item["timing_msg"])
            elif item["type"] == "result_carousel":
                send_result_carousel(item["match_name"], item["results"], item["url"], item["timing_msg"])
            elif item["type"] == "blog_entry_list":
                send_entry_list_flex(item["match_name"], item["img_url"], item["blog_url"])
            time.sleep(1)

    save_state(new_state)
    print("監視処理が完了しました。")

if __name__ == "__main__":
    main()
