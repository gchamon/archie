-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
--
-- Add any additional autocmds here
-- with `vim.api.nvim_create_autocmd`
--
-- Or remove existing autocmds by their group name (which is prefixed with `lazyvim_` for the defaults)
-- e.g. vim.api.nvim_del_augroup_by_name("lazyvim_wrap_spell")

-- GitLab CI filetype detection
vim.api.nvim_create_autocmd({ "BufRead", "BufNewFile" }, {
  pattern = "*.gitlab-ci*.{yml,yaml}",
  callback = function()
    vim.bo.filetype = "yaml.gitlab"
  end,
})

-- Folder-specific LSP exclusions
-- Configuration is in lua/config/lsp_exclusions.lua
local function get_exclusions()
  local ok, lsp_exclusions = pcall(require, "config.lsp_exclusions")
  if not ok or not lsp_exclusions.exclusions then
    return nil
  end
  return lsp_exclusions.exclusions
end

local function is_path_excluded(bufpath, excluded_path)
  local escaped_path = vim.pesc(excluded_path)
  return bufpath:match("^" .. escaped_path) ~= nil
end

local function is_server_excluded(server_name, excluded_servers)
  for _, excluded_server in ipairs(excluded_servers) do
    if server_name == excluded_server then
      return true
    end
  end
  return false
end

local function log_exclusion(server_name, bufpath)
  vim.schedule(function()
    local log_msg = string.format(
      "[%s] LSP Exclusion: Stopped %s for %s",
      os.date("%Y-%m-%d %H:%M:%S"),
      server_name,
      bufpath
    )
    vim.fn.writefile({ log_msg }, vim.fn.stdpath("log") .. "/lsp_exclusions.log", "a")
  end)
end

local function should_exclude_client(client, bufpath, exclusions)
  for excluded_path, excluded_servers in pairs(exclusions) do
    if is_path_excluded(bufpath, excluded_path) and is_server_excluded(client.name, excluded_servers) then
      return true
    end
  end
  return false
end

vim.api.nvim_create_autocmd("LspAttach", {
  callback = function(args)
    local client = vim.lsp.get_client_by_id(args.data.client_id)
    if not client then
      return
    end

    local bufpath = vim.api.nvim_buf_get_name(args.buf)
    if bufpath == "" then
      return
    end

    local exclusions = get_exclusions()
    if not exclusions then
      return
    end

    if should_exclude_client(client, bufpath, exclusions) then
      log_exclusion(client.name, bufpath)
      vim.lsp.stop_client(client.id, true)
    end
  end,
})
