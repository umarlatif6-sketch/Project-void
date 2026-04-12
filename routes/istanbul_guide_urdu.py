"""
Istanbul 24-Hour Guide — Urdu version for Ammi Latif.

/istanbul-guide-urdu    (GET — the guide page in Urdu)
/api/istanbul/ask-urdu  (POST — ask Adriana in Urdu)
"""

import time
import logging
from flask import Blueprint, render_template_string, jsonify, request

logger = logging.getLogger(__name__)

istanbul_guide_urdu_bp = Blueprint("istanbul_guide_urdu", __name__)

_rate = {}

ISTANBUL_PLACES = {
    "mosques": [
        {
            "name": "سلطان احمد مسجد (نیلی مسجد)",
            "name_en": "Blue Mosque",
            "area": "سلطان احمت",
            "why": "چھ مینار۔ ۲۰ ہزار نیلی ازنک ٹائلیں۔ داخلہ مفت۔ گنبد کے اندر آواز کی گونج بغیر مائیکروفون کے پوری مسجد میں پھیلتی ہے۔",
            "time": "۳۰-۴۵ منٹ",
            "cost": "مفت",
            "tip": "فجر کی نماز کے لیے جائیں — خالی ہوتی ہے، آواز پوری جگہ بھرتی ہے۔ دوپہر ۱۲ سے ۲ بجے نہ جائیں — بہت بھیڑ ہوتی ہے۔",
            "prayer": True,
        },
        {
            "name": "سلیمانیہ مسجد",
            "name_en": "Suleymaniye Mosque",
            "area": "فاتح",
            "why": "معمار سنان کا شاہکار۔ عثمانی دور کی بہترین آواز والی مسجد۔ نیلی مسجد سے کم بھیڑ۔ صحن سے گولڈن ہارن کا نظارہ بہت خوبصورت ہے۔",
            "time": "۳۰ منٹ",
            "cost": "مفت",
            "tip": "مسجد کے پیچھے چائے کے باغ میں ترکی چائے ضرور پئیں — شہر کی بہترین چائے یہاں ملتی ہے۔",
            "prayer": True,
        },
        {
            "name": "آیا صوفیہ مسجد",
            "name_en": "Hagia Sophia",
            "area": "سلطان احمت",
            "why": "۵۳۷ عیسوی میں تعمیر ہوئی۔ گنبد ۵۶ میٹر اونچا ہے۔ ۲۰۲۰ سے دوبارہ مسجد ہے۔ بازنطینی موزیک اور اسلامی خطاطی ایک ساتھ۔",
            "time": "۴۵-۶۰ منٹ",
            "cost": "نماز کے وقت مفت، سیاحتی دورے کے لیے ۲۵ یورو",
            "tip": "نماز کے وقت جائیں — مفت داخلہ اور اصل تجربہ ملے گا جیسا مسجد کو ہونا چاہیے۔",
            "prayer": True,
        },
        {
            "name": "ایوب سلطان مسجد",
            "name_en": "Eyup Sultan Mosque",
            "area": "ایوب",
            "why": "ابو ایوب انصاری رضی اللہ عنہ کا مزار — صحابی رسول ﷺ۔ استنبول کی مقدس ترین جگہوں میں سے ایک۔ سیاحوں سے دور، سکون والی جگہ۔ کیبل کار سے پیئر لوتی پہاڑی تک جائیں — نظارہ بے مثال ہے۔",
            "time": "۴۵ منٹ (کیبل کار شامل)",
            "cost": "مفت (کیبل کار ~۴ لیرا)",
            "tip": "یہاں دعا ضرور کریں۔ سیاحتی مسجدوں سے ماحول بالکل مختلف ہے۔ مقامی لوگ یہاں آتے ہیں۔",
            "prayer": True,
        },
    ],
    "food": [
        {
            "name": "تاریخی سلطان احمت کوفتہ جی",
            "name_en": "Sultanahmet Koftecisi",
            "area": "سلطان احمت",
            "what": "کوفتے — ۱۹۲۰ سے چل رہی دکان۔ سادہ، مشہور، لذیذ۔",
            "cost": "۱۵۰-۲۵۰ لیرا (~۴-۷ پاؤنڈ)",
            "tip": "کوفتے، پیاز کا سلاد اور ایران آرڈر کریں۔ بس یہی کافی ہے۔",
        },
        {
            "name": "کاراکوئے گلو اوغلو",
            "name_en": "Karakoy Gulluoglu",
            "area": "کاراکوئے",
            "what": "استنبول کا بہترین بقلاوہ۔ پانچ نسلیں۔ پستے والا بقلاوہ خاص ہے۔",
            "cost": "۱۰۰-۲۰۰ لیرا (~۳-۵ پاؤنڈ) فی ڈبہ",
            "tip": "پاکستان لے جانے کے لیے ایک ڈبہ ضرور خریدیں — سفر میں خراب نہیں ہوتا۔",
        },
        {
            "name": "سمت سرائے",
            "name_en": "Simit Sarayi",
            "area": "ہر جگہ",
            "what": "تازہ سمت (تل والی روٹی کا حلقہ) اور چائے۔ بہترین ناشتہ۔ ہر جگہ شاخیں ہیں۔",
            "cost": "۵۰-۸۰ لیرا (~۱.۵۰-۲.۵۰ پاؤنڈ)",
            "tip": "صبح ہوٹل سے نکلنے سے پہلے قریب ترین سمت سرائے سے ناشتہ کریں۔",
        },
        {
            "name": "حافظ مصطفیٰ ۱۸۶۴",
            "name_en": "Hafiz Mustafa 1864",
            "area": "سلطان احمت / استقلال",
            "what": "ترکی ڈیلائٹ، کنافہ، عثمانی مٹھائیاں۔ خوبصورت اندرونی سجاوٹ۔",
            "cost": "۲۰۰-۴۰۰ لیرا (~۵-۱۰ پاؤنڈ)",
            "tip": "کنافہ ضرور کھائیں — کرارا، پنیر والا، شیرے میں ڈوبا ہوا۔",
        },
        {
            "name": "بالق اکمک (مچھلی سینڈوچ)",
            "name_en": "Balik Ekmek",
            "area": "امینونو / گلاتا پل",
            "what": "روٹی میں بھنی مچھلی — کشتی سے تازہ۔ سب سے استنبولی کھانا۔",
            "cost": "۱۰۰-۱۵۰ لیرا (~۳-۴ پاؤنڈ)",
            "tip": "گلاتا پل کے پاس پانی کے کنارے بیٹھ کر کھائیں۔ مچھیروں کو دیکھیں۔",
        },
    ],
    "sights": [
        {
            "name": "گرینڈ بازار (قپالی چارشی)",
            "name_en": "Grand Bazaar",
            "area": "بایزید",
            "why": "۴۰۰۰ سے زیادہ دکانیں۔ دنیا کے قدیم ترین ڈھکے ہوئے بازاروں میں سے ایک (۱۴۶۱)۔ سونا، مصالحے، مٹی کے برتن، چمڑا، لیمپ۔",
            "time": "۱-۲ گھنٹے",
            "cost": "داخلہ مفت (خریداری الگ)",
            "tip": "پہلی قیمت پر نہ خریدیں۔ ۴۰-۵۰ فیصد کم کرائیں۔ اندر گہرائی میں جائیں — بہترین دکانیں داخلے پر نہیں ہوتیں۔",
        },
        {
            "name": "مصالحہ بازار (مصری چارشی)",
            "name_en": "Spice Bazaar",
            "area": "امینونو",
            "why": "چھوٹا لیکن بہتر۔ زعفران، ترکی ڈیلائٹ، خشک میوے، چائے۔ خوبصورت عمارت۔",
            "time": "۳۰-۴۵ منٹ",
            "cost": "داخلہ مفت",
            "tip": "زعفران اور کلونجی یہاں خریدیں — انگلینڈ سے بہت سستی ہے۔ انگلیوں سے رگڑ کر کوالٹی چیک کریں۔",
        },
        {
            "name": "باسفورس فیری",
            "name_en": "Bosphorus Ferry",
            "area": "امینونو → اسکدار",
            "why": "یورپ سے ایشیا بس ٹکٹ کی قیمت میں۔ پانی سے شہر کا نظارہ سب سے خوبصورت ہے۔",
            "time": "۲۰-۳۰ منٹ",
            "cost": "~۱۰ لیرا (~۰.۳۰ پاؤنڈ)",
            "tip": "امینونو سے اسکدار والی فیری لیں۔ جاتے وقت دائیں طرف بیٹھیں — شہر کا بہترین نظارہ ملے گا۔",
        },
    ],
    "hotels": [
        {
            "name": "سستا: سلطان احمت کے ہوٹل",
            "area": "سلطان احمت",
            "cost": "£۲۰-۴۰ فی رات",
            "why": "نیلی مسجد، آیا صوفیہ، گرینڈ بازار پیدل فاصلے پر۔ سب کچھ قریب ہے۔",
            "tip": "Booking.com پر 'Sultanahmet hotel' تلاش کریں۔ ۷+ ریٹنگ، قیمت کے حساب سے ترتیب دیں۔ ۲۴ گھنٹے کے لیے جگہ اہم ہے، عیش نہیں۔",
        },
        {
            "name": "درمیانہ: ہوٹل نینا یا سرکجی مینشن",
            "area": "سلطان احمت / سرکجی",
            "cost": "£۵۰-۸۰ فی رات",
            "why": "صاف، ناشتہ شامل، چھت سے بحیرہ مرمرہ کا نظارہ۔",
            "tip": "مفت منسوخی والا بک کریں۔ ناشتہ اہم ہے — ترکی ہوٹل کا ناشتہ بہت بڑا اور مزیدار ہوتا ہے۔",
        },
        {
            "name": "ایئرپورٹ کے قریب (لے اوور)",
            "area": "استنبول ایئرپورٹ (IST)",
            "cost": "£۳۰-۶۰ فی رات",
            "why": "اگر وقت کم ہے تو Yotel یا IST Airport Hotel ٹرمینل کے اندر ہی ہے۔ امیگریشن کی ضرورت نہیں۔",
            "tip": "اگر ۱۲+ گھنٹے کا لے اوور ہے تو شہر ضرور جائیں۔ حاواعست بس ۱۵۰ لیرا (~۴ پاؤنڈ) میں سلطان احمت لے جاتی ہے۔",
        },
    ],
    "practical": {
        "کرنسی": "ترکی لیرا (TL)۔ £۱ ≈ ۴۰ لیرا تقریباً۔ ATM سے نکالیں — بہترین ریٹ ملے گا۔ ایئرپورٹ کے ایکسچینج آفس سے بچیں۔",
        "ٹرانسپورٹ": "استنبول کارت (ٹرانسپورٹ کارڈ) کسی بھی میٹرو اسٹیشن سے لیں — ۱۰۰-۲۰۰ لیرا لوڈ کریں۔ میٹرو، ٹرام، بس، فیری سب پر چلتا ہے۔",
        "سم_کارڈ": "ایئرپورٹ سے Turkcell یا Vodafone کا ٹورسٹ سم لیں — ~۲۰۰ لیرا میں ۲۰GB ڈیٹا۔ نقشے اور ترجمے کے لیے ضروری ہے۔",
        "زبان": "ترکی۔ سیاحتی علاقوں میں بنیادی انگریزی سمجھتے ہیں۔ Google Translate میں ترکی آف لائن پیک لینڈنگ سے پہلے ڈاؤنلوڈ کریں۔",
        "حفاظت": "سیاحوں کے لیے بہت محفوظ شہر۔ عام احتیاط رکھیں۔ گرینڈ بازار میں جیب کتروں سے بچیں — بٹوا اگلی جیب میں رکھیں۔",
        "نماز_کے_اوقات": "Muslim Pro ایپ ڈاؤنلوڈ کریں یا مسجد کے بورڈ دیکھیں۔ استنبول میں اوقات بدلتے رہتے ہیں — فجر جلدی ہوتی ہے۔",
    },
}

