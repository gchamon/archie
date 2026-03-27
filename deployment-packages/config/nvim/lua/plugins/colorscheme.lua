return {
  {
    "LunarVim/lunar.nvim",
    priority = 1000,
    config = function()
      local function set_markdown_heading_highlights()
        vim.api.nvim_set_hl(0, "@markup.heading.1", { fg = "#D7DDE8", bg = "#706597", bold = true })
        vim.api.nvim_set_hl(0, "@markup.heading.1.markdown", { fg = "#D7DDE8", bg = "#706597", bold = true })
        vim.api.nvim_set_hl(0, "@markup.heading.2", { fg = "#D7DDE8", bg = "#657D91", bold = true })
        vim.api.nvim_set_hl(0, "@markup.heading.2.markdown", { fg = "#D7DDE8", bg = "#657D91", bold = true })
        vim.api.nvim_set_hl(0, "@markup.heading.3", { fg = "#D7DDE8", bg = "#6D8D76", bold = true })
        vim.api.nvim_set_hl(0, "@markup.heading.3.markdown", { fg = "#D7DDE8", bg = "#6D8D76", bold = true })
        vim.api.nvim_set_hl(0, "@markup.heading.4", { fg = "#D7DDE8", bg = "#A09A84", bold = true })
        vim.api.nvim_set_hl(0, "@markup.heading.4.markdown", { fg = "#D7DDE8", bg = "#A09A84", bold = true })
        vim.api.nvim_set_hl(0, "@markup.heading.5", { fg = "#D7DDE8", bg = "#987174", bold = true })
        vim.api.nvim_set_hl(0, "@markup.heading.5.markdown", { fg = "#D7DDE8", bg = "#987174", bold = true })
        vim.api.nvim_set_hl(0, "@markup.heading.6", { fg = "#D7DDE8", bg = "#8B5F78", bold = true })
        vim.api.nvim_set_hl(0, "@markup.heading.6.markdown", { fg = "#D7DDE8", bg = "#8B5F78", bold = true })
      end

      -- Apply lunar colorscheme
      vim.cmd("colorscheme lunar")

      -- Improve markdown heading contrast with darker background blocks
      set_markdown_heading_highlights()

      vim.api.nvim_create_autocmd("ColorScheme", {
        group = vim.api.nvim_create_augroup("MarkdownHeadingContrast", { clear = true }),
        pattern = "lunar",
        callback = set_markdown_heading_highlights,
      })
    end,
  },
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "lunar",
    },
  },
}
