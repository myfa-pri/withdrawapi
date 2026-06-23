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

        # --- BLEND / HIDE PART OF THE TRANSACTION ID ---
        # If the ID is DFL9CXQODJ, it becomes DFL***ODJ
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
        
        # DOWNLOAD AMHARIC FONT DIRECTLY INTO MEMORY
        try:
            font_url = "https://github.com/google/fonts/raw/main/ofl/notosansethiopic/NotoSansEthiopic-Bold.ttf"
            font_req = requests.get(font_url)
            font_bytes = BytesIO(font_req.content)
            
            # --- INCREASED TEXT SIZES TO MATCH ORIGINAL APP ---
            font_large = ImageFont.truetype(font_bytes, int(W * 0.085)) # Bigger Amount Text
            
            font_bytes.seek(0)
            font_small = ImageFont.truetype(font_bytes, int(W * 0.038)) # Bigger Normal text
            
            font_bytes.seek(0)
            font_top = ImageFont.truetype(font_bytes, int(W * 0.042)) # Bigger Phone Clock text
        except Exception:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_top = ImageFont.load_default()

        # 0. WIPE THE AREAS CLEAN WITH WHITE BOXES
        draw.rectangle([W * 0.20, H * 0.31, W * 0.80, H * 0.38], fill="#FFFFFF") # Main Amount Area
        draw.rectangle([W * 0.05, H * 0.015, W * 0.16, H * 0.035], fill="#FFFFFF") # Top-Left Phone Clock Area

        # Use a slightly softer dark color instead of pitch black to blend into a screenshot better
        text_color = "#151515"

        # 1. Draw Top-Left Phone Clock (e.g. 22:54)
        draw.text((W * 0.06, H * 0.015), time_str_short, fill=text_color, font=font_top)

        # 2. Draw Full Amount perfectly centered together: e.g. "-60.00 (ብር)"
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