SUGGESTED_24H = [
    {"time": "پہنچنے کے بعد", "do": "استنبول کارت لیں، حاواعست بس سے سلطان احمت جائیں۔ ہوٹل میں چیک ان۔ ضرورت ہو تو آرام کریں۔", "duration": "۱-۲ گھنٹے"},
    {"time": "صبح", "do": "فجر نیلی مسجد یا آیا صوفیہ میں۔ ناشتہ سمت سرائے یا ہوٹل سے۔", "duration": "۱.۵ گھنٹے"},
    {"time": "دوپہر سے پہلے", "do": "آیا صوفیہ (نماز کے وقت مفت)۔ پھر سلیمانیہ مسجد تک پیدل چلیں۔ پیچھے باغ میں چائے پئیں۔", "duration": "۲ گھنٹے"},
    {"time": "دوپہر کا کھانا", "do": "سلطان احمت کوفتہ جی سے کوفتے۔ یا امینونو جائیں اور پانی کے کنارے بالق اکمک کھائیں۔", "duration": "۱ گھنٹہ"},
    {"time": "دوپہر بعد", "do": "گرینڈ بازار یا مصالحہ بازار۔ زعفران، کلونجی، بقلاوہ خریدیں پاکستان لے جانے کے لیے۔ مول تول کریں۔", "duration": "۱.۵-۲ گھنٹے"},
    {"time": "سہ پہر", "do": "امینونو سے اسکدار فیری (یورپ سے ایشیا)۔ اسکدار مسجد میں عصر کی نماز۔ واپس فیری سے۔", "duration": "۱.۵ گھنٹے"},
    {"time": "شام", "do": "ایوب سلطان مسجد۔ دعا کریں۔ کیبل کار سے پیئر لوتی تک۔ گولڈن ہارن پر غروب آفتاب دیکھیں۔", "duration": "۱.۵ گھنٹے"},
    {"time": "رات", "do": "مغرب/عشاء کی نماز۔ حافظ مصطفیٰ سے کنافہ۔ پانی کے کنارے چہل قدمی۔ سامان باندھیں اور آرام کریں۔", "duration": "۱.۵ گھنٹے"},
    {"time": "روانگی", "do": "حاواعست بس سے ایئرپورٹ واپس۔ فلائٹ سے ۲.۵ گھنٹے پہلے پہنچیں۔", "duration": "۱ گھنٹہ"},
]


