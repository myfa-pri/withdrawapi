import os
import requests
from io import BytesIO
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# ==============================================================
# 🛠️ SETTINGS
# ==============================================================
BASE_WIDTH = 1080
SIZE_AMOUNT_NUM = 124  # Size of the "-60.00"
SIZE_AMOUNT_AM = 96    # Size of "(ብር)"
SIZE_DETAILS = 44      # Size of Date
SIZE_NAME_TXID = 54    # Size of Name and TXID
SIZE_CLOCK = 40        # Size of the top-left phone clock
# ==============================================================

FONT_AM_PATH = "/tmp/amharic.ttf"
FONT_EN_PATH = "/tmp/english.ttf"
DEFAULT_TEMPLATE_URLS = [
    "https://github.com/user-attachments/assets/47906285-fc13-4a82-ba02-2d93bd778c6c",
    "https://github.com/user-attachments/assets/5be0258a-7ef7-4a61-9beb-4827f40b52df",
    "https://i.ibb.co/4RcwTkxf/ja.jpg",
]


def scaled(size, width):
    return max(12, int(round(size * (width / BASE_WIDTH))))


def download_fonts():
    # 1. Download Amharic Font (For Name and ብር)
    if not os.path.exists(FONT_AM_PATH) or os.path.getsize(FONT_AM_PATH) < 10000:
        amharic_font_urls = [
            "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansethiopic/NotoSansEthiopic%5Bwght%5D.ttf",
            "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansethiopic/NotoSansEthiopic-Bold.ttf",
        ]
        for url in amharic_font_urls:
            try:
                r = requests.get(url, timeout=10)
                if r.ok and len(r.content) > 10000:
                    with open(FONT_AM_PATH, "wb") as f:
                        f.write(r.content)
                    break
            except Exception:
                continue

    # 2. Download English Font (For Numbers, Dates, IDs)
    if not os.path.exists(FONT_EN_PATH) or os.path.getsize(FONT_EN_PATH) < 10000:
        english_font_urls = [
            "https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/Roboto%5Bwdth,wght%5D.ttf",
            "https://raw.githubusercontent.com/google/fonts/main/apache/roboto/Roboto-Medium.ttf",
        ]
        for url in english_font_urls:
            try:
                r = requests.get(url, timeout=10)
                if r.ok and len(r.content) > 10000:
                    with open(FONT_EN_PATH, "wb") as f:
                        f.write(r.content)
                    break
            except Exception:
                continue


def is_amharic(text):
    # Detects if the text contains any Amharic characters
    for char in text:
        if '\u1200' <= char <= '\u137F':
            return True
    return False


def parse_ethiopia_time(raw_time):
    if not raw_time:
        utc_now = datetime.now(timezone.utc)
        return utc_now + timedelta(hours=3)

    formats = ["%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M"]
    for fmt in formats:
        try:
            parsed = datetime.strptime(raw_time, fmt)
            return parsed.replace(tzinfo=timezone(timedelta(hours=3)))
        except ValueError:
            continue

    try:
        parsed = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone(timedelta(hours=3)))
        return parsed.astimezone(timezone(timedelta(hours=3)))
    except ValueError:
        utc_now = datetime.now(timezone.utc)
        return utc_now + timedelta(hours=3)


def load_template():
    for img_url in DEFAULT_TEMPLATE_URLS:
        try:
            r = requests.get(img_url, timeout=12)
            if r.ok and len(r.content) > 10000:
                return Image.open(BytesIO(r.content)).convert("RGB")
        except Exception:
            continue
    return Image.new("RGB", (1080, 2400), "#FFFFFF")


