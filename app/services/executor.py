from __future__ import annotations

import asyncio
from typing import Any

from app.models.schemas import Action, ActionType
from app.tools.browser_tool import BrowserTool
from app.tools.filesystem_tool import FilesystemTool


class Executor:
    def __init__(self, browser: BrowserTool, fs: FilesystemTool, default_timeout_sec: int):
        self.browser = browser
        self.fs = fs
        self.default_timeout_sec = default_timeout_sec

    async def run_action(self, action: Action, context: dict[str, Any], timeout_sec: int) -> dict[str, Any]:
        t = timeout_sec
        args = action.args
        at = action.type

        if at == ActionType.navigate:
            return await self.browser.navigate(args["url"], t)
        if at == ActionType.click:
            return await self.browser.click(args["selector"], t)
        if at == ActionType.type:
            return await self.browser.type_text(args["selector"], args["text"], t)
        if at == ActionType.scroll:
            return await self.browser.scroll(int(args.get("delta_y", 800)))
        if at == ActionType.extract_text:
            result = await self.browser.extract_text(args["selector"], t)
            context["last_extract"] = result
            return result
        if at == ActionType.save_json:
            payload = args.get("payload", context.get("last_extract", context.get("last_result", {})))
            return self.fs.save_json(args["path"], payload)
        if at == ActionType.write_file:
            return self.fs.write_file(args["path"], args["content"])
        if at == ActionType.read_file:
            return self.fs.read_file(args["path"])
        if at == ActionType.delete_file:
            return self.fs.delete_file(args["path"])
        if at == ActionType.form_submit:
            if "selector" in args:
                return await self.browser.click(args["selector"], t)
            return await self.browser.press("Enter")

        raise ValueError(f"unsupported action: {at}")

    async def run_action_with_retry(
        self, action: Action, context: dict[str, Any], retries: int, timeout_sec: int
    ) -> dict[str, Any]:
        err = None
        for attempt in range(retries + 1):
            try:
                res = await asyncio.wait_for(self.run_action(action, context, timeout_sec), timeout=timeout_sec)
                context["last_result"] = res
                return res
            except Exception as exc:  # noqa: BLE001
                err = str(exc)
                if attempt >= retries:
                    break
                await asyncio.sleep(0.4)
        raise RuntimeError(err or "action failed")