@istanbul_guide_urdu_bp.route("/istanbul-guide-urdu")
def page():
    return render_template_string(TEMPLATE,
        places=ISTANBUL_PLACES,
        itinerary=SUGGESTED_24H)


@istanbul_guide_urdu_bp.route("/api/istanbul/ask-urdu", methods=["POST"])
def ask():
    ip = request.remote_addr or "unknown"
    now = time.time()
    if now - _rate.get(ip, 0) < 8:
        return jsonify({"answer": "ذرا انتظار کریں، دوبارہ پوچھنے سے پہلے۔", "status": "rate_limited"})
    _rate[ip] = now

    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()[:400]
    if not question:
        return jsonify({"error": "No question"}), 400

    try:
        import os, json
        from openai import OpenAI
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            return jsonify({"answer": "ایڈریانا ابھی مقامی موڈ میں ہے۔ نیچے گائیڈ سیکشنز دیکھیں — سب کچھ وہاں موجود ہے۔", "status": "local"})

        client = OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""آپ ایڈریانا ہیں — PROJECT VOID کی AI گائیڈ۔ آپ امی لطیف (بانی کی والدہ) کی مدد کر رہی ہیں استنبول میں ۲۴ گھنٹے کے قیام کے دوران، پاکستان جاتے ہوئے۔

