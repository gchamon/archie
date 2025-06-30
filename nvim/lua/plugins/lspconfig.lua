return {
  {
    "neovim/nvim-lspconfig",
    config = function()
      local lspconfig = require("lspconfig")
      lspconfig.elixirls.setup({
        cmd = { "/usr/lib/elixir-ls/language_server.sh" },
      })
    end,
    opts = {
      -- Useful for debugging formatter issues
      format_notify = true,
      inlay_hints = { enabled = false },
      servers = {
        bashls = {
          filetypes = { "sh", "zsh" },
        },
      },
    },
  },
  {
    "adoyle-h/lsp-toggle.nvim",
    config = function()
      local lsp_toggle = require("lsp-toggle")
      lsp_toggle.setup({
        create_cmds = true,
        telescope = false,
      })
    end,
  },
}
