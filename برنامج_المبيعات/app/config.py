# -*- coding: utf-8 -*-
"""
الإعدادات العامة، الألوان، ومساعدات اللغة العربية (RTL).
برنامج «تجارتي» — نظام إدارة المبيعات والمخزون المتكامل.
"""
import os

APP_NAME = "تجارتي"
APP_SUBTITLE = "نظام إدارة المبيعات والمخزون"
APP_VERSION = "1.0.0"

# مسارات أساسية
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DB_PATH = os.path.join(DATA_DIR, "tijarati.db")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# لوحة الألوان (واجهة داكنة عصرية)
COLORS = {
    "bg_deep":     "#0D0F14",
    "bg_panel":    "#13161E",
    "bg_card":     "#1A1E2A",
    "bg_hover":    "#21263A",
    "accent":      "#4F8EF7",
    "accent_h":    "#3A7AE0",
    "accent2":     "#7C5CFC",
    "accent2_h":   "#6A4EE0",
    "accent_dim":  "#2A3A5C",
    "green":       "#2ECC71",
    "green_h":     "#27AE60",
    "amber":       "#F59E0B",
    "red":         "#EF4444",
    "red_h":       "#DC2626",
    "text_1":      "#F0F2FF",
    "text_2":      "#8B92A8",
    "text_3":      "#4A5168",
    "border":      "#252A3A",
    "border2":     "#2F3650",
}

# الخطوط — Tahoma/Segoe UI تدعم العربية بشكل ممتاز على ويندوز
FONT = "Segoe UI"
FONT_AR = "Tahoma"   # أفضل خط لعرض العربية المتصلة في Tk

# ----------------------------------------------------------------------
# مساعد عرض النص العربي (RTL)
# ----------------------------------------------------------------------
# ملاحظة مهمة:
#   نسخة Tcl/Tk المرفقة مع بايثون على ويندوز (8.6.15) تعالج العربية تلقائياً
#   (تشكيل الحروف واتجاهها RTL). لذلك لا نحتاج arabic_reshaper + bidi، بل إن
#   استخدامها يسبب "معالجة مزدوجة" تعكس الحروف. لذا نتركها معطّلة افتراضياً.
#
#   إذا شغّلت البرنامج على نظام لا يعالج العربية تلقائياً (بعض توزيعات لينكس
#   أو إصدارات Tk قديمة) وظهرت الحروف متقطّعة، غيّر USE_ARABIC_RESHAPER إلى True.
USE_ARABIC_RESHAPER = False

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _RESHAPE_OK = True
    _reshaper = arabic_reshaper.ArabicReshaper(
        configuration={"delete_harakat": False, "support_ligatures": True}
    )
except Exception:  # pragma: no cover - المكتبات غير منصبة
    _RESHAPE_OK = False
    _reshaper = None


def ar(text) -> str:
    """يُرجع النص جاهزاً للعرض في Tkinter.

    افتراضياً يمرّر النص كما هو (لأن Tk على ويندوز يعالج العربية تلقائياً).
    عند تفعيل USE_ARABIC_RESHAPER يطبّق reshape + bidi للأنظمة التي تحتاجها.
    """
    if text is None:
        return ""
    text = str(text)
    if not USE_ARABIC_RESHAPER or not _RESHAPE_OK or not text:
        return text
    if not any("؀" <= ch <= "ۿ" for ch in text):
        return text
    try:
        return get_display(_reshaper.reshape(text))
    except Exception:
        return text


def money(value, currency="") -> str:
    """تنسيق المبالغ المالية بفواصل الآلاف."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        v = 0.0
    if v == int(v):
        s = f"{int(v):,}"
    else:
        s = f"{v:,.2f}"
    return f"{s} {currency}".strip()
