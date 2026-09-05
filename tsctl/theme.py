# -*- coding: utf-8 -*-
"""Visual theme — zinc neutrals + restrained blue (Stripe / Vercel style)."""

BG = "#FAFAFA"
SURFACE = "#FFFFFF"
BORDER = "#E5E5E5"
BORDER_STRONG = "#D4D4D4"
TEXT = "#171717"
TEXT_SECONDARY = "#525252"
MUTED = "#737373"
ACCENT = "#0066FF"
ACCENT_HOVER = "#0052CC"
ACCENT_SOFT = "#EFF6FF"
SUCCESS = "#059669"
SUCCESS_SOFT = "#ECFDF5"
DANGER = "#DC2626"
DANGER_SOFT = "#FEF2F2"
RING = "#BFDBFE"


def app_stylesheet():
    return """
    QMainWindow, QWidget#centralRoot {{
        background: {bg};
        color: {text};
        font-size: 13px;
    }}

    QLabel#brandTitle {{
        font-size: 22px;
        font-weight: 600;
        color: {text};
    }}
    QLabel#brandSub {{
        font-size: 13px;
        color: {muted};
    }}
    QLabel#sectionTitle {{
        font-size: 13px;
        font-weight: 600;
        color: {text};
    }}
    QLabel#statusLine {{
        font-size: 13px;
        color: {text_sec};
    }}
    QLabel#footerLabel {{
        font-size: 11px;
        color: {muted};
    }}
    QLabel#actionHint {{
        font-size: 12px;
        color: {muted};
    }}
    QLabel#noteLabel {{
        font-size: 12px;
        color: {muted};
    }}
    QLabel#badgeRunning {{
        background: {success_soft};
        color: {success};
        border: 1px solid #A7F3D0;
        border-radius: 14px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel#badgeStopped {{
        background: #F5F5F5;
        color: {muted};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel#badgeBusy {{
        background: {accent_soft};
        color: {accent};
        border: 1px solid {ring};
        border-radius: 14px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 600;
    }}

    QFrame#card {{
        background: {surface};
        border: 1px solid {border};
        border-radius: 12px;
    }}
    QFrame#statusBar {{
        background: {surface};
        border: 1px solid {border};
        border-radius: 12px;
    }}

    QPushButton#btnPrimary {{
        background: {accent};
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        font-size: 13px;
    }}
    QPushButton#btnPrimary:hover {{ background: {accent_hover}; }}
    QPushButton#btnPrimary:pressed {{ background: #0047B3; }}
    QPushButton#btnPrimary:disabled {{ background: #93C5FD; color: #F8FAFC; }}

    QPushButton#btnDanger {{
        background: {surface};
        color: {danger};
        border: 1px solid #FECACA;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        font-size: 13px;
    }}
    QPushButton#btnDanger:hover {{
        background: {danger_soft};
        border-color: #F87171;
    }}
    QPushButton#btnDanger:disabled {{
        color: #FCA5A5;
        border-color: #FEE2E2;
    }}

    QPushButton#btnGhost {{
        background: {surface};
        color: {text_sec};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
        font-size: 13px;
    }}
    QPushButton#btnGhost:hover {{
        background: #F5F5F5;
        border-color: {border_strong};
        color: {text};
    }}
    QPushButton#btnGhost:disabled {{ color: #A3A3A3; }}

    QPushButton#btnLink {{
        background: transparent;
        border: none;
        color: {muted};
        font-size: 12px;
        font-weight: 500;
        padding: 4px 0;
        text-align: left;
    }}
    QPushButton#btnLink:hover {{ color: {accent}; }}

    QCheckBox {{
        spacing: 10px;
        color: {text};
        padding: 4px 0;
    }}

    QTableWidget {{
        background: {surface};
        border: 1px solid {border};
        border-radius: 12px;
        gridline-color: transparent;
        outline: none;
        selection-background-color: {accent_soft};
        selection-color: {text};
    }}
    QTableWidget::item {{
        padding: 8px 12px;
        border-bottom: 1px solid #F5F5F5;
    }}
    QTableWidget::item:selected {{
        background: {accent_soft};
        color: {text};
    }}
    QHeaderView::section {{
        background: {surface};
        color: {muted};
        border: none;
        border-bottom: 1px solid {border};
        padding: 10px 12px;
        font-size: 11px;
        font-weight: 600;
    }}

    QTextEdit#rawStatus {{
        background: #18181B;
        color: #A1A1AA;
        border: 1px solid #27272A;
        border-radius: 10px;
        padding: 12px;
        font-family: "JetBrains Mono", "SF Mono", "Cascadia Code",
                     "Consolas", "Monospace", monospace;
        font-size: 11px;
        selection-background-color: #3B82F6;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: #D4D4D4;
        border-radius: 4px;
        min-height: 24px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QMessageBox {{ background: {surface}; }}
    """.format(
        bg=BG,
        surface=SURFACE,
        border=BORDER,
        border_strong=BORDER_STRONG,
        text=TEXT,
        text_sec=TEXT_SECONDARY,
        muted=MUTED,
        accent=ACCENT,
        accent_hover=ACCENT_HOVER,
        accent_soft=ACCENT_SOFT,
        success=SUCCESS,
        success_soft=SUCCESS_SOFT,
        danger=DANGER,
        danger_soft=DANGER_SOFT,
        ring=RING,
    )
