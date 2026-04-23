#!/usr/bin/env python3
"""OneNote to Obsidian Markdown Exporter

Exports Microsoft OneNote notebooks to Obsidian-compatible markdown files
with proper folder hierarchy, images, and YAML frontmatter.
"""

import os
import sys
import json
import re
import time
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

# ─── Auto-install dependencies ──────────────────────────────────────────────
def ensure_deps():
    deps = {
        "requests": "requests",
        "msal": "msal",
        "markdownify": "markdownify",
        "bs4": "beautifulsoup4",
    }
    missing = []
    for module, package in deps.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    if missing:
        print(f"📦 Installing dependencies: {', '.join(missing)}")
        os.system(f"{sys.executable} -m pip install {' '.join(missing)} -q")

ensure_deps()

import requests
import msal
from markdownify import markdownify as md_convert
from bs4 import BeautifulSoup

# ─── Configuration ──────────────────────────────────────────────────────────
CLIENT_ID = "cl1entID$tr1n6n0t3ncryp7ed"  # Microsoft Graph PowerShell
AUTHORITY = "https://login.microsoftonline.com/organizations"
SCOPES = ["Notes.Read", "Notes.Read.All", "User.Read"]
GRAPH_BASE = "https://graph.microsoft.com/v1.0"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_CACHE_FILE = os.path.join(SCRIPT_DIR, ".token_cache.json")

DEFAULT_OUTPUT = "/Users/[username]/OneDrive - Microsoft/[username]-dev_space/onenote-2-obsidian/onenote-export"

# ─── Authentication ─────────────────────────────────────────────────────────

def get_token(token_file=None):
    """Get access token from file or Graph Explorer browser flow."""
    # Option 1: Token provided via file
    if token_file and os.path.exists(token_file):
        with open(token_file, "r") as f:
            token = f.read().strip()
        if token:
            print("✅ Using token from file")
            sys.stdout.flush()
            return token

    # Option 2: Token cached from previous Graph Explorer session
    ge_token_file = os.path.join(SCRIPT_DIR, ".ge_token")
    if os.path.exists(ge_token_file):
        with open(ge_token_file, "r") as f:
            token = f.read().strip()
        if token:
            # Verify token is still valid with a quick API call
            try:
                headers = {"Authorization": f"Bearer {token}"}
                resp = requests.get(f"{GRAPH_BASE}/me", headers=headers, timeout=10)
                if resp.status_code == 200:
                    print("✅ Using cached Graph Explorer token")
                    sys.stdout.flush()
                    return token
                else:
                    print("⚠️ Cached token expired, need re-auth via Graph Explorer")
            except Exception:
                pass

    print("TOKEN_NEEDED")
    print("No valid token found. Please provide a token via --token-file.")
    print("Use the skill's Graph Explorer flow to obtain one.")
    sys.stdout.flush()
    sys.exit(1)


def save_token(token):
    """Cache token from Graph Explorer for reuse."""
    ge_token_file = os.path.join(SCRIPT_DIR, ".ge_token")
    with open(ge_token_file, "w") as f:
        f.write(token)
    os.chmod(ge_token_file, 0o600)


# ─── Graph API Helpers ──────────────────────────────────────────────────────

def graph_get(token, url, params=None, raw=False):
    """Make authenticated GET request to Graph API."""
    headers = {"Authorization": f"Bearer {token}"}
    if not raw:
        headers["Accept"] = "application/json"

    resp = requests.get(url, headers=headers, params=params, timeout=60)

    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 10))
        print(f"  ⏳ Rate limited, waiting {retry_after}s...")
        sys.stdout.flush()
        time.sleep(retry_after)
        return graph_get(token, url, params, raw)

    if resp.status_code == 401:
        raise Exception("TOKEN_EXPIRED")

    resp.raise_for_status()
    return resp.text if raw else resp.json()


def graph_get_all(token, url, params=None):
    """Get all pages of results from Graph API."""
    results = []
    while url:
        data = graph_get(token, url, params)
        results.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
        params = None
    return results


# ─── Content Processing ─────────────────────────────────────────────────────

