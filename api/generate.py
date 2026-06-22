import os
import requests
from io import BytesIO
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Use a standard font for text rendering
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/notosansethiopic/NotoSansEthiopic-Medium.ttf"
FONT_PATH = "/tmp/NotoSansEthiopic-Medium.ttf"

def download_font():
    if not os.path.exists(FONT_PATH):
        try:
            r = requests.get(FONT_URL)
            with open(FONT_PATH, "wb") as f:
                f.write(r.content)
        except Exception:
            pass

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        
        # Get query parameters
        amount = query.get("amount", ["0.00"])[0]
        name = query.get("name", ["User"])[0]
        txid = query.get("txid", [""])[0]
        
        # Format Amount correctly (e.g. 50.00)
        try:
            amount = f"{float(amount):.2f}"
        except:
            pass

        # Calculate exact Ethiopian Time (UTC+3)
        utc_now = datetime.now(timezone.utc)
        eth_now = utc_now + timedelta(hours=3)
        time_str = eth_now.strftime("%Y/%m/%d %H:%M:%S")

        # Load your CLEANED image template
        img_url = "https://i.ibb.co/4RcwTkxf/ja.jpg"
        try:
            r = requests.get(img_url)
            img = Image.open(BytesIO(r.content)).convert("RGB")
        except Exception:
            img = Image.new("RGB", (1080, 2400), "#FFFFFF")

        W, H = img.size
        draw = ImageDraw.Draw(img)
        download_font()
        
        # Setup Fonts
        try:
            font_large = ImageFont.truetype(FONT_PATH, int(W * 0.08)) # Big text for Amount
            font_small = ImageFont.truetype(FONT_PATH, int(W * 0.035)) # Smaller text for details
        except Exception:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # 1. Draw Amount (Centered in the gap between '-' and '(ብር)')
        # anchor="mm" centers the text perfectly at the given X/Y coordinates
        draw.text((W * 0.45, H * 0.35), amount, fill="#000000", font=font_large, anchor="mm")

        # 2. Draw Transaction Time (Right-aligned against the margin)
        # anchor="rm" aligns text to the Right-Middle
        draw.text((W * 0.92, H * 0.443), time_str, fill="#000000", font=font_small, anchor="rm")

        # 3. Draw Account Name (Right-aligned)
        draw.text((W * 0.92, H * 0.525), name, fill="#000000", font=font_small, anchor="rm")

        # 4. Draw Transaction ID (Right-aligned)
        draw.text((W * 0.92, H * 0.565), txid, fill="#000000", font=font_small, anchor="rm")

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
