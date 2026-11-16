"""TUI 渲染回归测试。

背景：RichText / Rich markup 里的样式串会被 **Textual 自己的 parser 再解析一遍**。
Rich 认的写法（比如 256 色的 ``color(99)``、ANSI 名 ``ansicyan``）Textual 不认，
会抛 ``MissingStyle``；而且异常发生在 compositor 的排版阶段，普通单测、
``--help`` 甚至启动画面都碰不到，只有真正渲染消息行时才会炸。
"""

from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path

import pytest
from rich.text import Text as RichText
from textual.containers import Vertical
from textual.style import Style as TextualStyle
from textual.widgets import Static

from pandacode.app import STYLE_AI_MARKER, STYLE_PROMPT, PandaCodeApp
from pandacode.config import ProviderConfig

PACKAGE_DIR = Path(__file__).resolve().parent.parent / "pandacode"


def _provider() -> ProviderConfig:
    # 只用于构造 client，base_url 指向不可达地址，测试里不会真的发请求。
    return ProviderConfig(
        name="test",
        protocol="openai-compat",
        base_url="http://127.0.0.1:9/v1",
        model="test-model",
        api_key="sk-test",
    )


def _code_only(source: str) -> str:
    """去掉注释，避免注释里提到 color(N) 就被误判。"""
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        return "\n".join(tok.string for tok in tokens if tok.type != tokenize.COMMENT)
    except (tokenize.TokenError, IndentationError):
        return source


def test_no_rich_only_color_syntax():
    """color(N) 是 Rich 独有的 256 色写法，Textual 解析不了，排版时会崩。"""
    offenders: list[str] = []
    for path in PACKAGE_DIR.rglob("*.py"):
        source = _code_only(path.read_text(encoding="utf-8"))
        for lineno, line in enumerate(source.splitlines(), 1):
            if re.search(r"color\(\d", line):
                offenders.append(f"{path.relative_to(PACKAGE_DIR)}:{lineno}: {line.strip()}")
    assert not offenders, "发现 Textual 不支持的 color(N) 写法：\n" + "\n".join(offenders)


@pytest.mark.parametrize("style", [STYLE_PROMPT, STYLE_AI_MARKER])
def test_style_constants_are_textual_parseable(style: str):
    TextualStyle.parse(style)


@pytest.mark.asyncio
async def test_message_rows_render_without_style_error():
    """按 app 里真实的构造方式挂一条用户消息 + 一条 AI 消息，再整屏绘制一次。"""
    app = PandaCodeApp(providers=[_provider()], mcp_servers=[])
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause()
        chat = app.query_one("#chat-area")

        user = Vertical(classes="user-row")
        await chat.mount(user)
        text = RichText()
        text.append("❯ ", style=STYLE_PROMPT)
        text.append("帮我看看这个函数", style="bold")
        await user.mount(Static(text, classes="message user-message"))

        ai = Vertical(classes="ai-row")
        await chat.mount(ai)
        await ai.mount(Static(RichText("●  ", style=STYLE_AI_MARKER), classes="message"))

        await pilot.pause()
        # export_screenshot 会跑完整个 compositor，样式不合法就在这里暴露
        assert app.export_screenshot()
