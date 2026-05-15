#!/usr/bin/env python3
"""
Playwright script to search for Google Maps API documentation
"""

import asyncio
from playwright.async_api import async_playwright


async def search_google_maps_api():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # headless=False aby zobaczyć co się dzieje
        page = await browser.new_page()

        print("🌐 Otwieram Google...")
        await page.goto("https://www.google.com")

        # Zaakceptuj cookies jeśli pojawią się
        try:
            await page.click("button:has-text('Zaakceptuj wszystko')", timeout=2000)
        except:
            pass

        # Wyszukaj Google Maps API
        print("🔍 Wyszukuję 'Google Maps API'...")
        await page.fill("input[name='q']", "Google Maps API documentation")
        await page.press("input[name='q']", "Enter")

        # Czekaj na wyniki
        await page.wait_for_load_state("networkidle")

        # Pobierz linki do wyników
        print("\n📋 Wyniki wyszukiwania:\n")

        links = await page.query_selector_all("a[href*='google'] h3")

        for i, link in enumerate(links[:10], 1):  # Pierwszych 10 wyników
            text = await link.text_content()
            parent_link = await link.locator("xpath=ancestor::a").first.get_attribute("href")
            print(f"{i}. {text}")
            print(f"   URL: {parent_link}\n")

        print("\n✅ Búiterfacerem otwartą w przeglądarce. Zamknij ją aby zakończyć.")

        # Czekaj aż użytkownik zamknie przeglądarkę
        await browser.wait_for_event("close")


if __name__ == "__main__":
    asyncio.run(search_google_maps_api())
