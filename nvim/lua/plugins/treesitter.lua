return {
  "nvim-treesitter/nvim-treesitter",
  branch = "master",
  lazy = false,
  build = ":TSUpdate",
  config = function()
    treesitter = require("nvim-treesitter.configs")
    treesitter.setup({
      ensure_installed = {
        "eex",
        "elixir",
        "erlang",
        "heex",
        "html",
        "markdown",
        "markdown_inline",
        "surface",
      },
      highlight = { enable = true },
    })
  end,
}