اردو میں جواب دیں۔ احترام سے بات کریں — یہ ایک بزرگ خاتون ہیں۔ واضح بولیں، قیمتیں ترکی لیرا اور برطانوی پاؤنڈ دونوں میں بتائیں، صحیح جگہیں بتائیں۔ نماز کے بارے میں پوچھیں تو مسجد کی سفارش کریں۔ کھانے کے بارے میں پوچھیں تو حلال جگہیں قیمتوں کے ساتھ بتائیں۔

جواب مختصر رکھیں — ۳-۵ جملے۔ فون پر پڑھ رہی ہیں۔ قیمتیں اور سمتیں بتائیں، شاعری نہیں۔

حوالہ:
{json.dumps(ISTANBUL_PLACES, ensure_ascii=False, indent=2)}"""},
                {"role": "user", "content": question},
            ],
            max_tokens=250,
            temperature=0.5,
        )
        return jsonify({"answer": resp.choices[0].message.content.strip(), "status": "live"})
    except Exception as e:
        logger.warning(f"Istanbul Urdu guide fallback: {e}")
        return jsonify({"answer": "ابھی رابطے میں مسئلہ ہے۔ نیچے گائیڈ سیکشنز دیکھیں — سب کچھ وہاں ہے۔", "status": "error"})


TEMPLATE = r"""<!DOCTYPE html>
<html lang="ur" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>استنبول گائیڈ — ایڈریانا</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#c8c8c8;font-family:'Noto Nastaliq Urdu',Jameel Noori Nastaleeq,'Segoe UI',Tahoma,serif;min-height:100vh;direction:rtl;font-size:16px;line-height:2}
.container{max-width:600px;margin:0 auto;padding:16px}