def sanitize_filename(name):
    """Sanitize a string for use as a filename (Obsidian-safe)."""
    name = re.sub(r'[<>:"/\\|?*#\[\]]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    name = name.rstrip('.')
    return name or "Untitled"


def download_image(token, img_url, assets_dir, page_id):
    """Download an image and return the local filename."""
    os.makedirs(assets_dir, exist_ok=True)

    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(img_url, headers=headers, stream=True, timeout=30)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "image/png")
        ext_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/gif": ".gif",
            "image/bmp": ".bmp",
            "image/svg+xml": ".svg",
            "image/webp": ".webp",
        }
        ext = ext_map.get(content_type.split(";")[0].strip(), ".png")

        img_hash = hashlib.md5(img_url.encode()).hexdigest()[:10]
        filename = f"{page_id[:8]}_{img_hash}{ext}"
        filepath = os.path.join(assets_dir, filename)

        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)

        return filename
    except Exception as e:
        print(f"    ⚠️ Image download failed: {e}")
        return None


def html_to_markdown(token, html_content, assets_dir, page_id):
    """Convert OneNote HTML to Obsidian-compatible markdown."""
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    # Download and relink images
    for img in soup.find_all("img"):
        src = img.get("data-fullres-src") or img.get("src", "")
        if src and ("graph.microsoft.com" in src or src.startswith("http")):
            local_name = download_image(token, src, assets_dir, page_id)
            if local_name:
                img["src"] = f"assets/{local_name}"
                if not img.get("alt"):
                    img["alt"] = "image"

    # Remove OneNote chrome elements
    for tag in soup.find_all(["meta", "link", "style", "script"]):
        tag.decompose()

    # Handle OneNote checkboxes (data-tag="to-do")
    for tag in soup.find_all(attrs={"data-tag": True}):
        data_tag = tag.get("data-tag", "")
        if "to-do" in data_tag:
            prefix = "- [x] " if "completed" in data_tag else "- [ ] "
            tag.string = prefix + (tag.get_text() or "")

    # Convert to markdown
    markdown = md_convert(
        str(soup),
        heading_style="atx",
        bullets="-",
        strip=["script"],
    )

    # Clean up excessive whitespace
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    markdown = markdown.strip()

    return markdown


def generate_frontmatter(page, notebook_name, section_name):
    """Generate YAML frontmatter for Obsidian."""
    title = page.get("title", "Untitled")
    created = page.get("createdDateTime", "")
    modified = page.get("lastModifiedDateTime", "")
    onenote_link = page.get("links", {}).get("oneNoteWebUrl", {}).get("href", "")

    def fmt_date(dt_str):
        if dt_str:
            try:
                return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
        return dt_str

    lines = [
        "---",
        f'title: "{title}"',
        f'notebook: "{notebook_name}"',
        f'section: "{section_name}"',
        f'created: "{fmt_date(created)}"',
        f'modified: "{fmt_date(modified)}"',
        f'source: onenote',
    ]
    if onenote_link:
        lines.append(f'onenote_url: "{onenote_link}"')
    lines.append("---")
    lines.append("")

    return "\n".join(lines) + "\n"


# ─── OneNote Structure Traversal ────────────────────────────────────────────

def list_notebooks(token):
    """List all notebooks sorted by name."""
    notebooks = graph_get_all(token, f"{GRAPH_BASE}/me/onenote/notebooks")
    return sorted(notebooks, key=lambda n: n.get("displayName", "").lower())


def get_sections(token, notebook_id):
    """Get all sections in a notebook, including nested section groups."""
    sections = []

    # Direct sections
    direct = graph_get_all(
        token, f"{GRAPH_BASE}/me/onenote/notebooks/{notebook_id}/sections"
    )
    for s in direct:
        s["_group_path"] = ""
    sections.extend(direct)

    # Section groups (recursive)
    groups = graph_get_all(
        token, f"{GRAPH_BASE}/me/onenote/notebooks/{notebook_id}/sectionGroups"
    )
    for group in groups:
        sections.extend(
            _get_section_group_sections(token, group, group.get("displayName", ""))
        )

    return sections


