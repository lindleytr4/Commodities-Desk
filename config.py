# config.py — Design tokens for the Commodity Desk dashboard

def hex_to_rgba(hex_color, alpha=0.1):
    """Convert a 6-digit hex color to an rgba() string Plotly accepts."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

COLORS = {
    "bg":       "#0A0C0F",
    "surface":  "#111418",
    "border":   "#1E2328",
    "grid":     "#141820",
    "text":     "#D4D8DE",
    "muted":    "#5A6070",
    "accent":   "#00B4D8",   # cyan — primary highlight
    "accent2":  "#E85D04",   # orange — secondary
    "accent3":  "#48CAE4",   # light cyan — tertiary
    "up":       "#2DC653",   # green
    "down":     "#E63946",   # red
    "gold":     "#FFD166",
    "silver":   "#B0B8C1",
    "copper":   "#CD7F32",
}

FONT = {
    "mono": "Share Tech Mono, monospace",
    "head": "Barlow Condensed, sans-serif",
    "body": "Barlow, sans-serif",
}
