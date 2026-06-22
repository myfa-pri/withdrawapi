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
        time_str = eth_now.strftime("%Y/%m/%d %H:%M:%S")

        # Load your CLEANED image template directly into memory
        img_url = "https://i.ibb.co/4RcwTkxf/ja.jpg"
        try:
            r = requests.get(img_url)
            img = Image.open(BytesIO(r.content)).convert("RGB")
        except Exception:
            img = Image.new("RGB", (1080, 2400), "#FFFFFF")

        W, H = img.size
        draw = ImageDraw.Draw(img)
        
        # DOWNLOAD FONT DIRECTLY INTO MEMORY (Fixes the tiny text issue!)
        try:
            font_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"
            font_req = requests.get(font_url)
            font_bytes = BytesIO(font_req.content)
            
            font_large = ImageFont.truetype(font_bytes, int(W * 0.08)) # Big text
            
            # Reset memory pointer to read the font again for smaller size
            font_bytes.seek(0)
            font_small = ImageFont.truetype(font_bytes, int(W * 0.035)) # Smaller text
        except Exception:
            # Absolute fallback if Vercel has no internet
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # 1. Draw Amount (Centered horizontally, roughly 33% down)
        draw.text((W * 0.44, H * 0.33), amount, fill="#000000", font=font_large, anchor="mm")

        # 2. Draw Transaction Time (Right-aligned)
        draw.text((W * 0.90, H * 0.442), time_str, fill="#000000", font=font_small, anchor="rm")

        # 3. Draw Account Name (Right-aligned)
        draw.text((W * 0.90, H * 0.525), name, fill="#000000", font=font_small, anchor="rm")

        # 4. Draw Transaction ID (Right-aligned)
        draw.text((W * 0.90, H * 0.565), txid, fill="#000000", font=font_small, anchor="rm")

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