def _get_section_group_sections(token, group, path_prefix):
    """Recursively get sections from section groups."""
    sections = []
    group_id = group["id"]

    group_sections = graph_get_all(
        token, f"{GRAPH_BASE}/me/onenote/sectionGroups/{group_id}/sections"
    )
    for s in group_sections:
        s["_group_path"] = path_prefix
    sections.extend(group_sections)

    # Nested section groups
    sub_groups = graph_get_all(
        token, f"{GRAPH_BASE}/me/onenote/sectionGroups/{group_id}/sectionGroups"
    )
    for sg in sub_groups:
        nested_path = f"{path_prefix}/{sg.get('displayName', '')}"
        sections.extend(_get_section_group_sections(token, sg, nested_path))

    return sections


def get_pages(token, section_id):
    """Get all pages in a section ordered by position."""
    return graph_get_all(
        token,
        f"{GRAPH_BASE}/me/onenote/sections/{section_id}/pages",
        params={
            "$orderby": "order",
            "$select": "id,title,createdDateTime,lastModifiedDateTime,level,order,links,parentSection",
        },
    )


def build_page_tree(pages):
    """Build hierarchical tree from flat page list using indent levels."""
    tree = []
    stack = [{"children": tree, "level": -1}]

    for page in pages:
        level = page.get("level", 0) or 0
        node = {"page": page, "children": [], "level": level}

        while len(stack) > 1 and stack[-1]["level"] >= level:
            stack.pop()

        stack[-1]["children"].append(node)
        stack.append(node)

    return tree


# ─── Export Logic ────────────────────────────────────────────────────────────

def export_page(token, page, output_path, assets_dir, notebook_name, section_name):
    """Export a single page to markdown file."""
    page_id = page["id"]
    title = page.get("title", "Untitled")

    print(f"    📄 {title}")
    sys.stdout.flush()

    try:
        html_content = graph_get(
            token, f"{GRAPH_BASE}/me/onenote/pages/{page_id}/content", raw=True
        )
    except Exception as e:
        print(f"      ⚠️ Content fetch failed: {e}")
        html_content = ""

    markdown = html_to_markdown(token, html_content, assets_dir, page_id)
    frontmatter = generate_frontmatter(page, notebook_name, section_name)

    full_content = frontmatter + f"# {title}\n\n" + markdown

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_content)


def export_page_tree(token, tree, section_dir, assets_dir, notebook_name, section_name, prefix=""):
    """Recursively export page tree to folder structure."""
    for idx, node in enumerate(tree):
        page = node["page"]
        children = node["children"]
        title = sanitize_filename(page.get("title", "Untitled"))
        order_prefix = f"{prefix}{idx + 1:02d}"

        if children:
            # Page has subpages → create folder
            page_dir = os.path.join(section_dir, f"{order_prefix}-{title}")
            os.makedirs(page_dir, exist_ok=True)

            # Parent page → same-named .md inside the folder
            parent_path = os.path.join(page_dir, f"{title}.md")
            export_page(token, page, parent_path, assets_dir, notebook_name, section_name)

            # Recurse children
            export_page_tree(
                token, children, page_dir, assets_dir,
                notebook_name, section_name, prefix=f"{order_prefix}."
            )
        else:
            # Leaf page → flat .md file
            page_path = os.path.join(section_dir, f"{order_prefix}-{title}.md")
            export_page(token, page, page_path, assets_dir, notebook_name, section_name)


