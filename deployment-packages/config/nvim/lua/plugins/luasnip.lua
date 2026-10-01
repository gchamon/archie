return {
  {
    "L3MON4D3/LuaSnip",
    dependencies = { "rafamadriz/friendly-snippets" },
    opts = function()
      require("luasnip.loaders.from_vscode").lazy_load()
      local luasnip = require("luasnip")
      luasnip.add_snippets("bash", require("snippets.bash"))
      luasnip.filetype_extend("sh", { "bash" })
    end,
  },
  {
    "saghen/blink.cmp",
    optional = true,
    opts = {
      snippets = { preset = "luasnip" },
    },
  },
}
