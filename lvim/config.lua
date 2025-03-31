-- Read the docs: https://www.lunarvim.org/docs/configuration
-- Video Tutorials: https://www.youtube.com/watch?v=sFA9kX-Ud_c&list=PLhoH5vyxr6QqGu0i7tt_XoVK9v-KvZ3m6
-- Forum: https://www.reddit.com/r/lunarvim/
-- Discord: https://discord.com/invite/Xb9B4Ny
vim.opt.relativenumber = true
vim.opt.number = true
vim.opt.shiftwidth = 4
vim.opt.tabstop = 4
vim.opt.textwidth = 90
lvim.format_on_save.enabled = true

lvim.plugins = {
    { "rmagatti/logger.nvim" },
    {
        "luckasRanarison/tree-sitter-hyprlang",
        dependencies = { "nvim-treesitter/nvim-treesitter" },
    },
    {
        "rmagatti/goto-preview",
        config = function()
            require('goto-preview').setup {
                width = 120,             -- Width of the floating window
                height = 25,             -- Height of the floating window
                default_mappings = true, -- Bind default mappings
                debug = false,           -- Print debug information
                opacity = nil,           -- 0-100 opacity level of the floating window where 100 is fully transparent.
                post_open_hook = nil     -- A function taking two arguments, a buffer and a window to be ran as a hook.
                -- You can use "default_mappings = true" setup option
                -- Or explicitly set keybindings
                -- vim.cmd("nnoremap gpd <cmd>lua require('goto-preview').goto_preview_definition()<CR>")
                -- vim.cmd("nnoremap gpi <cmd>lua require('goto-preview').goto_preview_implementation()<CR>")
                -- vim.cmd("nnoremap gP <cmd>lua require('goto-preview').close_all_win()<CR>")
            }
        end
    },
    {
        "nvimtools/none-ls.nvim",
        config = function()
            null_ls = require("null-ls")
            null_ls.setup({
                sources = {
                    -- null_ls.builtins.diagnostics.pylint.with({
                    --     diagnostics_postprocess = function(diagnostic)
                    --         diagnostic.code = diagnostic.message_id
                    --     end,
                    -- }),
                    null_ls.builtins.code_actions.refactoring,
                    -- null_ls.builtins.diagnostics.mypy,
                    null_ls.builtins.formatting.isort,
                    -- null_ls.builtins.formatting.black
                }
            })
        end,
        dependencies = { "nvim-lua/plenary.nvim" },
    },
    {
        "ThePrimeagen/refactoring.nvim",
        dependencies = {
            "nvim-lua/plenary.nvim",
            "nvim-treesitter/nvim-treesitter",
        },
        config = function()
            require("refactoring").setup()
        end,
    },
    { "AndrewRadev/linediff.vim" },
    {
        "tpope/vim-surround",

        -- make sure to change the value of `timeoutlen` if it's not triggering correctly, see https://github.com/tpope/vim-surround/issues/117
        -- setup = function()
        --  vim.o.timeoutlen = 500
        -- end
    },
    {
        "Mofiqul/vscode.nvim",
        lazy = false,
        priority = 1000,
        config = function()
            -- local c = require('vscode.colors').get_colors()
            require('vscode').setup({
                -- Alternatively set style in setup
                -- style = 'light'

                -- Enable transparent background
                -- transparent = true,

                -- Enable italic comment
                -- italic_comments = true,

                -- Disable nvim-tree background color
                -- disable_nvimtree_bg = true,

                -- Override colors (see ./lua/vscode/colors.lua)
                -- color_overrides = {
                --     vscLineNumber = '#FFFFFF',
                -- },

                -- Override highlight groups (see ./lua/vscode/theme.lua)
                -- group_overrides = {
                --     -- this supports the same val table as vim.api.nvim_set_hl
                --     -- use colors from this colorscheme by requiring vscode.colors!
                --     Cursor = { fg=c.vscDarkBlue, bg=c.vscLightGreen, bold=true },
                -- }
            })
            require('vscode').load()
        end,
    }
}

local treesitter = require "nvim-treesitter.configs"

treesitter.setup {
    indent = { enable = true, disable = { "python" } }
}

-- local formatters = require "lvim.lsp.null-ls.formatters"
-- formatters.setup {
--     { name = "black" },
--     {
--         name = "prettier",
--         ---@usage arguments to pass to the formatter
--         -- these cannot contain whitespace
--         -- options such as `--line-width 80` become either `{"--line-width", "80"}` or `{"--line-width=80"}`
--         args = { "--print-width", "100" },
--         ---@usage only start in these filetypes, by default it will attach to all filetypes it supports
--         filetypes = { "typescript", "typescriptreact" },
--     },
-- }

local linters = require "lvim.lsp.null-ls.linters"
linters.setup {
    -- { name = "black" },
    {
        name = "shellcheck",
        args = { "--severity", "warning" },
    },
}

-- local code_actions = require "lvim.lsp.null-ls.code_actions"
-- code_actions.setup {
--     {
--         name = "proselint",
--     },
-- }
--

local bashls_options = {
    filetypes = { "sh", "zsh" }
}
require("lvim.lsp.manager").setup("bashls", bashls_options)