def export_notebook(token, notebook, output_base):
    """Export a complete notebook with all sections and pages."""
    nb_name = sanitize_filename(notebook.get("displayName", "Untitled"))
    nb_dir = os.path.join(output_base, nb_name)
    os.makedirs(nb_dir, exist_ok=True)

    print(f"\n📓 Exporting: {nb_name}")
    sys.stdout.flush()

    sections = get_sections(token, notebook["id"])
    total_pages = 0

    for section in sections:
        sec_name = sanitize_filename(section.get("displayName", "Untitled"))
        group_path = section.get("_group_path", "")

        if group_path:
            sec_dir = os.path.join(
                nb_dir,
                *[sanitize_filename(p) for p in group_path.split("/") if p],
                sec_name,
            )
        else:
            sec_dir = os.path.join(nb_dir, sec_name)

        assets_dir = os.path.join(sec_dir, "assets")
        os.makedirs(sec_dir, exist_ok=True)

        label = f"{group_path}/{sec_name}" if group_path else sec_name
        print(f"  📂 {label}")
        sys.stdout.flush()

        pages = get_pages(token, section["id"])
        if not pages:
            print(f"    (empty)")
            continue

        total_pages += len(pages)
        page_tree = build_page_tree(pages)
        export_page_tree(token, page_tree, sec_dir, assets_dir, nb_name, sec_name)

    return nb_dir, total_pages


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Export OneNote to Obsidian markdown")
    parser.add_argument("--output", "-o", default=None, help="Output directory")
    parser.add_argument("--list", "-l", action="store_true", help="List notebooks only (JSON)")
    parser.add_argument("--notebooks", "-n", type=str, help="Comma-separated notebook indices (1-based)")
    parser.add_argument("--all", "-a", action="store_true", help="Export all notebooks")
    parser.add_argument("--token-file", "-t", type=str, help="File containing Graph API access token")
    args = parser.parse_args()

    output_base = args.output or os.environ.get("ONENOTE_EXPORT_DIR", DEFAULT_OUTPUT)

    print("🔐 Authenticating...")
    sys.stdout.flush()
    token = get_token(token_file=args.token_file)
    save_token(token)
    print("✅ Authenticated\n")
    sys.stdout.flush()

    print("📚 Fetching notebooks...")
    sys.stdout.flush()
    notebooks = list_notebooks(token)

    if not notebooks:
        print("❌ No notebooks found.")
        return

    # ── List mode: output JSON for the skill to parse ──
    if args.list:
        nb_list = []
        for i, nb in enumerate(notebooks, 1):
            nb_list.append({
                "index": i,
                "name": nb["displayName"],
                "id": nb["id"],
                "created": nb.get("createdDateTime", "")[:10],
                "modified": nb.get("lastModifiedDateTime", "")[:10],
            })
        print("NOTEBOOKS_JSON_START")
        print(json.dumps(nb_list, indent=2))
        print("NOTEBOOKS_JSON_END")
        return

    # ── Select notebooks ──
    if args.all:
        selected = notebooks
    elif args.notebooks:
        indices = [int(x.strip()) for x in args.notebooks.split(",")]
        selected = [notebooks[i - 1] for i in indices if 0 < i <= len(notebooks)]
    else:
        print("❌ No selection mode specified. Use --all, --notebooks, or --list.")
        return

    if not selected:
        print("❌ No valid notebooks selected.")
        return

    # ── Export ──
    print(f"\n🚀 Exporting {len(selected)} notebook(s) to:\n   {output_base}\n")
    sys.stdout.flush()
    os.makedirs(output_base, exist_ok=True)

    results = []
    for nb in selected:
        try:
            nb_dir, page_count = export_notebook(token, nb, output_base)
            md_count = sum(1 for _ in Path(nb_dir).rglob("*.md"))
            img_count = sum(1 for _ in Path(nb_dir).rglob("assets/*"))
            results.append({
                "name": nb["displayName"],
                "path": nb_dir,
                "pages": page_count,
                "md_files": md_count,
                "images": img_count,
            })
        except Exception as e:
            print(f"\n❌ Error exporting {nb['displayName']}: {e}")
            results.append({"name": nb["displayName"], "error": str(e)})

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"EXPORT_COMPLETE")
    print(f"{'='*60}")
    print(f"📁 Output: {output_base}")
    for r in results:
        if "error" in r:
            print(f"  ❌ {r['name']}: {r['error']}")
        else:
            print(f"  📓 {r['name']}: {r['md_files']} pages, {r['images']} images")
    print(f"{'='*60}")

    print("RESULTS_JSON_START")
    print(json.dumps({"output_dir": output_base, "notebooks": results}, indent=2))
    print("RESULTS_JSON_END")


if __name__ == "__main__":
    main()
