"""权限确认弹窗的交互测试。

真实事故：用户在「是否允许写文件」的弹窗上点了 Yes，但组件只支持键盘，
点击没有反应，随后按 Esc 关掉弹窗 → 被判成 DENY，工具返回
「The user rejected this tool use」，用户看到的是「我明明同意了却没写上」。
这里把三种操作方式（键盘选择 / 数字键 / 鼠标点击）都钉住。
"""

from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from pandacode.agent import PermissionResponse
from pandacode.permission_dialog import InlinePermissionWidget


class _Harness(App):
    def __init__(self) -> None:
        super().__init__()
        self.responses: list[PermissionResponse] = []

    def compose(self) -> ComposeResult:
        yield InlinePermissionWidget("WriteFile", r"C:\Users\me\.pandacode\memory\MEMORY.md")

    def on_inline_permission_widget_responded(
        self, event: InlinePermissionWidget.Responded
    ) -> None:
        self.responses.append(event.response)


async def _run(keys: tuple[str, ...] = (), click: str | None = None) -> list[PermissionResponse]:
    app = _Harness()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        if click:
            await pilot.click(click)
        for key in keys:
            await pilot.press(key)
        await pilot.pause()
    return app.responses


@pytest.mark.asyncio
async def test_enter_picks_default_yes():
    assert await _run(keys=("enter",)) == [PermissionResponse.ALLOW]


@pytest.mark.asyncio
async def test_click_on_yes_option_allows():
    """鼠标点第一项（Yes）必须等同于确认。"""
    assert await _run(click="#perm-opt-0") == [PermissionResponse.ALLOW]


@pytest.mark.asyncio
async def test_click_on_no_option_denies():
    assert await _run(click="#perm-opt-2") == [PermissionResponse.DENY]


@pytest.mark.asyncio
async def test_digit_keys_pick_option():
    # 2 = "don't ask again"，3 = No
    assert await _run(keys=("2",)) == [PermissionResponse.ALLOW_ALWAYS]
    assert await _run(keys=("3",)) == [PermissionResponse.DENY]


@pytest.mark.asyncio
async def test_y_and_n_shortcuts():
    assert await _run(keys=("y",)) == [PermissionResponse.ALLOW]
    assert await _run(keys=("n",)) == [PermissionResponse.DENY]


@pytest.mark.asyncio
async def test_escape_denies():
    assert await _run(keys=("escape",)) == [PermissionResponse.DENY]


@pytest.mark.asyncio
async def test_arrow_down_then_enter_picks_second_option():
    assert await _run(keys=("down", "enter")) == [PermissionResponse.ALLOW_ALWAYS]
