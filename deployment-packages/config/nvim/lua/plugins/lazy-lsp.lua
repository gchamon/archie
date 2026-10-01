return {
  "dundalek/lazy-lsp.nvim",
  dependencies = { "neovim/nvim-lspconfig" },
  config = function()
    require("lazy-lsp").setup({
      excluded_servers = {
        "bashls", -- configured by LazyVim's nvim-lspconfig spec
        "ccls", -- prefer clangd
        "denols", -- prefer eslint and ts_ls
        "docker_compose_language_service", -- yamlls should be enough?
        "flow", -- prefer eslint and ts_ls
        "ltex", -- grammar tool using too much CPU
        "quick_lint_js", -- prefer eslint and ts_ls
        "scry", -- archived on Jun 1, 2023
        "tailwindcss", -- associates with too many filetypes
        "biome", -- not mature enough to be default
        "oxlint", -- prefer eslint
        "basedpyright", -- too verbose
      },
      preferred_servers = {
        cs = { "csharp_ls" },
        -- Godot provides the GDScript language server on 127.0.0.1:6005.
        gdscript = { "gdscript" },
        markdown = { "marksman" },
        python = { "ruff", "pyright" },
        terraform = { "terraformls" },
      },
    })
  end,
}
