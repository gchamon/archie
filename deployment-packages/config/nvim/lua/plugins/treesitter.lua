return {
  "nvim-treesitter/nvim-treesitter",
  opts = function(_, opts)
    vim.list_extend(opts.ensure_installed, {
      "eex",
      "elixir",
      "erlang",
      "heex",
      "surface",
    })
  end,
}
