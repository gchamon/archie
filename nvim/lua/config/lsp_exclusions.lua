-- LSP Exclusions Configuration
--
-- Define folder-specific LSP server exclusions.
-- Servers listed here will be prevented from attaching to buffers
-- whose paths match the specified directory patterns.
--
-- Usage:
--   Add entries in the format:
--   ["/absolute/path/to/project"] = { "server_name_1", "server_name_2" }
--
-- Examples:
--   ["/home/gchamon/Projects/legacy-app"] = { "eslint", "tsserver" }
--   ["/home/gchamon/Projects/python-project"] = { "pyright" }
--   ["/home/gchamon/.config"] = { "lua_ls" }
--
-- Notes:
--   - Paths should be absolute (no ~ expansion)
--   - Server names match the LSP client name (check with :LspInfo)
--   - Partial path matches work (e.g., "/home/user/Projects" matches all subdirectories)
--   - You can use vim.fn.expand("$HOME") for home directory if needed

local M = {}

M.exclusions = {
  -- Add your exclusions here
  -- Example:
  -- [vim.fn.expand("$HOME") .. "/Projects/target-project"] = { "eslint" },
  [vim.fn.expand("$HOME") .. "/Projects/alertd/alertd-core"] = { "eslint" },
}

return M
