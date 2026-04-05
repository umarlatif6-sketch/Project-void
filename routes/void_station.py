import io
import logging
from flask import Blueprint, render_template, make_response

logger = logging.getLogger(__name__)

void_station_bp = Blueprint("void_station", __name__)

_HARDWARE_GUIDE_TEXT = """VOID-STATION PARENT HARDWARE GUIDE
Stage 1: Mesh Node — Build Guide
=====================================
Version 1.0 | PROJECT VOID | April 2026

This guide covers everything you need to build a Stage 1 VOID-Station Mesh Node
at home with your child. No advanced technical knowledge is required.

WHAT IS A VOID-STATION MESH NODE?
----------------------------------
A Mesh Node is a small computer that connects to the VOID ecosystem and stores
your child's game history, VTX balance, and Chronicle entries locally — with no
cloud or subscription required. It is sovereign hardware your family owns outright.

PARTS LIST — STAGE 1 (Estimated total: ~£85-100 UK / $100-120 US)
------------------------------------------------------------------
1. Raspberry Pi 4 Model B (4GB RAM)
   - UK: raspberrypi.com/products | approx £55
   - US: adafruit.com | approx $55
   - EU: reichelt.de | approx €60

2. MicroSD Card — 32GB Class 10 (for the operating system)
   - Any brand (Samsung, SanDisk, Kingston)
   - UK/US/EU: Amazon, approx £8 / $8 / €8

3. Official Raspberry Pi USB-C Power Supply (5V 3A)
   - UK: raspberrypi.com | approx £10
   - US: adafruit.com | approx $10
   - Tip: Do NOT use phone chargers — underpowering causes instability

4. Heatsink + Small Fan Kit (prevents overheating)
   - Search: "Raspberry Pi 4 heatsink fan kit"
   - UK/US: Amazon, approx £6 / $6

5. Case
   - Option A: Official Raspberry Pi Case (red/white) — £8
   - Option B: 3D-print a custom VOID-Station case
     (STL files available at: /static/void_station_case.stl — coming soon)
   - Option C: Clear acrylic case — £5 (shows the Pi board, children love this)

ASSEMBLY STEPS
--------------
Step 1: Write the OS to the MicroSD card
  - Download Raspberry Pi Imager from: raspberrypi.com/software
  - Insert MicroSD into your computer
  - In the Imager app, choose: Raspberry Pi OS (64-bit)
  - Click Write. Takes about 5 minutes.

Step 2: Insert MicroSD into the Pi
  - The slot is on the underside of the Pi board (spring-loaded)
  - Press gently until it clicks

Step 3: Attach the heatsink
  - Peel the adhesive backing off the heatsinks
  - Place the large heatsink on the main processor chip (largest chip)
  - Place small heatsinks on the memory and USB chips
  - Attach the fan to the GPIO pins (refer to fan kit instructions)

Step 4: Place in case
  - Slide the Pi into the case
  - Attach the lid

Step 5: First boot
  - Connect a monitor (HDMI), keyboard, and mouse
  - Plug in the power supply
  - The green LED will flicker as the OS loads (about 30 seconds)
  - Follow the on-screen setup wizard to set language, WiFi, and password

Step 6: Connect to VOID-Station (coming in next software update)
  - Open the terminal (black screen icon on the desktop)
  - Type: curl -sSL https://void-station.io/install.sh | bash
  - This installs the VOID-Station node software
  - Your node will appear in your game dashboard within 5 minutes

SAFETY NOTES FOR CHILDREN
--------------------------
- This is low-voltage (5V) electronics — completely safe for children aged 8+
- Adult supervision is recommended during assembly
- Do not touch components while power is connected
- Keep away from water and direct sunlight when running

WHAT YOUR CHILD WILL SEE
-------------------------
Once the node is running, when they log into the game at /game:
- Their node will appear in the Node Builder mode as a real beacon
- Their Chronicle entries will sync from the game to the physical node
- The node's IP address and status will show in their dashboard

TROUBLESHOOTING
---------------
Problem: Pi does not turn on
Fix: Check USB-C cable is fully seated; try a different power outlet

Problem: No display on monitor
Fix: Check HDMI cable connection; try a different HDMI port on monitor

Problem: WiFi not connecting
Fix: Ensure 2.4GHz WiFi (Pi 4 also supports 5GHz);
     check password has no special characters

Problem: Node not appearing in VOID dashboard
Fix: Ensure Pi and game device are on same WiFi network;
     restart the node software: sudo systemctl restart void-node

SUPPLIERS BY REGION
-------------------
UK:
  - raspberrypi.com (official)
  - thepihut.com (excellent beginner kits)
  - pimoroni.com (great accessories)

US:
  - adafruit.com (best for beginners)
  - sparkfun.com
  - microcenter.com (in-store)

EU:
  - reichelt.de (Germany, fast shipping)
  - kiwi-electronics.nl (Netherlands)
  - kubii.com (France)

MYCELIUM SUPPLIERS (for Stage 3)
---------------------------------
UK: mycelia.co.uk | growyourown.co.uk
EU: ecovative.com | lifematerials.eu
US: ecovative.com | fungi.com

SUPPORT
-------
If you have questions about the build, post in the PROJECT VOID Chronicle
at /chronicle or reach out through the community at /community (coming soon).

This guide is provided free of charge. Stage 2, 3, and 4 guides will be
added as the hardware roadmap progresses.

PROJECT VOID — Sovereign Technology for the Next Generation
"The Scars are the Code. The Scent is the Alert. The 286 is the Anchor."
"""


