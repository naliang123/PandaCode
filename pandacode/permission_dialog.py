from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Static

from pandacode.agent import PermissionResponse


_PERM_OPTIONS = [
    ("Yes", PermissionResponse.ALLOW),
    ("Yes, and don't ask again for this pattern", PermissionResponse.ALLOW_ALWAYS),
    ("No", PermissionResponse.DENY),
]


class InlinePermissionWidget(Vertical, can_focus=True):
    """渲染在聊天区域内部的内联权限确认提示。

    工具名 + 描述 + 带编号的选项，三种操作方式都支持：
    方向键 + 回车、数字键 1/2/3、鼠标直接点某一项；y / n 等价 Yes / No，
    Esc 视为拒绝。

    鼠标点击必须真的能选中：否则用户看到「Yes」就去点它，点不动之后
    往往按 Esc 关掉弹窗，最终被判成「用户拒绝了本次操作」。
    """

    BINDINGS = [
        Binding("up", "cursor_up", "Up", priority=True),
        Binding("down", "cursor_down", "Down", priority=True),
        Binding("enter", "select", "Select", priority=True),
        Binding("escape", "deny", "Deny", priority=True),
        Binding("1", "pick(0)", "Option 1", show=False, priority=True),
        Binding("2", "pick(1)", "Option 2", show=False, priority=True),
        Binding("3", "pick(2)", "Option 3", show=False, priority=True),
        Binding("y", "allow", "Yes", show=False, priority=True),
        Binding("n", "deny", "No", show=False, priority=True),
    ]

    class Responded(Message):


        def __init__(self, response: PermissionResponse) -> None:
            super().__init__()
            self.response = response

    def __init__(self, tool_name: str, description: str, **kwargs) -> None:
        super().__init__(id="perm-inline", **kwargs)
        self._tool_name = tool_name
        self._description = description
        self._cursor = 0

    def compose(self) -> ComposeResult:
        yield Static(self._header_content(), id="perm-content")
        for i, _option in enumerate(_PERM_OPTIONS):
            yield Static(
                self._option_content(i),
                id=f"perm-opt-{i}",
                classes="perm-option",
            )

    def on_mount(self) -> None:
        self.focus()

    def _header_content(self) -> str:
        lines = []
        lines.append(f"\n  [bold yellow]{self._tool_name} command[/bold yellow]\n")
        lines.append(f"    {self._description}\n")
        lines.append("  [dim]This command requires approval[/dim]\n")
        lines.append("  Do you want to proceed?\n")
        return "\n".join(lines)

    def _option_content(self, index: int) -> str:
        label = _PERM_OPTIONS[index][0]
        if index == self._cursor:
            return f" [bold cyan]❯[/bold cyan] [bold]{index + 1}. {label}[/bold]"
        return f"   [dim]{index + 1}. {label}[/dim]"

    def _refresh(self) -> None:
        for i in range(len(_PERM_OPTIONS)):
            self.query_one(f"#perm-opt-{i}", Static).update(self._option_content(i))

    def on_click(self, event: events.Click) -> None:
        """鼠标点某一项 = 选中它并立即确认。"""
        widget_id = getattr(event.widget, "id", "") or ""
        if not widget_id.startswith("perm-opt-"):
            return
        try:
            index = int(widget_id.rsplit("-", 1)[1])
        except ValueError:
            return
        if 0 <= index < len(_PERM_OPTIONS):
            self._cursor = index
            self._refresh()
            self.action_select()

    def action_cursor_up(self) -> None:
        if self._cursor > 0:
            self._cursor -= 1
            self._refresh()

    def action_cursor_down(self) -> None:
        if self._cursor < len(_PERM_OPTIONS) - 1:
            self._cursor += 1
            self._refresh()

    def action_pick(self, index: int | str) -> None:
        # Binding 里的 "pick(0)" 传进来的可能是字符串，统一转一下
        try:
            idx = int(index)
        except (TypeError, ValueError):
            return
        if 0 <= idx < len(_PERM_OPTIONS):
            self._cursor = idx
            self._refresh()
            self.action_select()

    def action_allow(self) -> None:
        self.post_message(self.Responded(PermissionResponse.ALLOW))

    def action_select(self) -> None:
        _label, response = _PERM_OPTIONS[self._cursor]
        self.post_message(self.Responded(response))

    def action_deny(self) -> None:
        self.post_message(self.Responded(PermissionResponse.DENY))
