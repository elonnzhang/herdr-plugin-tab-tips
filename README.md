# Herdr Tab Tips

[中文说明](README.zh-CN.md)

A local Herdr plugin that shows the active pane in the tab bar and labels unlabeled panes. It does not change Herdr itself.

- gives unlabeled panes a useful border label (terminal title, cwd basename, or pane id)
- provides a `tab_bar_right` status command showing the active pane label and public id
- copies the active pane ID with a plugin action (`prefix+y` in the example config)

Clicking the tab-bar status area cannot copy the ID. Herdr does not expose a mouse hit target or click handler for `tab_bar_right`; that would require a Herdr core change. Use the plugin action instead.

`herdr plugin list` prints a `config:` path. That is the plugin's user config directory. It does not contain `plugin.py`. The source directory is `plugin_root` from `herdr plugin list --json`. Use `plugin_root` in `tab_bar_right`.

## Install from GitHub

```bash
herdr plugin install elonnzhang/herdr-plugin-tab-tips --yes
```

Verified install output:

```text
Installed local.herdr-plugin-tab-tips from elonnzhang/herdr-plugin-tab-tips.
Config: ~/.config/herdr/plugins/config/local.herdr-plugin-tab-tips
```

Human list:

```text
- local.herdr-plugin-tab-tips (Herdr Tab Tips) enabled [github:elonnzhang/herdr-plugin-tab-tips@<commit>]
  config: ~/.config/herdr/plugins/config/local.herdr-plugin-tab-tips
```

JSON `plugin_root` looks like:

```text
~/.config/herdr/plugins/github/local.herdr-plugin-tab-tips-<hash>
```

Print it:

```bash
herdr plugin list --plugin local.herdr-plugin-tab-tips --json
```

Copy `plugin.py` and `config.toml.example` from that `plugin_root`. Merge the example into `~/.config/herdr/config.toml`, replacing `/path/to/herdr-plugin-tab-tips` with `plugin_root`. Reload:

```bash
herdr server reload-config
```

Refresh a GitHub-managed checkout:

```bash
herdr plugin install elonnzhang/herdr-plugin-tab-tips --yes
```

## Install from a local checkout

```bash
herdr plugin link /path/to/herdr-plugin-tab-tips
```

Verified human list:

```text
- local.herdr-plugin-tab-tips (Herdr Tab Tips) enabled [local:/path/to/herdr-plugin-tab-tips]
  config: ~/.config/herdr/plugins/config/local.herdr-plugin-tab-tips
```

JSON `plugin_root` is the checkout path. Merge `config.toml.example` into `~/.config/herdr/config.toml`, replacing `/path/to/herdr-plugin-tab-tips` with that checkout path, then reload:

```bash
herdr server reload-config
```

The plugin preserves an existing pane label. It only assigns a label when the pane currently has none. Event hooks are short-lived commands; no daemon is needed.
