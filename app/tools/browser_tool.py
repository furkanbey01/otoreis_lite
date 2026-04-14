from __future__ import annotations

import asyncio
from typing import Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class BrowserTool:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def start(self) -> None:
        if self._page:
            return
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context()
        self._page = await self._context.new_page()

    async def stop(self) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def navigate(self, url: str, timeout_sec: int) -> dict[str, Any]:
        await self.start()
        assert self._page
        await self._page.goto(url, wait_until="domcontentloaded", timeout=timeout_sec * 1000)
        return {"url": self._page.url, "title": await self._page.title()}

    async def click(self, selector: str, timeout_sec: int) -> dict[str, Any]:
        await self.start()
        assert self._page
        await self._page.click(selector, timeout=timeout_sec * 1000)
        return {"clicked": selector}

    async def type_text(self, selector: str, text: str, timeout_sec: int) -> dict[str, Any]:
        await self.start()
        assert self._page
        await self._page.fill(selector, text, timeout=timeout_sec * 1000)
        return {"typed": selector, "length": len(text)}

    async def scroll(self, delta_y: int = 800) -> dict[str, Any]:
        await self.start()
        assert self._page
        await self._page.mouse.wheel(0, delta_y)
        await asyncio.sleep(0.2)
        return {"scroll": delta_y}

    async def extract_text(self, selector: str, timeout_sec: int) -> dict[str, Any]:
        await self.start()
        assert self._page
        el = await self._page.wait_for_selector(selector, timeout=timeout_sec * 1000)
        text = (await el.inner_text()).strip()
        return {"selector": selector, "text": text[:2000]}

    async def press(self, key: str) -> dict[str, Any]:
        await self.start()
        assert self._page
        await self._page.keyboard.press(key)
        return {"key": key}
