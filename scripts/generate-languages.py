import os
import requests

# =========================
# CONFIG
# =========================
GITHUB_API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN")

if not TOKEN:
    raise RuntimeError("GITHUB_TOKEN environment variable is not set")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

OUTPUT_DIR = "stats"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "languages.svg")
TOP_N = 5


# =========================
# FETCH ALL REPOS (PUBLIC + PRIVATE)
# =========================
def fetch_all_repos():
    repos = []
    page = 1

    while True:
        url = f"{GITHUB_API}/user/repos?per_page=100&page={page}"
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()

        data = res.json()
        if not data:
            break

        repos.extend(data)
        page += 1

    return repos


# =========================
# FILTER REPO (EXCLUDE)
# =========================
def is_valid_repo(repo):
    if repo.get("fork"):
        return False
    if repo.get("archived"):
        return False
    return True


# =========================
# AGGREGATE LANGUAGE BYTES
# =========================
def aggregate_languages(repos):
    totals = {}

    for repo in repos:
        if not is_valid_repo(repo):
            continue

        lang_url = repo.get("languages_url")
        if not lang_url:
            continue

        res = requests.get(lang_url, headers=HEADERS)
        res.raise_for_status()
        languages = res.json()

        for lang, size in languages.items():
            totals[lang] = totals.get(lang, 0) + size

    return totals


# =========================
# NORMALIZE & SORT
# =========================
def calculate_percentages(language_bytes):
    total = sum(language_bytes.values())
    if total == 0:
        return []

    result = []
    for lang, size in language_bytes.items():
        percent = (size / total) * 100
        result.append({
            "name": lang,
            "percent": round(percent, 1)
        })

    result.sort(key=lambda x: x["percent"], reverse=True)
    return result[:TOP_N]


# =========================
# GENERATE SVG
# =========================
LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Go": "#00ADD8",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "Shell": "#89e051",
    "Rust": "#000000",
    "PHP": "#777BB4",
    "Ruby": "#701516",
    "Swift": "#fa7343",
    "Kotlin": "#A97BFF",
    "Dart": "#00B4AB",
    "R": "#198CE7",
    "Scala": "#c22d40",
    "Lua": "#000080",
    "Perl": "#0298c3",
    "Haskell": "#5e5086",
    "Elixir": "#6e4a7e",
    "Clojure": "#db5855",
    "Julia": "#a270ba",
    "MATLAB": "#e16737",
    "Objective-C": "#438eff",
    "Vim Script": "#199f4b",
    "PowerShell": "#012456",
    "TeX": "#3D6117",
    "Vue": "#4FC08D",
    "Svelte": "#ff3e00",
    "Assembly": "#6E4C13",
    "Makefile": "#427819",
    "Dockerfile": "#2496ED",
    "YAML": "#cb171e",
    "JSON": "#292929",
    "XML": "#0060ac",
    "Markdown": "#083fa1",
    "Other": "#586069",
}

def generate_svg(languages):
    # Dimensions closely matching GitHub Readme Stats compact layout
    width = 400
    bar_height = 8
    row_height = 18  # Tighter spacing for compact feel
    padding = 15
    bar_max_width = 180  # Shorter bars for compact layout
    title_height = 25

    height = padding * 2 + title_height + row_height * len(languages)

    svg = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        '<defs>',
        # Subtle gradient for background (react theme inspired, very close to example)
        '<linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">',
        '<stop offset="0%" style="stop-color:#0d1117;stop-opacity:1" />',
        '<stop offset="100%" style="stop-color:#161b22;stop-opacity:1" />',
        '</linearGradient>',
        '</defs>',
        '<style>',
        'text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 11px; fill: #c9d1d9; }',
        '.title { font-weight: 600; font-size: 14px; fill: #f0f6fc; }',
        '.bg { fill: url(#bgGradient); stroke: #30363d; stroke-width: 1; rx: 6; }',
        '.bar { rx: 3; }',  # No shadow for cleaner look like the example
        '.label { fill: #f0f6fc; font-weight: 500; }',
        '.percent { fill: #8b949e; }',
        '</style>',

        # Background card (no shadow for exact match)
        f'<rect x="0" y="0" width="{width}" height="{height}" class="bg" />',

        # Title exactly as in example
        f'<text x="{padding}" y="{padding + 12}" class="title">Most Used Languages</text>',
    ]

    y = padding + title_height

    for lang in languages:
        percent = lang["percent"]
        bar_width = (percent / 100) * bar_max_width
        color = LANG_COLORS.get(lang["name"], "#8b949e")

        # Bar (clean, no shadow)
        svg.append(
            f'<rect x="{padding}" y="{y}" width="{bar_width}" height="{bar_height}" class="bar" fill="{color}" />'
        )
        # Language name (positioned right of bar, like example)
        svg.append(
            f'<text x="{padding + bar_max_width + 8}" y="{y + 7}" class="label">{lang["name"]}</text>'
        )
        # Percentage (right-aligned at end, like example)
        svg.append(
            f'<text x="{width - padding}" y="{y + 7}" text-anchor="end" class="percent">{percent}%</text>'
        )

        y += row_height

    svg.append("</svg>")
    return "\n".join(svg)

# =========================
# MAIN
# =========================
def main():
    repos = fetch_all_repos()
    language_bytes = aggregate_languages(repos)
    top_languages = calculate_percentages(language_bytes)

    if not top_languages:
        print("No language data found.")
        return

    svg_content = generate_svg(top_languages)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print("languages.svg generated successfully")


if __name__ == "__main__":
    main()
