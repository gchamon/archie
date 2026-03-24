return {
  {
    "LunarVim/lunar.nvim",
    priority = 1000,
    config = function()
      local function set_markdown_heading_highlights()
        vim.api.nvim_set_hl(0, "@markup.heading.1", { fg = "#E6EAF2", bg = "", bold = true }) -- Dark navy
        vim.api.nvim_set_hl(0, "@markup.heading.2", { fg = "#E6EAF2", bg = "", bold = true }) -- Darker teal
        vim.api.nvim_set_hl(0, "@markup.heading.3", { fg = "#E6EAF2", bg = "", bold = true }) -- Dark green
        vim.api.nvim_set_hl(0, "@markup.heading.4", { fg = "#E6EAF2", bg = "", bold = true }) -- Darker violet
        vim.api.nvim_set_hl(0, "@markup.heading.5", { fg = "#E6EAF2", bg = "", bold = true }) -- Dark amber
        vim.api.nvim_set_hl(0, "@markup.heading.6", { fg = "#E6EAF2", bg = "", bold = true }) -- Dark brown-orange
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
