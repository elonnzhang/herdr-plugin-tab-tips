# Herdr Tab Tips

在 tab bar 右侧显示当前 pane，给未命名 pane 加 label，并用 `prefix+y` 复制当前 pane id。

`tab_bar_right` 要用源码目录 `plugin_root`，不要用 `herdr plugin list` 里的 `config:`。

![图示](img/image.png)

## GitHub 安装

```bash
herdr plugin install elonnzhang/herdr-plugin-tab-tips --yes
herdr plugin list --plugin local.herdr-plugin-tab-tips --json
```

从 JSON 里取出 `plugin_root`。把 `config.toml.example` 合并进 `~/.config/herdr/config.toml`，把 `/path/to/herdr-plugin-tab-tips` 换成这个路径，然后：

```bash
herdr server reload-config
```

## 本地安装

```bash
herdr plugin link /path/to/herdr-plugin-tab-tips
```

把 `config.toml.example` 合并进 `~/.config/herdr/config.toml`，把 `/path/to/herdr-plugin-tab-tips` 换成本地检出路径，然后：

```bash
herdr server reload-config
```

## 配置

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

默认 prefix 是 `ctrl+b`。已有 pane label 不会被覆盖。
