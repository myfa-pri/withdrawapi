import os
import requests
from io import BytesIO
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# ==============================================================
# 🛠️ SETTINGS
# ==============================================================
BASE_WIDTH = 360  # Reference mobile screen width to scale sizes proportionally

# Font size specs as requested (scaled dynamically to image width):
SIZE_AMOUNT = 26      # Times New Roman Regular for the main withdrawal amount
SIZE_DETAILS = 20     # Times New Roman Bold for right-aligned table values (Time, Name, Trx ID)
SIZE_CLOCK = 16       # Times New Roman Regular for the top status bar time
# ==============================================================

FONT_REG_PATH = "/tmp/TimesNewRoman.ttf"
FONT_BOLD_PATH = "/tmp/TimesNewRomanBold.ttf"
FONT_AM_PATH = "/tmp/NotoSansEthiopicBold.ttf"

# Updated to use only your new template image
TEMPLATE_URL = "https://github.com/user-attachments/assets/ea995e13-3e77-4c3f-866d-be997b0a6e8b"


def scaled(size_px, width):
    return int(round(size_px * (width / BASE_WIDTH)))


def download_fonts():
    # 1. Download Times New Roman Regular
    if not os.path.exists(FONT_REG_PATH) or os.path.getsize(FONT_REG_PATH) < 10000:
        reg_font_urls = [
            "https://raw.githubusercontent.com/justrajdeep/fonts/master/Times%20New%20Roman.ttf",
            "https://raw.githubusercontent.com/google/fonts/main/ofl/notoserif/NotoSerif-Regular.ttf",
        ]
        for url in reg_font_urls:
            try:
                r = requests.get(url, timeout=10)
                if r.ok and len(r.content) > 10000:
                    with open(FONT_REG_PATH, "wb") as f:
                        f.write(r.content)
                    break
            except Exception:
                continue

    # 2. Download Times New Roman Bold
    if not os.path.exists(FONT_BOLD_PATH) or os.path.getsize(FONT_BOLD_PATH) < 10000:
        bold_font_urls = [
            "https://raw.githubusercontent.com/justrajdeep/fonts/master/Times%20New%20Roman%20Bold.ttf",
            "https://raw.githubusercontent.com/google/fonts/main/ofl/notoserif/NotoSerif-Bold.ttf",
        ]
        for url in bold_font_urls:
            try:
                r = requests.get(url, timeout=10)
                if r.ok and len(r.content) > 10000:
                    with open(FONT_BOLD_PATH, "wb") as f:
                        f.write(r.content)
                    break
            except Exception:
                continue

    # 3. Download Amharic Bold Font (Fallback for Amharic names)
    if not os.path.exists(FONT_AM_PATH) or os.path.getsize(FONT_AM_PATH) < 10000:
        am_font_urls = [
            "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansethiopic/NotoSansEthiopic-Bold.ttf",
        ]
        for url in am_font_urls:
            try:
                r = requests.get(url, timeout=10)
                if r.ok and len(r.content) > 10000:
                    with open(FONT_AM_PATH, "wb") as f:
                        f.write(r.content)
                    break
            except Exception:
                continue


def is_amharic(text):
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
    try:
        r = requests.get(TEMPLATE_URL, timeout=12)
        if r.ok and len(r.content) > 10000:
            return Image.open(BytesIO(r.content)).convert("RGB")
    except Exception:
        pass
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

        amount = query.get("amount", ["0.00"])[0]
        name = query.get("name", ["User"])[0]
        txid = query.get("txid", [""])[0]
        raw_time = query.get("time", [""])[0]
        mask_txid = query.get("mask_txid", ["false"])[0].lower() == "true"

        # Format Amount correctly
        try:
            formatted_amount = f"{abs(float(amount)):.2f}"
            if "-" in amount:
                formatted_amount = f"-{formatted_amount}"
        except Exception:
            formatted_amount = amount

        # Calculate exact Ethiopian Time (UTC+3)
        eth_now = parse_ethiopia_time(raw_time)
        time_str_full = eth_now.strftime("%Y/%m/%d %H:%M:%S")
        time_str_short = eth_now.strftime("%H:%M")

        if mask_txid and len(txid) >= 7:
            display_txid = txid[:3] + "***" + txid[-3:]
        else:
            display_txid = txid

        img = load_template()
        W, H = img.size
        draw = ImageDraw.Draw(img)

        # Download and load the requested fonts
        download_fonts()
        font_reg = load_font(FONT_REG_PATH, scaled(SIZE_AMOUNT, W), ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
        font_bold = load_font(FONT_BOLD_PATH, scaled(SIZE_DETAILS, W), ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"])
        font_clock = load_font(FONT_REG_PATH, scaled(SIZE_CLOCK, W), ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
        font_am_bold = load_font(FONT_AM_PATH, scaled(SIZE_DETAILS, W), ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"])

        # Clean/Wipe the dynamic regions of the image to prevent double-printing over old elements
        # 1. Clock status bar region
        draw.rectangle([W * 0.04, H * 0.012, W * 0.20, H * 0.04], fill="#FFFFFF")
        # 2. Amount region (stops before the pre-printed (ብር) label on the right)
        draw.rectangle([W * 0.10, H * 0.31, W * 0.70, H * 0.37], fill="#FFFFFF")
        # 3. Details right-aligned regions
        draw.rectangle([W * 0.50, H * 0.422, W * 0.95, H * 0.462], fill="#FFFFFF")  # Time Row
        draw.rectangle([W * 0.45, H * 0.505, W * 0.95, H * 0.545], fill="#FFFFFF")  # Name Row
        draw.rectangle([W * 0.50, H * 0.545, W * 0.95, H * 0.585], fill="#FFFFFF")  # TXID Row

        text_color = "#151515"

        # Render top status bar time (Times New Roman Regular, 16px scaled)
        draw.text((W * 0.06, H * 0.015), time_str_short, fill=text_color, font=font_clock)

        # Render numerical amount (Times New Roman Regular, 26px scaled)
        # Positioned right-aligned at W * 0.70 to sit cleanly before the pre-printed (ብር)
        draw.text((W * 0.70, H * 0.345), formatted_amount, fill=text_color, font=font_reg, anchor="rm")

        # Render Transaction Time & ID (Times New Roman Bold, 20px scaled)
        draw.text((W * 0.90, H * 0.442), time_str_full, fill=text_color, font=font_bold, anchor="rm")
        draw.text((W * 0.90, H * 0.565), display_txid, fill=text_color, font=font_bold, anchor="rm")

        # Render Name (Falls back to Noto Sans Ethiopic Bold if the text contains Amharic script)
        name_font = font_am_bold if is_amharic(name) else font_bold
        draw.text((W * 0.90, H * 0.525), name, fill=text_color, font=name_font, anchor="rm")

        # Export image
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-Type', 'image/jpeg')
        self.send_header('Content-Length', str(len(img_byte_arr)))
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
