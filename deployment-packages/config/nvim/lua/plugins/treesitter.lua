return {
  "nvim-treesitter/nvim-treesitter",
  opts = function(_, opts)
    vim.list_extend(opts.ensure_installed, {
      "c_sharp",
      "eex",
      "elixir",
      "erlang",
      "gdscript",
      "heex",
      "surface",
    })
  end,
}
