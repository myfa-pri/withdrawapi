import requests
from io import BytesIO
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)

        # Get parameters
        amount = query.get("amount", ["0.00"])[0]
        name = query.get("name", ["User"])[0]
        txid = query.get("txid", [""])[0]

        # Format amount
        try:
            amount = f"{float(amount):.2f}"
        except:
            pass

        # Ethiopian Time (UTC+3)
        utc_now = datetime.now(timezone.utc)
        eth_now = utc_now + timedelta(hours=3)

        time_str_full = eth_now.strftime("%Y/%m/%d %H:%M:%S")
        time_str_short = eth_now.strftime("%H:%M")

        # Hide TXID
        if len(txid) >= 7:
            display_txid = txid[:3] + "***" + txid[-3:]
        else:
            display_txid = txid

        # Load template
        img_url = "https://i.ibb.co/4RcwTkxf/ja.jpg"
        try:
            r = requests.get(img_url)
            img = Image.open(BytesIO(r.content)).convert("RGB")
        except:
            img = Image.new("RGB", (1080, 2400), "#FFFFFF")

        W, H = img.size
        draw = ImageDraw.Draw(img)

        # Load font
        try:
            font_url = "https://github.com/google/fonts/raw/main/ofl/notosansethiopic/NotoSansEthiopic-Regular.ttf"
            font_req = requests.get(font_url)
            font_bytes = BytesIO(font_req.content)

            base = W / 1080  # scale factor

            font_large = ImageFont.truetype(font_bytes, int(110 * base))   # BIG
            font_bytes.seek(0)
            font_medium = ImageFont.truetype(font_bytes, int(52 * base))  # medium
            font_bytes.seek(0)
            font_small = ImageFont.truetype(font_bytes, int(42 * base))   # small
            font_bytes.seek(0)
            font_top = ImageFont.truetype(font_bytes, int(46 * base))     # clock

        except:
            font_large = font_medium = font_small = font_top = ImageFont.load_default()

        # Clean areas
        draw.rectangle([W * 0.2, H * 0.30, W * 0.8, H * 0.40], fill="#FFFFFF")
        draw.rectangle([W * 0.05, H * 0.01, W * 0.18, H * 0.05], fill="#FFFFFF")

        # --- TOP CLOCK ---
        draw.text((W * 0.06, H * 0.02), time_str_short, fill="#111111", font=font_top)

        # --- AMOUNT (BIG + SHADOW) ---
        amount_text = f"-{amount} ብር"

        # shadow
        draw.text((W * 0.502, H * 0.352), amount_text, fill="#000000", font=font_large, anchor="mm")
        # main
        draw.text((W * 0.5, H * 0.35), amount_text, fill="#111111", font=font_large, anchor="mm")

        # --- RIGHT SIDE TEXTS ---
        draw.text((W * 0.92, H * 0.44), time_str_full, fill="#222222", font=font_medium, anchor="rm")

        draw.text((W * 0.92, H * 0.525), name, fill="#111111", font=font_medium, anchor="rm")

        draw.text((W * 0.92, H * 0.575), display_txid, fill="#333333", font=font_small, anchor="rm")

        # Export
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr = img_byte_arr.getvalue()

        # Response
        self.send_response(200)
        self.send_header('Content-Type', 'image/jpeg')
        self.send_header('Content-Length', str(len(img_byte_arr)))
        self.end_headers()
        self.wfile.write(img_byte_arr)