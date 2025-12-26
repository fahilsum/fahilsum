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
def generate_svg(languages):
    max_width = 200
    bar_height = 12
    spacing = 22

    height = 40 + spacing * len(languages)

    svg = [
        f'<svg width="420" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        '<style>',
        'text { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif; font-size: 12px; fill: #333; }',
        '</style>',
        '<text x="10" y="20" font-weight="bold">Most Used Languages</text>'
    ]

    y = 40
    for lang in languages:
        width = (lang["percent"] / 100) * max_width
        svg.append(f'<rect x="10" y="{y}" width="{width}" height="{bar_height}" rx="4" fill="#4c71f2" />')
        svg.append(f'<text x="{max_width + 20}" y="{y + 10}">{lang["name"]} {lang["percent"]}%</text>')
        y += spacing

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
