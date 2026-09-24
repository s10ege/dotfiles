# Cheatsheet: WezTerm + tmux + Neovim + Claude Code

## How to read this

| Written as | Means |
|---|---|
| `prefix` | `Ctrl+Space`, let go, then press the next key (tmux) |
| `<leader>` | `Space` (Neovim) |
| `C-x` / `Ctrl+x` | hold Ctrl, press x |
| normal mode | Neovim's default mode for moving around. `Esc` always takes you back here |
| insert mode | typing text (`i` to enter) |
| visual mode | selecting text (`v` to enter) |

**Stuck? `Space Enter` (nvim) or `prefix Enter` (anywhere) opens a Claude helper.**
Ask it anything about this setup; `prefix Enter` again hides it (the chat is kept).

Lost in Neovim? Press `Space` and wait: a menu shows what comes next.
`<leader>sk` searches **every** keymap you have.

---

## Daily flow

1. `cd ~/myproject && tmux new -s myproject` starts a session (next time: `tmux attach -t myproject`)
2. `nvim .` opens the editor
3. `prefix C` opens Claude Code on the right
4. `Ctrl+h` / `Ctrl+l` jumps between nvim and Claude
5. When Claude edits a file, go back to nvim (it reloads the file) and use `]c` / `[c` to jump through the changes

---

## tmux (`tmux/.config/tmux/tmux.conf`)

| Keys | Does |
|---|---|
| `prefix \|` | split left/right |
| `prefix -` | split top/bottom |
| `prefix C` | open Claude Code in a split on the right |
| `Ctrl+h/j/k/l` | move between panes (works across nvim splits too) |
| `prefix z` | zoom the pane to full screen (press again to unzoom) |
| `prefix H/J/K/L` | resize the pane (hold to repeat) |
| `prefix x` | close the pane |
| `prefix c` | new window (tab) |
| `prefix 1..9` | go to window N |
| `prefix ,` | rename the window |
| `prefix d` | detach (the session keeps running; `tmux attach` to return) |
| `prefix s` | list and switch sessions |
| `prefix [` | scroll/copy mode: `v` selects, `y` copies, `q` quits |
| `prefix r` | reload the tmux config |

The mouse works too: click panes, drag borders, scroll.

---

## Neovim essentials

| Keys | Does |
|---|---|
| `i` / `a` / `o` | insert before the cursor / after the cursor / on a new line |
| `Esc` | back to normal mode (also clears the search highlight) |
| `:w` / `:q` / `:wq` | save / quit / save and quit |
| `h j k l` | left, down, up, right |
| `w` / `b` | next / previous word |
| `gg` / `G` | top / bottom of the file |
| `u` / `Ctrl+r` | undo / redo |
| `dd` / `yy` / `p` | delete line / copy line / paste |
| `/text` then `n` | search, then jump to the next match |

Want more? Run `:Tutor`. It's a 30-minute interactive lesson.

## Neovim: your shortcuts

**Find things (Telescope)**

| Keys | Does |
|---|---|
| `<leader>sf` | find a file by name |
| `<leader>sg` | search text in all files (grep) |
| `<leader>sw` | search the word under the cursor |
| `<leader>/` | search in the current file |
| `<leader><leader>` | switch between open files |
| `<leader>s.` | recent files |
| `<leader>sr` | reopen the last search |
| `<leader>sh` | search Neovim help |
| `<leader>sk` | search keymaps |
| `<leader>sn` | search your Neovim config files |

**Code (needs a language server; they install automatically through Mason)**

| Keys | Does |
|---|---|
| `K` | show docs for the thing under the cursor |
| `grd` | go to definition (`Ctrl+o` jumps back) |
| `grr` | find all references |
| `grn` | rename everywhere |
| `gra` | code actions (quick fixes) |
| `<leader>f` | format the file |
| `<leader>q` | list errors and warnings |
| `Ctrl+y` | accept the autocomplete suggestion (`Ctrl+n`/`Ctrl+p` to pick) |

**Git (gitsigns): great for reviewing what Claude changed**

| Keys | Does |
|---|---|
| `]c` / `[c` | next / previous changed block |
| `<leader>hp` | preview the change |
| `<leader>hr` | undo that change (reset hunk) |
| `<leader>hs` | stage that change |
| `<leader>hb` | who changed this line (blame) |
| `<leader>hd` | diff the whole file |

**Editing helpers (mini.nvim)**

| Keys | Does |
|---|---|
| `ci'` / `ci"` / `ci)` | change inside quotes / parentheses |
| `va)` | select around parentheses |
| `saiw)` | surround a word with `()` |
| `sd'` | delete the surrounding `'` |
| `sr)'` | replace the surrounding `)` with `'` |

---

## lazy.nvim (plugin manager)

Run `:Lazy` to open it. Inside the window:

| Key | Does |
|---|---|
| `I` | install missing plugins |
| `U` | update plugins |
| `S` | sync (install + update + clean) |
| `X` | clean (remove plugins you deleted from the config) |
| `C` | check for updates without installing |
| `R` | restore the versions in `lazy-lock.json` |
| `L` | log (what changed recently) |
| `P` | profile (what makes startup slow) |
| `?` | help |
| `q` | close |

**Add a plugin:** create `nvim/.config/nvim/lua/custom/plugins/<name>.lua`:

```lua
return {
  'author/plugin-name',
  opts = {},
}
```

Restart nvim and it installs. `theme.lua` and `tmux.lua` in the same folder are real examples.

**Remove a plugin:** delete its file, restart, then `:Lazy` → `X`.

**Updates:** after `U`, commit `lazy-lock.json`. If an update breaks something:
`git checkout nvim/.config/nvim/lazy-lock.json`, then `:Lazy` → `R`.

---

## Telescope (the search popup)

Open it with any `<leader>s…` key above. Then:

| Keys | Does |
|---|---|
| type | filter the results |
| `Ctrl+n` / `Ctrl+p` | move down / up |
| `Enter` | open |
| `Ctrl+v` / `Ctrl+x` | open in a vertical / horizontal split |
| `Ctrl+t` | open in a new tab |
| `Ctrl+u` / `Ctrl+d` | scroll the preview |
| `Ctrl+q` | send all results to the quickfix list |
| `Ctrl+/` | show all Telescope keys |
| `Ctrl+c` or `Esc Esc` | close |

---

## Treesitter (makes nvim understand code)

Treesitter gives better colors, indentation, and smart selection. It mostly works on its own: opening a file in a new language installs that language's parser automatically.

| Command / keys | Does |
|---|---|
| `:TSInstall python` | install a language manually |
| `:TSUpdate` | update all parsers |
| `:InspectTree` | show the code's syntax tree |
| `:Inspect` | what highlight group is under the cursor |
| `v` then `an` | select the surrounding code block; press `an` again to grow |
| `v` then `in` | shrink the selection back |

Broken? Run `:checkhealth nvim-treesitter`. Parsers need the `tree-sitter` program in `~/.local/bin`.

---

## Claude Code

| Keys | Does |
|---|---|
| `Enter` | send |
| `Shift+Enter` | new line |
| `Ctrl+G` | write the prompt in nvim (save + quit to return) |
| `Esc` | stop Claude mid-answer |
| `Esc Esc` | rewind to an earlier message |
| `Shift+Tab` | switch mode: normal → auto-accept edits → plan |
| `@` | mention a file (`@init.lua`) |
| `/` | commands (`/help`, `/clear`, `/init`, `/keybindings`) |
| `!` at the start | run a shell command (`!git status`) |
| `?` | show all shortcuts |
| `Up` / `Ctrl+R` | previous prompts / search prompt history |
| `Ctrl+O` | show the full transcript |
| `Ctrl+C` twice / `Ctrl+D` twice | quit |

---

## WezTerm (`wezterm/.wezterm.lua`)

| Keys | Does |
|---|---|
| right-click | paste |
| `Ctrl+Shift+C` / `Ctrl+Shift+V` | copy / paste |
| `Ctrl+=` / `Ctrl+-` / `Ctrl+0` | bigger / smaller / reset font |
| `Ctrl+Shift+R` | reload the config (it usually reloads by itself) |
| `Ctrl+Shift+P` | command palette (search every WezTerm action) |

---

## Changing shortcuts yourself

Yes, you can change everything. Each tool reads a plain text file in `~/dotfiles`:

| Tool | File | Example | Apply it |
|---|---|---|---|
| tmux | `tmux/.config/tmux/tmux.conf` | `bind g new-window lazygit` | `prefix r` |
| Neovim | `nvim/.config/nvim/lua/custom/plugins/keymaps.lua` (new file) | see below | restart nvim |
| WezTerm | `wezterm/.wezterm.lua` | see below | automatic |
| Claude Code | `~/.claude/keybindings.json` | run `/keybindings` inside Claude | automatic |

Neovim: your own keymaps, in `lua/custom/plugins/keymaps.lua`:

```lua
vim.keymap.set('n', '<leader>w', '<cmd>w<CR>', { desc = 'Save file' })
return {}
```

WezTerm: add this before `return config`:

```lua
config.keys = {
  { key = 't', mods = 'ALT', action = wezterm.action.SpawnTab 'CurrentPaneDomain' },
}
```

Tips:
- Before adding a key, check it isn't taken: `<leader>sk` in nvim, `tmux list-keys` in tmux.
- Or just ask Claude: *"add a shortcut in nvim that does X and explain it"*.
- After each change that works: `git add -A && git commit -m "..."`, so you can always go back.
