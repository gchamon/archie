# Markdown Syntax Highlight Test

This file is intended for manual Neovim markdown highlighting checks.

## Headers

# Heading Level 1

## Heading Level 2

### Heading Level 3

#### Heading Level 4

##### Heading Level 5

###### Heading Level 6

## Emphasis And Inline Elements

Plain text next to *italic*, **bold**, ***bold italic***, ~~strikethrough~~, and `inline code`.

A [link to the Arch Wiki](https://wiki.archlinux.org/) and an automatic URL <https://neovim.io/>.

Escape test: \*this should not be italic\*.

## Lists

- Unordered item
- Unordered item with `inline code`
  - Nested unordered item
  - Nested item with **strong text**

1. Ordered item
2. Ordered item
3. Ordered item with a [reference link][archie-repo]

## Task List

- [x] Completed task
- [ ] Pending task

## Blockquote

> Archie is a living system configuration.
>
> This paragraph exists to verify blockquote highlighting and wrapping.

## Horizontal Rule

---

## Tables

| Tool | Purpose | Notes |
| --- | --- | --- |
| `marksman` | Markdown LSP | Provides LSP features, not syntax colors |
| `tree-sitter` | Parsing and captures | Drives markdown highlighting |
| `lunar.nvim` | Colorscheme | Provides the base palette |

## Fenced Code Blocks

```lua
local message = "hello from lua"
print(message)
```

```bash
#!/bin/bash
set -euo pipefail
echo "hello from bash"
```

```json
{
  "name": "archie",
  "enabled": true,
  "features": ["markdown", "treesitter", "lsp"]
}
```

```yaml
plugins:
  - marksman
  - nvim-treesitter
theme: lunar
```

```diff
- old heading background
+ new heading background
```

```text
Plain text fence for comparison.
```

## Indented Code Block

    function legacy_example()
      return "indented code block"
    end

## Definition-Like Content

Term
: This line is useful to see how plain markdown text is rendered around punctuation.

## HTML

<details>
  <summary>HTML block inside Markdown</summary>
  <p>This checks embedded HTML highlighting.</p>
</details>

## Mixed Paragraph

Markdown can include footnotes,[^highlight] entities like &rarr;, and reference-style links such as [Archie][archie-repo].

## Footnotes

Here is a statement with a footnote.[^one]

[^one]: This is a footnote definition.
[^highlight]: Footnotes are useful to test less common captures.

[archie-repo]: https://example.com/archie
