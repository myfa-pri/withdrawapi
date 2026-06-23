import requests
from io import BytesIO
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# ==============================================================
# 🛠️ SETTINGS: CHANGE TEXT SIZES HERE (NORMAL NUMBERS!)
# Just type normal numbers. Increase to make it bigger.
# ==============================================================
SIZE_AMOUNT  = 240   # Size of the huge "-60.00 (ብር)" amount
SIZE_DETAILS = 90    # Size of the Date, Name, and Transaction ID
SIZE_CLOCK   = 98    # Size of the time at the top-left of the phone screen
# ==============================================================

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

        # Load your CLEANED image template directly into memory
        img_url = "https://i.ibb.co/4RcwTkxf/ja.jpg"
        try:
            r = requests.get(img_url)
            img = Image.open(BytesIO(r.content)).convert("RGB")
        except Exception:
            img = Image.new("RGB", (1080, 2400), "#FFFFFF")

        W, H = img.size
        draw = ImageDraw.Draw(img)
        
        # DOWNLOAD AMHARIC FONT DIRECTLY INTO MEMORY (Double Server Guarantee)
        try:
            # 1st attempt: Fast jsDelivr CDN
            font_url = "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosansethiopic/NotoSansEthiopic-Bold.ttf"
            font_req = requests.get(font_url, timeout=10)
            
            if font_req.status_code != 200:
                # 2nd attempt: GitHub Raw Fallback
                font_url = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansethiopic/NotoSansEthiopic-Bold.ttf"
                font_req = requests.get(font_url, timeout=10)
                
            font_bytes = BytesIO(font_req.content)
            
            # Apply the easy sizes you set at the top!
            font_large = ImageFont.truetype(font_bytes, SIZE_AMOUNT) 
            font_bytes.seek(0)
            font_small = ImageFont.truetype(font_bytes, SIZE_DETAILS) 
            font_bytes.seek(0)
            font_top = ImageFont.truetype(font_bytes, SIZE_CLOCK) 
        except Exception as e:
            print("Font Error:", e)
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_top = ImageFont.load_default()

        # 0. WIPE THE AREAS CLEAN WITH WHITE BOXES
        draw.rectangle([W * 0.10, H * 0.30, W * 0.90, H * 0.39], fill="#FFFFFF") # Main Amount Area
        draw.rectangle([W * 0.04, H * 0.012, W * 0.18, H * 0.038], fill="#FFFFFF") # Top-Left Phone Clock Area

        # Dark gray color so it looks natural on a screen
        text_color = "#151515"

        # 1. Draw Top-Left Phone Clock
        draw.text((W * 0.06, H * 0.015), time_str_short, fill=text_color, font=font_top)

        # 2. Draw Full Amount perfectly centered
        amount_text = f"-{amount} (ብር)"
        draw.text((W * 0.5, H * 0.345), amount_text, fill=text_color, font=font_large, anchor="mm")

        # 3. Draw Transaction Time (Right-aligned)
        draw.text((W * 0.90, H * 0.442), time_str_full, fill=text_color, font=font_small, anchor="rm")

        # 4. Draw Account Name (Right-aligned)
        draw.text((W * 0.90, H * 0.525), name, fill=text_color, font=font_small, anchor="rm")

        # 5. Draw Transaction ID (Right-aligned with Asterisks)
        draw.text((W * 0.90, H * 0.565), display_txid, fill=text_color, font=font_small, anchor="rm")

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