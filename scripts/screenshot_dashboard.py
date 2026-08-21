"""Capture dashboard reports screenshot for local visual QA."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from playwright.sync_api import sync_playwright

User = get_user_model()


def make_session_cookie(username: str = "admin") -> str:
    user = User.objects.filter(username=username).first()
    if user is None:
        user = User.objects.filter(is_superuser=True).first()
    if user is None:
        raise SystemExit("No admin/superuser found. Create one first.")

    store = SessionStore()
    store["_auth_user_id"] = str(user.pk)
    store["_auth_user_backend"] = "django.contrib.auth.backends.ModelBackend"
    store["_auth_user_hash"] = user.get_session_auth_hash()
    store.create()
    return store.session_key


def main():
    out_dir = ROOT / "media"
    out_dir.mkdir(parents=True, exist_ok=True)
    page_path = out_dir / "tmp_dashboard_reports.png"
    brand_path = out_dir / "tmp_sidebar_brand.png"
    session_key = make_session_cookie()
    cookie_name = settings.SESSION_COOKIE_NAME

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1360, "height": 900})
        context.add_cookies(
            [
                {
                    "name": cookie_name,
                    "value": session_key,
                    "domain": "127.0.0.1",
                    "path": "/",
                    "httpOnly": True,
                    "sameSite": "Lax",
                }
            ]
        )
        page = context.new_page()
        page.goto("http://127.0.0.1:8001/dashboard/reports/", wait_until="networkidle")
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(400)
        if "/login/" in page.url:
            raise SystemExit(f"Still on login page: {page.url}")
        page.screenshot(path=str(page_path), full_page=False)
        page.locator(".sidebar-brand").screenshot(path=str(brand_path))
        print("URL", page.url)
        print("PAGE", page_path)
        print("BRAND", brand_path)
        browser.close()


if __name__ == "__main__":
    main()
