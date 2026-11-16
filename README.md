# PandaCode

PandaCode 是一个运行在终端的 AI 编程助手，基于 Python 实现。它在终端里提供对话式编码体验：理解你的需求、读写代码、执行命令、管理任务，全程需要你确认关键操作，安全可控。

## 功能特性

- **多协议模型接入**：支持 Anthropic、OpenAI 及任意 OpenAI 兼容协议的服务商，可配置多个 provider，API Key 支持环境变量引用
- **内置工具集**：文件读写与编辑、代码搜索（glob / grep）、diff 查看、Bash 命令执行、向用户提问等
- **子代理（Agent）**：内置探索、规划、通用、验证等代理，均以 Markdown 定义，可按同样格式自定义新代理
- **多代理团队协作**：支持创建团队、代理间消息通信，以及协调者（coordinator）多团队模式
- **MCP 接入**：支持 stdio 与 HTTP 两种方式挂载 MCP（Model Context Protocol）服务器，扩展外部工具
- **权限系统**：default / acceptEdits / plan / bypassPermissions 四种模式，敏感操作弹窗确认
- **记忆系统**：基于 Markdown 索引的持久化记忆，支持自动整理与去重（consolidation）
- **上下文管理**：对话压缩（compact）、会话恢复、rewind 回退，context window 自动探测（配置覆盖 > 服务商接口 > 内置映射 > 保守默认值）
- **技能（Skills）**：可安装、加载、注册技能，按需扩展助手能力
- **Hooks**：在特定事件上触发 command / prompt / http / agent 动作
- **Git worktree 隔离**：在独立 worktree 中进行功能开发，支持目录符号链接与过期清理
- **沙箱**：可选的 OS 级沙箱，支持网络开关与自动放行策略
- **斜杠命令**：`/clear`、`/compact`、`/plan`、`/review`、`/rewind`、`/session`、`/memory`、`/mcp`、`/status`、`/tasks`、`/worktree`、`/sandbox`、`/permission`、`/skill`、`/trace`、`/help` 等

## 环境要求

- Python >= 3.11
- 推荐使用 [uv](https://docs.astral.sh/uv/) 管理依赖（也可使用 pip）

## 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/<your-username>/PandaCode.git
cd PandaCode

# 2. 安装依赖（二选一）
uv sync                # 推荐
# 或
pip install -e .

# 3. 创建配置文件（见「配置说明」章节）
mkdir -p .pandacode
# 编辑 .pandacode/config.yaml，填入你的模型配置
```

## 使用方法

### 启动

```bash
uv run pandacode
# 或安装后直接运行
pandacode
```

启动后进入终端交互界面，直接输入自然语言描述需求即可，例如：

```
> 帮我在项目里找到所有使用了旧接口的调用点，并列出文件清单
> 给 utils 模块补充单元测试
> 重构这个函数，把副作用从计算逻辑里拆出来
```

### 常用命令

| 命令 | 作用 |
| --- | --- |
| `/help` | 查看所有可用命令 |
| `/status` | 查看当前状态与配置 |
| `/compact` | 压缩当前对话，释放上下文窗口 |
| `/session` | 管理会话（切换 / 恢复） |
| `/rewind` | 回退对话到指定位置 |
| `/plan` | 进入规划模式，先出方案再动手 |
| `/permission` | 查看 / 切换权限模式 |
| `/memory` | 查看与维护记忆 |
| `/mcp` | 管理已挂载的 MCP 服务器 |
| `/tasks` | 查看后台任务 |
| `/worktree` | 管理隔离工作区 |
| `/clear` | 清空当前对话 |

### 权限模式

- `default`：所有敏感操作（写文件、执行命令等）逐次弹窗确认
- `acceptEdits`：自动接受文件编辑，其他操作仍需确认
- `plan`：只读模式，助手只能查看与分析，不改动任何内容
- `bypassPermissions`：跳过所有确认（谨慎使用）

## 配置说明

PandaCode 按以下顺序加载并合并配置（后层覆盖前层）：

1. `~/.pandacode/config.yaml` — 全局配置
2. `<项目根目录>/.pandacode/config.yaml` — 项目配置
3. `<项目根目录>/.pandacode/config.local.yaml` — 本地覆盖（建议不要提交到仓库）

### 配置示例

以下示例中的所有值均为占位符，请替换为你自己的信息：

```yaml
# .pandacode/config.yaml
providers:
  - name: <your-provider-name>          # 自定义名称
    protocol: <anthropic | openai | openai-compat>
    base_url: <https://your-api-endpoint>
    model: <your-model-name>
    api_key: ${<YOUR_API_KEY_ENV_VAR>}  # 推荐引用环境变量；也可留空，
                                        # 由 ANTHROPIC_API_KEY / OPENAI_API_KEY 兜底
    thinking: false                     # 是否启用思考模式
    context_window: 0                   # 0 = 自动探测；正数 = 显式覆盖
    max_output_tokens: 0                # 0 = 按默认规则推导

permission_mode: default                # default | acceptEdits | plan | bypassPermissions

mcp_servers:
  - name: <your-mcp-server-name>
    command: <server-command>           # stdio 方式
    args: [<server-args>]
    env:
      <YOUR_MCP_ENV_VAR>: <value>
  - name: <your-remote-mcp-server-name>
    url: <https://your-mcp-endpoint>    # HTTP 方式
    headers:
      Authorization: <your-auth-header>

sandbox:
  enabled: false                        # 是否启用 OS 级沙箱
  auto_allow: false                     # 沙箱开启时是否自动放行命令
  network_enabled: false                # 沙箱内是否允许网络访问

worktree:
  symlink_directories: [node_modules, .venv, vendor]
  stale_cleanup_interval: 3600          # 过期检查间隔（秒）
  stale_cutoff_hours: 24                # 超过该时长的 worktree 视为过期

enable_fork: true                       # 是否允许派生子代理
enable_verification_agent: false        # 是否启用验证代理
teammate_mode: ""                       # 留空或 in-process
enable_coordinator_mode: false          # 是否启用协调者多团队模式
```

### 说明

- **API Key 安全**：`api_key` 字段支持 `${ENV_VAR}` 语法引用环境变量，请勿将真实密钥写入配置文件；`config.local.yaml` 与整个 `.pandacode/` 目录已被 `.gitignore` 忽略
- **context window 解析优先级**：显式配置 > 服务商接口自动拉取 > 内置模型映射表 > 保守默认值
- **MCP 服务器**：同时支持 `command`（stdio）与 `url`（HTTP）两种挂载方式，`env` 中的值同样支持环境变量引用

## 运行测试

```bash
uv run pytest
```

涉及真实模型的端到端测试默认跳过，需要设置相应的测试环境变量后才会执行。

## 贡献指南

欢迎参与贡献：

1. Fork 本仓库
2. 创建你的分支：`git checkout -b <your-branch-name>`
3. 完成改动并补充测试，确保 `uv run pytest` 全部通过
4. 提交改动，commit message 直接描述做了什么即可
5. 发起 Pull Request，说明改动内容与动机

约定：

- 代码标识符使用 snake_case 命名
- 注释与文档使用中文
- 新功能请附带对应的测试用例

## 许可证

本项目尚未声明许可证。如需使用或分发代码，请先联系仓库维护者确认授权，或等待许可证文件补充。
