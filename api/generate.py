import os
import requests
from io import BytesIO
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# ==============================================================
# 🛠️ SETTINGS: EXACT REAL SIZES
# ==============================================================
SIZE_AMOUNT_NUM = 110  # Size of the "-60.00"
SIZE_AMOUNT_AM  = 75   # Size of the "(ብር)"
SIZE_DETAILS    = 40   # Size of Date, Name, TXID
SIZE_CLOCK      = 38   # Size of the top-left phone clock
# ==============================================================

FONT_AM_PATH = "/tmp/amharic.ttf"
FONT_EN_PATH = "/tmp/english.ttf"

def download_fonts():
    # 1. Download Amharic Font (For Name and ብር)
    if not os.path.exists(FONT_AM_PATH) or os.path.getsize(FONT_AM_PATH) < 10000:
        try:
            r = requests.get("https://raw.githubusercontent.com/google/fonts/main/ofl/notosansethiopic/NotoSansEthiopic-Bold.ttf", timeout=10)
            with open(FONT_AM_PATH, "wb") as f: f.write(r.content)
        except: pass

    # 2. Download English Font (For Numbers, Dates, IDs)
    if not os.path.exists(FONT_EN_PATH) or os.path.getsize(FONT_EN_PATH) < 10000:
        try:
            r = requests.get("https://raw.githubusercontent.com/google/fonts/main/apache/roboto/Roboto-Medium.ttf", timeout=10)
            with open(FONT_EN_PATH, "wb") as f: f.write(r.content)
        except: pass

def is_amharic(text):
    # Detects if the text contains any Amharic characters
    for char in text:
        if '\u1200' <= char <= '\u137F':
            return True
    return False

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        
        # Get query parameters
        amount = query.get("amount", ["0.00"])[0]
        name = query.get("name", ["User"])[0]
        txid = query.get("txid", [""])[0]
        
        # Format Amount correctly
        try:
            amount = f"{float(amount):.2f}"
        except:
            pass

        # Calculate exact Ethiopian Time (UTC+3)
        utc_now = datetime.now(timezone.utc)
        eth_now = utc_now + timedelta(hours=3)
        time_str_full = eth_now.strftime("%Y/%m/%d %H:%M:%S")
        time_str_short = eth_now.strftime("%H:%M") # Just Hours:Minutes for the phone clock

        # --- BLEND / HIDE PART OF THE TRANSACTION ID ---
        if len(txid) >= 7:
            display_txid = txid[:3] + "***" + txid[-3:]
        else:
            display_txid = txid

        # Load your CLEANED image template
        img_url = "https://i.ibb.co/4RcwTkxf/ja.jpg"
        try:
            r = requests.get(img_url)
            img = Image.open(BytesIO(r.content)).convert("RGB")
        except Exception:
            img = Image.new("RGB", (1080, 2400), "#FFFFFF")

        W, H = img.size
        draw = ImageDraw.Draw(img)
        
        # --- LOAD FONTS ---
        download_fonts()
        try:
            # Amharic Fonts
            font_am_large = ImageFont.truetype(FONT_AM_PATH, SIZE_AMOUNT_AM)
            font_am_details = ImageFont.truetype(FONT_AM_PATH, SIZE_DETAILS)
            
            # English/Number Fonts
            font_en_large = ImageFont.truetype(FONT_EN_PATH, SIZE_AMOUNT_NUM)
            font_en_details = ImageFont.truetype(FONT_EN_PATH, SIZE_DETAILS)
            font_en_clock = ImageFont.truetype(FONT_EN_PATH, SIZE_CLOCK)
        except:
            font_am_large = font_am_details = font_en_large = font_en_details = font_en_clock = ImageFont.load_default()

        # 0. WIPE THE AREAS CLEAN WITH WHITE BOXES
        draw.rectangle([W * 0.10, H * 0.30, W * 0.90, H * 0.39], fill="#FFFFFF") # Main Amount Area
        draw.rectangle([W * 0.04, H * 0.012, W * 0.18, H * 0.038], fill="#FFFFFF") # Top-Left Phone Clock Area

        text_color = "#151515"

        # 1. Draw Top-Left Phone Clock (Always English)
        draw.text((W * 0.06, H * 0.015), time_str_short, fill=text_color, font=font_en_clock)

        # 2. Draw Full Amount (Numbers in English Font, "(ብር)" in Amharic Font)
        num_text = f"-{amount}"
        am_text = " (ብር)"
        
        # Calculate exactly where to put them so they are perfectly centered together
        w_num = draw.textlength(num_text, font=font_en_large)
        w_am = draw.textlength(am_text, font=font_am_large)
        total_w = w_num + w_am
        start_x = (W - total_w) / 2
        
        draw.text((start_x, H * 0.345), num_text, fill=text_color, font=font_en_large, anchor="lm")
        draw.text((start_x + w_num, H * 0.345), am_text, fill=text_color, font=font_am_large, anchor="lm")

        # 3. Draw Transaction Time & ID (Always English Numbers)
        draw.text((W * 0.90, H * 0.442), time_str_full, fill=text_color, font=font_en_details, anchor="rm")
        draw.text((W * 0.90, H * 0.565), display_txid, fill=text_color, font=font_en_details, anchor="rm")

        # 4. Draw Account Name (Checks if Amharic or English, picks the right font)
        name_font = font_am_details if is_amharic(name) else font_en_details
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