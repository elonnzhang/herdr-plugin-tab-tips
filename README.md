# Herdr Tab Tips

[中文说明](README.zh-CN.md)

A local Herdr plugin that shows the active pane in the tab bar and labels unlabeled panes. It does not change Herdr itself.

- gives unlabeled panes a useful border label (terminal title, cwd basename, or pane id)
- provides a `tab_bar_right` status command showing the active pane label and public id
- copies the active pane ID with a plugin action (`prefix+y` in the example config)

Clicking the tab-bar status area cannot copy the ID. Herdr does not expose a mouse hit target or click handler for `tab_bar_right`; that would require a Herdr core change. Use the plugin action instead.

## Install from GitHub

```bash
herdr plugin install elonnzhang/herdr-plugin-tab-tips
```

Herdr clones the repo, validates `herdr-plugin.toml`, and registers the plugin. Use `--yes` for a noninteractive install.

Then print the installed plugin source directory. The `config:` line from `herdr plugin list` is the plugin's user config directory; it does not contain `plugin.py` and must not be used in `tab_bar_right`. The source directory is `plugin_root` in JSON:

```bash
herdr plugin list --json
```

Find `local.herdr-plugin-tab-tips` and copy its `plugin_root`. Merge that directory's `config.toml.example` into `~/.config/herdr/config.toml`, replacing `/path/to/herdr-plugin-tab-tips` with `plugin_root`. Reload:

```bash
herdr server reload-config
```

Reinstall from GitHub to refresh a managed checkout:

```bash
herdr plugin install elonnzhang/herdr-plugin-tab-tips --yes
```

## Install from a local checkout

```bash
herdr plugin link /path/to/herdr-plugin-tab-tips
```

Merge `config.toml.example` into `~/.config/herdr/config.toml`, replacing `/path/to/herdr-plugin-tab-tips` with the checkout path, then reload:

```bash
herdr server reload-config
```

The plugin preserves an existing pane label. It only assigns a label when the pane currently has none. Event hooks are short-lived commands; no daemon is needed.
