return {
  {
    "neovim/nvim-lspconfig",
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
