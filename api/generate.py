import requests
from io import BytesIO
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)

        amount = query.get("amount", ["0.00"])[0]
        name = query.get("name", ["User"])[0]
        txid = query.get("txid", [""])[0]

        try:
            amount = f"{float(amount):.2f}"
        except:
            pass

        # Ethiopian Time
        utc_now = datetime.now(timezone.utc)
        eth_now = utc_now + timedelta(hours=3)
        time_str_full = eth_now.strftime("%Y/%m/%d %H:%M:%S")
        time_str_short = eth_now.strftime("%H:%M")

        # TXID mask
        if len(txid) >= 7:
            display_txid = txid[:3] + "***" + txid[-3:]
        else:
            display_txid = txid

        # Load image
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
            font_url = "https://github.com/google/fonts/raw/main/ofl/notosansethiopic/NotoSansEthiopic-Bold.ttf"
            font_bytes = BytesIO(requests.get(font_url).content)

            # 🔥 BIGGER + UI MATCHED SIZES
            font_amount = ImageFont.truetype(font_bytes, int(W * 0.11))  # VERY BIG (main)
            font_bytes.seek(0)
            font_value = ImageFont.truetype(font_bytes, int(W * 0.055))  # values (RIGHT SIDE)
            font_bytes.seek(0)
            font_label = ImageFont.truetype(font_bytes, int(W * 0.048))  # labels (LEFT SIDE)
            font_bytes.seek(0)
            font_top = ImageFont.truetype(font_bytes, int(W * 0.060))  # top clock

        except:
            font_amount = font_value = font_label = font_top = ImageFont.load_default()

        # Clean areas
        draw.rectangle([W*0.15, H*0.30, W*0.85, H*0.40], fill="#FFFFFF")
        draw.rectangle([W*0.04, H*0.01, W*0.20, H*0.06], fill="#FFFFFF")

        text_color = "#111111"
        label_color = "#666666"

        # 1. Top time (BIGGER)
        draw.text((W*0.06, H*0.02), time_str_short, fill=text_color, font=font_top)

        # 2. Amount (CENTER BIG)
        amount_text = f"-{amount} (ብር)"
        draw.text((W*0.5, H*0.35), amount_text, fill=text_color, font=font_amount, anchor="mm")

        # 3. Labels (LEFT SIDE) — BIGGER now
        draw.text((W*0.08, H*0.46), "የግብይት ጊዜ:", fill=label_color, font=font_label)
        draw.text((W*0.08, H*0.52), "የግብይት አይነት:", fill=label_color, font=font_label)
        draw.text((W*0.08, H*0.58), "የግብይት መለያ:", fill=label_color, font=font_label)

        # 4. Values (RIGHT SIDE — LIKE APP)
        draw.text((W*0.92, H*0.46), time_str_full, fill=text_color, font=font_value, anchor="ra")
        draw.text((W*0.92, H*0.52), name,