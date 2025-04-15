return {
  "dundalek/lazy-lsp.nvim",
  dependencies = { "neovim/nvim-lspconfig" },
  opts = {
    servers = {
      bashls = {
        settings = {
          filetypes = { "sh", "zsh" },
        },
      },
    },
  },
  config = function()
    require("lazy-lsp").setup({
      excluded_servers = {
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
        markdown = {},
        python = { "ruff", "pyright" },
        terraform = { "terraformls" },
      },
    })
  end,
}
