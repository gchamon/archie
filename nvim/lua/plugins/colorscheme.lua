return {
  {
    "LunarVim/lunar.nvim",
    priority = 1000,
    config = function()
      -- Apply lunar colorscheme
      vim.cmd("colorscheme lunar")

      -- Improve markdown heading contrast with brighter colors
      vim.api.nvim_set_hl(0, "@markup.heading.1.markdown", { fg = "#61AFEF", bold = true }) -- Bright blue
      vim.api.nvim_set_hl(0, "@markup.heading.2.markdown", { fg = "#56B6C2", bold = true }) -- Bright cyan
      vim.api.nvim_set_hl(0, "@markup.heading.3.markdown", { fg = "#98C379", bold = true }) -- Bright green
      vim.api.nvim_set_hl(0, "@markup.heading.4.markdown", { fg = "#C678DD", bold = true }) -- Bright magenta
      vim.api.nvim_set_hl(0, "@markup.heading.5.markdown", { fg = "#E5C07B", bold = true }) -- Bright yellow
      vim.api.nvim_set_hl(0, "@markup.heading.6.markdown", { fg = "#D19A66", bold = true }) -- Bright orange

      -- Also set fallback highlight groups for non-treesitter markdown
      vim.api.nvim_set_hl(0, "markdownH1", { fg = "#61AFEF", bold = true })
      vim.api.nvim_set_hl(0, "markdownH2", { fg = "#56B6C2", bold = true })
      vim.api.nvim_set_hl(0, "markdownH3", { fg = "#98C379", bold = true })
      vim.api.nvim_set_hl(0, "markdownH4", { fg = "#C678DD", bold = true })
      vim.api.nvim_set_hl(0, "markdownH5", { fg = "#E5C07B", bold = true })
      vim.api.nvim_set_hl(0, "markdownH6", { fg = "#D19A66", bold = true })
    end,
  },
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "lunar",
    },
  },
}