def load_font(path, size, fallback_paths):
    try:
        if os.path.exists(path) and os.path.getsize(path) > 10000:
            return ImageFont.truetype(path, size)
    except Exception:
        pass

    for fallback in fallback_paths:
        try:
            return ImageFont.truetype(fallback, size)
        except Exception:
            continue
    return ImageFont.load_default()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)

        # Get query parameters
        amount = query.get("amount", ["0.00"])[0]
        name = query.get("name", ["User"])[0]
        txid = query.get("txid", [""])[0]
        raw_time = query.get("time", [""])[0]
        mask_txid = query.get("mask_txid", ["false"])[0].lower() == "true"

        # Format Amount correctly
        try:
            amount = f"{abs(float(amount)):.2f}"
        except Exception:
            amount = "0.00"

        # Calculate exact Ethiopian Time (UTC+3)
        eth_now = parse_ethiopia_time(raw_time)
        time_str_full = eth_now.strftime("%Y/%m/%d %H:%M:%S")
        time_str_short = eth_now.strftime("%H:%M")

        # Optional TXID masking
        if mask_txid and len(txid) >= 7:
            display_txid = txid[:3] + "***" + txid[-3:]
        else:
            display_txid = txid

        # Load image template
        img = load_template()

        W, H = img.size
        draw = ImageDraw.Draw(img)

        # --- LOAD FONTS ---
        download_fonts()
        font_am_large = load_font(FONT_AM_PATH, scaled(SIZE_AMOUNT_AM, W), ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
        font_am_details = load_font(FONT_AM_PATH, scaled(SIZE_DETAILS, W), ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
        font_am_name_txid = load_font(FONT_AM_PATH, scaled(SIZE_NAME_TXID, W), ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
        font_en_large = load_font(FONT_EN_PATH, scaled(SIZE_AMOUNT_NUM, W), ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
        font_en_details = load_font(FONT_EN_PATH, scaled(SIZE_DETAILS, W), ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
        font_en_name_txid = load_font(FONT_EN_PATH, scaled(SIZE_NAME_TXID, W), ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
        font_en_clock = load_font(FONT_EN_PATH, scaled(SIZE_CLOCK, W), ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])

        # 0. WIPE THE AREAS CLEAN WITH WHITE BOXES
        draw.rectangle([W * 0.10, H * 0.30, W * 0.90, H * 0.39], fill="#FFFFFF")
        draw.rectangle([W * 0.04, H * 0.012, W * 0.18, H * 0.038], fill="#FFFFFF")

        text_color = "#151515"

        # 1. Draw Top-Left Phone Clock (Always English)
        draw.text((W * 0.06, H * 0.015), time_str_short, fill=text_color, font=font_en_clock)

        # 2. Draw Full Amount (Numbers in English Font, "(ብር)" in Amharic Font)
        num_text = f"-{amount}"
        am_text = " (ብር)"

        # Calculate exactly where to put them so they are centered together
        w_num = draw.textlength(num_text, font=font_en_large)
        total_w = w_num + draw.textlength(am_text, font=font_am_large)
        start_x = (W - total_w) / 2

        draw.text((start_x, H * 0.345), num_text, fill=text_color, font=font_en_large, anchor="lm")
        draw.text((start_x + w_num, H * 0.345), am_text, fill=text_color, font=font_am_large, anchor="lm")

        # 3. Draw Transaction Time & ID (Always English Numbers)
        draw.text((W * 0.90, H * 0.442), time_str_full, fill=text_color, font=font_en_details, anchor="rm")
        draw.text((W * 0.90, H * 0.565), display_txid, fill=text_color, font=font_en_name_txid, anchor="rm")

        # 4. Draw Account Name (Checks if Amharic or English, picks the right font)
        name_font = font_am_name_txid if is_amharic(name) else font_en_name_txid
        draw.text((W * 0.90, H * 0.525), name, fill=text_color, font=name_font, anchor="rm")

        # Export image back to bytes
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr = img_byte_arr.getvalue()

        # Send Image Response
        self.send_response(200)
        self.send_header('Content-Type', 'image/jpeg')
        self.send_header('Content-Length', str(len(img_byte_arr)))
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
