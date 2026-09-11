# Herdr Tab Tips

本地 Herdr 插件。它只做三件事，不修改 Herdr 核心：

- 给还没有名称的 pane 自动加上边框 label（优先终端标题，其次目录名，最后用 pane id）
- 在 tab bar 右侧显示当前激活 pane 的 label 和 public id
- 用插件动作复制当前 pane id（示例快捷键是 `prefix+y`）

`tab_bar_right` 状态区不能点击复制。Herdr 没有给这段文字提供鼠标命中区域，纯插件无法给它加点击行为。复制请用快捷键。

普通 `herdr plugin list` 里的 `config:` 是插件自己的配置目录，里面没有 `plugin.py`，不能填进 `tab_bar_right`。源码目录只在 JSON 的 `plugin_root`：

```bash
herdr plugin list --plugin local.herdr-plugin-tab-tips --json
```

## 从 GitHub 安装

```bash
herdr plugin install elonnzhang/herdr-plugin-tab-tips --yes
```

实测安装输出：

```text
Installed local.herdr-plugin-tab-tips from elonnzhang/herdr-plugin-tab-tips.
Config: ~/.config/herdr/plugins/config/local.herdr-plugin-tab-tips
```

这里的 `Config:` 和 list 里的 `config:` 是同一类路径，不是 `plugin.py` 所在目录。

文本 list：

```text
- local.herdr-plugin-tab-tips (Herdr Tab Tips) enabled [github:elonnzhang/herdr-plugin-tab-tips@<commit>]
  config: ~/.config/herdr/plugins/config/local.herdr-plugin-tab-tips
```

JSON 里的 `plugin_root` 类似：

```text
~/.config/herdr/plugins/github/local.herdr-plugin-tab-tips-<hash>
```

把这个目录下的 `config.toml.example` 合并进 `~/.config/herdr/config.toml`，把示例里的 `/path/to/herdr-plugin-tab-tips` 换成这个 `plugin_root`，然后重新加载：

```bash
herdr server reload-config
```

刷新 GitHub 管理的安装：

```bash
herdr plugin install elonnzhang/herdr-plugin-tab-tips --yes
```

## 本地安装

```bash
herdr plugin link /path/to/herdr-plugin-tab-tips
```

实测文本 list：

```text
- local.herdr-plugin-tab-tips (Herdr Tab Tips) enabled [local:/path/to/herdr-plugin-tab-tips]
  config: ~/.config/herdr/plugins/config/local.herdr-plugin-tab-tips
```

这时 JSON 的 `plugin_root` 就是本地检出路径。把 `config.toml.example` 合并进 `~/.config/herdr/config.toml`，把 `/path/to/herdr-plugin-tab-tips` 换成这个路径，然后重新加载：

```bash
herdr server reload-config
```

## 需要的 Herdr 配置

```toml
[ui]
pane_borders = "always"
pane_outer_borders = true
tab_bar_right = [
  { type = "command", command = "python3 /path/to/herdr-plugin-tab-tips/plugin.py status", interval_seconds = 1, timeout_seconds = 2 },
]
tab_bar_right_separator = " · "

[[keys.command]]
key = "prefix+y"
type = "plugin_action"
command = "local.herdr-plugin-tab-tips.copy-pane-id"
description = "copy active pane ID"
```

GitHub 安装后，把上面的 `/path/to/herdr-plugin-tab-tips` 换成 `herdr plugin list --json` 给出的 `plugin_root`。本地 link 后，换成检出路径。

默认 prefix 是 `ctrl+b`。因此 `prefix+y` 的按法是：先按 `Ctrl+B`，再按 `y`。

## 显示和刷新

tab bar 右侧显示类似：

```text
π - herdr · wM:p1
```

这是定时刷新，不是实时，也不是切 pane 立刻更新。当前间隔是 1 秒：配置加载后立刻跑一次，之后每秒再跑一次。切 pane 后最多大约 1 秒才会换成新的 id。

## 复制 pane id

`prefix+y` 会把当前激活 pane 的 public id 写到系统剪贴板。复制成功后会弹出提示。

请到 Herdr 外面的应用里用 `Cmd+V` 验证，例如备忘录或浏览器地址栏。如果只在 Herdr pane 里粘贴，外层终端可能自己处理粘贴，看起来会不像刚复制的 pane id。

## 行为说明

- 已有 pane label 不会被覆盖。只有 label 为空时才会自动命名。
- 事件钩子是一次性命令，不常驻后台。
- 插件本身不能自动写入 `[ui]` 配置，需要用户合并一次 `config.toml.example`。
