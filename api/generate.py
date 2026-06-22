import requests
from io import BytesIO
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

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

        # Load your CLEANED image template directly into memory
        img_url = "https://i.ibb.co/4RcwTkxf/ja.jpg"
        try:
            r = requests.get(img_url)
            img = Image.open(BytesIO(r.content)).convert("RGB")
        except Exception:
            img = Image.new("RGB", (1080, 2400), "#FFFFFF")

        W, H = img.size
        draw = ImageDraw.Draw(img)
        
        # DOWNLOAD AMHARIC FONT DIRECTLY INTO MEMORY
        try:
            font_url = "https://github.com/google/fonts/raw/main/ofl/notosansethiopic/NotoSansEthiopic-Bold.ttf"
            font_req = requests.get(font_url)
            font_bytes = BytesIO(font_req.content)
            
            # INCREASED SIZES HERE:
            font_large = ImageFont.truetype(font_bytes, int(W * 0.095)) # Increased from 0.065 to 0.095 (Huge Amount Text)
            
            font_bytes.seek(0)
            font_small = ImageFont.truetype(font_bytes, int(W * 0.040)) # Increased from 0.032 to 0.040 (Normal Details Text)
            
            font_bytes.seek(0)
            font_top = ImageFont.truetype(font_bytes, int(W * 0.040))   # Increased Phone Clock text
        except Exception:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_top = ImageFont.load_default()

        # 0. WIPE THE AREAS CLEAN WITH WHITE BOXES (Erases old dots, dashes, and phone time)
        draw.rectangle([W * 0.15, H * 0.30, W * 0.85, H * 0.39], fill="#FFFFFF") # Main Amount Area (Made slightly wider)
        draw.rectangle([W * 0.04, H * 0.015, W * 0.18, H * 0.038], fill="#FFFFFF") # Top-Left Phone Clock Area

        # 1. Draw Top-Left Phone Clock (e.g. 22:54)
        draw.text((W * 0.05, H * 0.015), time_str_short, fill="#000000", font=font_top)

        # 2. Draw Full Amount perfectly centered together: e.g. "-60.00 (ብር)"
        amount_text = f"-{amount} (ብር)"
        draw.text((W * 0.5, H * 0.345), amount_text, fill="#000000", font=font_large, anchor="mm")

        # 3. Draw Transaction Time (Right-aligned)
        draw.text((W * 0.90, H * 0.442), time_str_full, fill="#000000", font=font_small, anchor="rm")

        # 4. Draw Account Name (Right-aligned)
        draw.text((W * 0.90, H * 0.525), name, fill="#000000", font=font_small, anchor="rm")

        # 5. Draw Transaction ID (Rig