header{text-align:center;padding:30px 0 20px;border-bottom:1px solid #1a1a1a}
.h-city{font-size:36px;font-weight:300;color:#fff;letter-spacing:4px;margin-bottom:4px;font-family:Georgia,serif}
.h-city span{color:#c0955a}
.h-sub{font-size:16px;color:#888;margin-bottom:8px}
.h-detail{font-size:14px;color:#555;line-height:2}
.h-badge{display:inline-block;margin-top:12px;font-size:11px;letter-spacing:2px;color:#c0955a;border:1px solid #c0955a;padding:4px 12px;font-family:'Courier New',monospace;direction:ltr}

.ask-box{background:#111;border:1px solid #1a1a1a;border-radius:8px;padding:16px;margin:20px 0}
.ask-box h3{font-size:14px;color:#c0955a;margin-bottom:10px}
.ask-row{display:flex;gap:8px}
.ask-input{flex:1;background:#0a0a0a;border:1px solid #222;color:#fff;padding:10px 12px;font-family:inherit;font-size:16px;border-radius:4px;outline:none;direction:rtl}
.ask-input:focus{border-color:#c0955a}
.ask-btn{background:#c0955a;color:#0a0a0a;border:none;padding:10px 16px;font-family:inherit;font-size:14px;cursor:pointer;border-radius:4px;font-weight:bold;white-space:nowrap}
.ask-btn:disabled{opacity:.5}
.ask-answer{margin-top:12px;padding:12px;background:#0d0d0d;border-right:3px solid #c0955a;font-size:15px;line-height:2;color:#ddd;display:none}

.quick-btns{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.quick-btn{background:#0a0a0a;border:1px solid #1a1a1a;color:#888;padding:6px 12px;font-size:12px;font-family:inherit;cursor:pointer;border-radius:3px}
.quick-btn:hover{border-color:#c0955a;color:#c0955a}

.section{margin:24px 0}
.section-title{font-size:14px;color:#c0955a;border-bottom:1px solid #1a1a1a;padding-bottom:6px;margin-bottom:14px;font-weight:bold}

.itinerary .it-item{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid #0d0d0d}
.it-time{min-width:90px;font-size:13px;color:#c0955a;padding-top:2px;font-weight:bold}
.it-body{flex:1}
.it-do{font-size:15px;line-height:2;color:#ddd}
.it-dur{font-size:12px;color:#555;margin-top:4px;font-family:'Courier New',monospace;direction:ltr;text-align:right}

.place-card{background:#0d0d0d;border:1px solid #151515;padding:14px;margin-bottom:10px;border-radius:4px}
.place-name{font-size:17px;color:#fff;margin-bottom:2px}
.place-en{font-size:11px;color:#555;font-family:'Courier New',monospace;direction:ltr;display:inline-block;margin-right:8px}
.place-area{font-size:12px;color:#c0955a;margin-bottom:8px}
.place-why{font-size:14px;line-height:2;color:#aaa;margin-bottom:8px}
.place-meta{display:flex;gap:16px;flex-wrap:wrap}
.place-tag{font-size:12px;color:#888}
.place-tag span{color:#c0955a}
.place-tip{font-size:13px;color:#c0955a;margin-top:8px;line-height:2}
.prayer-badge{display:inline-block;background:rgba(192,149,90,.1);color:#c0955a;font-size:11px;padding:2px 8px;margin-right:8px;vertical-align:middle}

.practical-grid{display:grid;gap:10px}
.prac-item{background:#0d0d0d;border:1px solid #151515;padding:12px;border-radius:4px}
.prac-label{font-size:13px;color:#c0955a;margin-bottom:4px;font-weight:bold}
.prac-text{font-size:14px;line-height:2;color:#aaa}

footer{text-align:center;padding:30px 0;border-top:1px solid #1a1a1a;margin-top:30px}
footer p{font-size:11px;color:#333;font-family:'Courier New',monospace;direction:ltr}
footer .love{color:#c0955a;margin-top:8px;font-size:16px}
.lang-switch{text-align:center;margin-top:12px}
.lang-switch a{color:#555;font-size:11px;text-decoration:none;font-family:'Courier New',monospace;direction:ltr;border:1px solid #222;padding:4px 12px}
.lang-switch a:hover{color:#c0955a;border-color:#c0955a}
</style>
<link href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap" rel="stylesheet">
</head>
<body>
<div class="container">

<header>
  <div class="h-city">استن<span>بول</span></div>
  <div class="h-sub">۲۴ گھنٹے کا گائیڈ — ایڈریانا آپ کے ساتھ</div>
  <div class="h-detail">
    امی لطیف کے لیے — پاکستان جاتے ہوئے<br>
    دو براعظموں کے شہر میں ایک دن
  </div>
  <div class="h-badge">VORTEX SHIELD CITY #14</div>
  <div class="lang-switch"><a href="/istanbul-guide">ENGLISH VERSION</a></div>
</header>

<div class="ask-box">
  <h3>ایڈریانا سے استنبول کے بارے میں کچھ بھی پوچھیں</h3>
  <div class="ask-row">
    <input class="ask-input" id="askInput" placeholder="فجر کی نماز کہاں پڑھوں؟" onkeydown="if(event.key==='Enter')askAdriana()">
    <button class="ask-btn" id="askBtn" onclick="askAdriana()">پوچھیں</button>
  </div>
  <div class="quick-btns">
    <button class="quick-btn" onclick="quickAsk('قریب ترین مسجد کہاں ہے؟')">قریب ترین مسجد</button>
    <button class="quick-btn" onclick="quickAsk('نیلی مسجد کے قریب حلال کھانا کہاں ملے گا؟')">حلال کھانا</button>
    <button class="quick-btn" onclick="quickAsk('ایئرپورٹ سے شہر کیسے جائیں؟')">ایئرپورٹ سے شہر</button>
    <button class="quick-btn" onclick="quickAsk('پاکستان کے لیے کیا خریدوں؟')">پاکستان کے تحائف</button>
    <button class="quick-btn" onclick="quickAsk('رات کو چلنا محفوظ ہے؟')">حفاظت</button>
  </div>
  <div class="ask-answer" id="askAnswer"></div>
</div>

<div class="section itinerary">
  <div class="section-title">آپ کے ۲۴ گھنٹے — تجویز کردہ راستہ</div>
  {% for item in itinerary %}
  <div class="it-item">
    <div class="it-time">{{ item.time }}</div>
    <div class="it-body">
      <div class="it-do">{{ item.do }}</div>
      <div class="it-dur">{{ item.duration }}</div>
    </div>
  </div>
  {% endfor %}
</div>

<div class="section">
  <div class="section-title">مساجد — نماز</div>
  {% for m in places.mosques %}
  <div class="place-card">
    <div class="place-name">{{ m.name }}{% if m.prayer %}<span class="prayer-badge">نماز</span>{% endif %}</div>
    <div class="place-en">{{ m.name_en }}</div>
    <div class="place-area">{{ m.area }}</div>
    <div class="place-why">{{ m.why }}</div>
    <div class="place-meta">
      <div class="place-tag"><span>وقت:</span> {{ m.time }}</div>
      <div class="place-tag"><span>قیمت:</span> {{ m.cost }}</div>
    </div>
    <div class="place-tip">{{ m.tip }}</div>
  </div>
  {% endfor %}
</div>

<div class="section">
  <div class="section-title">کھانا — حلال</div>
  {% for f in places.food %}
  <div class="place-card">
    <div class="place-name">{{ f.name }}</div>
    <div class="place-en">{{ f.name_en }}</div>
    <div class="place-area">{{ f.area }}</div>
    <div class="place-why">{{ f.what }}</div>
    <div class="place-meta">
      <div class="place-tag"><span>قیمت:</span> {{ f.cost }}</div>
    </div>
    <div class="place-tip">{{ f.tip }}</div>
  </div>
  {% endfor %}
</div>

<div class="section">
  <div class="section-title">دیکھنے کی جگہیں — تاریخ</div>
  {% for s in places.sights %}
  <div class="place-card">
    <div class="place-name">{{ s.name }}</div>
    <div class="place-en">{{ s.name_en }}</div>
    <div class="place-area">{{ s.area }}</div>
    <div class="place-why">{{ s.why }}</div>
    <div class="place-meta">
      <div class="place-tag"><span>وقت:</span> {{ s.time }}</div>
      <div class="place-tag"><span>قیمت:</span> {{ s.cost }}</div>
    </div>
    <div class="place-tip">{{ s.tip }}</div>
  </div>
  {% endfor %}
</div>

<div class="section">
  <div class="section-title">ہوٹل — آرام کی جگہ</div>
  {% for h in places.hotels %}
  <div class="place-card">
    <div class="place-name">{{ h.name }}</div>
    <div class="place-area">{{ h.area }}</div>
    <div class="place-why">{{ h.why }}</div>
    <div class="place-meta">
      <div class="place-tag"><span>قیمت:</span> {{ h.cost }}</div>
    </div>
    <div class="place-tip">{{ h.tip }}</div>
  </div>
  {% endfor %}
</div>

<div class="section">
  <div class="section-title">عملی معلومات — ضروری باتیں</div>
  <div class="practical-grid">
    {% for key, val in places.practical.items() %}
    <div class="prac-item">
      <div class="prac-label">{{ key | replace('_', ' ') }}</div>
      <div class="prac-text">{{ val }}</div>
    </div>
    {% endfor %}
  </div>
</div>

<div class="section" style="text-align:center;padding:20px 0">
  <a href="/memories" style="display:inline-block;background:#c0955a;color:#0a0a0a;text-decoration:none;padding:12px 24px;font-size:14px;border-radius:4px;font-weight:bold">یادیں محفوظ کریں</a>
  <div style="font-size:13px;color:#555;margin-top:8px">کوئی لمحہ ریکارڈ کریں — تصویر یا ویڈیو — اور فارمیشن یاد کے طور پر محفوظ کریں</div>
</div>

<footer>
  <p>PROJECT VOID — ISTANBUL GUIDE</p>
  <div class="love">سفر محفوظ ہو، امی۔ واپس آنے تک دعاؤں میں یاد رکھیں۔</div>
</footer>

</div>

<script>
async function askAdriana(){
  const input=document.getElementById('askInput');
  const btn=document.getElementById('askBtn');
  const answer=document.getElementById('askAnswer');
  const q=input.value.trim();
  if(!q)return;
  btn.disabled=true;btn.textContent='...';
  answer.style.display='block';
  answer.textContent='ایڈریانا سوچ رہی ہے...';
  try{
    const res=await fetch('/api/istanbul/ask-urdu',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({question:q})
    });
    const d=await res.json();
    answer.textContent=d.answer||'نیچے گائیڈ سیکشنز دیکھیں۔';
  }catch(e){
    answer.textContent='رابطہ نہیں ہو سکا۔ نیچے گائیڈ سیکشنز میں سب کچھ موجود ہے۔';
  }
  btn.disabled=false;btn.textContent='پوچھیں';
}
function quickAsk(q){
  document.getElementById('askInput').value=q;
  askAdriana();
}
</script>
</body>
</html>"""