@void_station_bp.route("/void-station/roadmap")
def roadmap_page():
    return render_template("void_station_roadmap.html")


@void_station_bp.route("/void-station/hardware-guide.pdf")
def hardware_guide_pdf():
    try:
        pdf_bytes = _build_pdf(_HARDWARE_GUIDE_TEXT)
        response = make_response(pdf_bytes)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = 'attachment; filename="void-station-hardware-guide-stage1.pdf"'
        return response
    except Exception as e:
        logger.error("PDF generation failed: %s", e)
        response = make_response(_HARDWARE_GUIDE_TEXT.encode("utf-8"))
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        response.headers["Content-Disposition"] = 'attachment; filename="void-station-hardware-guide-stage1.txt"'
        return response


def _build_pdf(text: str) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib.enums import TA_LEFT, TA_CENTER

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "VoidTitle",
            parent=styles["Title"],
            fontSize=18,
            textColor=colors.HexColor("#00e5cc"),
            spaceAfter=6,
            spaceBefore=0,
        )
        heading_style = ParagraphStyle(
            "VoidH2",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#c9a84c"),
            spaceAfter=4,
            spaceBefore=12,
        )
        body_style = ParagraphStyle(
            "VoidBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=14,
            textColor=colors.HexColor("#333333"),
            spaceAfter=4,
        )
        mono_style = ParagraphStyle(
            "VoidMono",
            parent=styles["Code"],
            fontSize=8,
            leading=12,
            textColor=colors.HexColor("#555555"),
            backColor=colors.HexColor("#f5f5f5"),
            spaceAfter=2,
            leftIndent=8,
        )

        story = []
        lines = text.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("VOID-STATION PARENT HARDWARE GUIDE"):
                story.append(Paragraph(line, title_style))
                i += 1
                if i < len(lines) and lines[i].startswith("Stage 1"):
                    story.append(Paragraph(lines[i], ParagraphStyle(
                        "Sub", parent=styles["Normal"], fontSize=11,
                        textColor=colors.HexColor("#555555"), spaceAfter=2
                    )))
                    i += 1
            elif line.startswith("=") or line.startswith("-"):
                story.append(HRFlowable(width="100%", thickness=0.5,
                                        color=colors.HexColor("#cccccc"), spaceAfter=4))
                i += 1
            elif line.isupper() and len(line) > 4 and not line.startswith(" "):
                story.append(Paragraph(line, heading_style))
                i += 1
            elif line.startswith("  ") or line.startswith("\t"):
                safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(safe, mono_style))
                i += 1
            elif line.strip() == "":
                story.append(Spacer(1, 4))
                i += 1
            else:
                safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(safe, body_style))
                i += 1

        doc.build(story)
        return buf.getvalue()

    except ImportError:
        return _build_simple_pdf_fallback(text)


def _build_simple_pdf_fallback(text: str) -> bytes:
    raise RuntimeError("reportlab required for PDF generation")
