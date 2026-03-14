import os
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import app, MAJORS, FEATURE_PAGES, JOURNAL_PAGES, get_conn

OUT_DIR = BASE_DIR / "static_site"
STATIC_DIR = BASE_DIR / "static"


def get_approved_teacher_ids():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id FROM teachers WHERE status = 'approved' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [row["id"] for row in rows]


def build_paths():
    paths = [
        "/",
        "/demo",
        "/metrics",
        "/rules",
        "/register",
        "/login",
        "/register-teacher",
        "/ask-subject",
    ]

    for item in FEATURE_PAGES.keys():
        paths.append(f"/feature/{item}")

    for item in JOURNAL_PAGES.keys():
        paths.append(f"/journals/{item}")

    for major in MAJORS:
        paths.append(f"/ask-teacher/{major['slug']}")

    for teacher_id in get_approved_teacher_ids():
        paths.append(f"/teacher-profile/{teacher_id}")

    return paths


def write_file(path: Path, content: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def copy_static_assets():
    if STATIC_DIR.exists():
        target = OUT_DIR / "static"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(STATIC_DIR, target)


def export_pages():
    client = app.test_client()
    paths = build_paths()

    for route in paths:
        resp = client.get(route)
        if resp.status_code != 200:
            print(f"Skip {route} (status {resp.status_code})")
            continue
        output_path = OUT_DIR / route.lstrip("/")
        if route.endswith("/") or route == "/":
            output_path = output_path / "index.html"
        else:
            output_path = output_path.with_suffix(".html")
        write_file(output_path, resp.data)
        print(f"Exported {route} -> {output_path.relative_to(OUT_DIR)}")

    return paths


def write_robots_and_sitemap(paths):
    base_url = "https://your-domain.example"
    sitemap_entries = []
    for route in paths:
        if route == "/":
            url = f"{base_url}/"
        else:
            url = f"{base_url}{route}"
        if not url.endswith(".html") and not url.endswith("/"):
            url = f"{url}.html"
        sitemap_entries.append(
            f"  <url><loc>{url}</loc></url>"
        )

    sitemap = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + \
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n" + \
        "\n".join(sitemap_entries) + "\n</urlset>\n"

    robots = "User-agent: *\nAllow: /\nSitemap: " + base_url + "/sitemap.xml\n"

    write_file(OUT_DIR / "sitemap.xml", sitemap.encode("utf-8"))
    write_file(OUT_DIR / "robots.txt", robots.encode("utf-8"))


if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)
    copy_static_assets()
    paths = export_pages()
    write_robots_and_sitemap(paths)
    print("Static export complete. Update sitemap base_url before publishing.")
