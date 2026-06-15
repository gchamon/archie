local M = {}

local function sorted_keys(tbl)
  local keys = vim.tbl_keys(tbl)
  table.sort(keys)
  return keys
end

local function stop_session_writes()
  vim.opt.shada = ""
  vim.opt.swapfile = false
  pcall(function()
    vim.loader.enable(false)
  end)
  pcall(function()
    vim.lsp.set_log_level("off")
  end)
  pcall(function()
    require("persistence").stop()
  end)
end

local function edit_debug_file()
  local file = vim.env.NVIM_DEBUG_FILE
  if not file or file == "" then
    error("NVIM_DEBUG_FILE is required")
  end

  vim.cmd.edit(vim.fn.fnameescape(file))
end

local function installed_parsers()
  local installed = {}
  for _, parser in ipairs(require("nvim-treesitter").get_installed("parsers")) do
    installed[parser] = true
  end
  return installed
end

local function parser_report()
  local filetype = vim.bo.filetype
  local language = vim.treesitter.language.get_lang(filetype) or ""
  local installed = installed_parsers()

  print("treesitter-language: " .. (language ~= "" and language or "none"))
  print("parser-installed: " .. (installed[language] and "yes" or "no"))

  for _, query in ipairs({ "highlights", "indents", "folds" }) do
    local ok = language ~= "" and vim.treesitter.query.get(language, query) ~= nil
    print("query-" .. query .. ": " .. (ok and "yes" or "no"))
  end
end

local function loaded_plugins()
  local plugins = require("lazy.core.config").plugins
  local loaded = {}

  for name, plugin in pairs(plugins) do
    if plugin._ and plugin._.loaded then
      loaded[name] = true
    end
  end

  return loaded
end

local function loaded_after(before)
  local plugins = require("lazy.core.config").plugins
  local loaded = {}

  for name, plugin in pairs(plugins) do
    if plugin._ and plugin._.loaded and not before[name] then
      table.insert(loaded, name)
    end
  end

  table.sort(loaded)
  return loaded
end

local function print_loaded_after(before)
  local loaded = loaded_after(before)

  if #loaded == 0 then
    print("loaded-after-open: none")
    return
  end

  for _, name in ipairs(loaded) do
    print("loaded-after-open: " .. name)
  end
end

local function print_lsp_clients()
  vim.wait(3000, function()
    return #vim.lsp.get_clients({ bufnr = 0 }) > 0
  end, 100)

  local clients = vim.lsp.get_clients({ bufnr = 0 })
  if #clients == 0 then
    print("lsp: none")
    return
  end

  table.sort(clients, function(a, b)
    return a.name < b.name
  end)

  for _, client in ipairs(clients) do
    print("lsp: " .. client.name)
  end
end

local function print_file_header()
  print("file: " .. vim.api.nvim_buf_get_name(0))
  print("filetype: " .. vim.bo.filetype)
end

function M.lazy_list()
  local plugins = require("lazy.core.config").plugins

  for _, name in ipairs(sorted_keys(plugins)) do
    local plugin = plugins[name]
    local installed = plugin._ and plugin._.installed and "installed" or "missing"
    local loaded = plugin._ and plugin._.loaded and "loaded" or "not-loaded"
    local updates = plugin._ and plugin._.updates and "updates" or "current"

    print(string.format("%-36s %-10s %-10s %s", name, installed, loaded, updates))
  end
end

function M.mason_list()
  local registry = require("mason-registry")
  local packages = registry.get_installed_packages()

  table.sort(packages, function(a, b)
    return a.name < b.name
  end)

  for _, package in ipairs(packages) do
    local categories = package.spec.categories and table.concat(package.spec.categories, ",") or ""
    print(string.format("%-32s %s", package.name, categories))
  end
end

function M.lsp_list()
  local configs = require("lspconfig.configs")

  for _, name in ipairs(sorted_keys(configs)) do
    local config = configs[name]
    local default_config = config.document_config and config.document_config.default_config or {}
    local filetypes = default_config.filetypes and table.concat(default_config.filetypes, ",") or ""
    print(string.format("%-28s %s", name, filetypes))
  end
end

function M.ts_list()
  local parsers = require("nvim-treesitter").get_installed("parsers")
  table.sort(parsers)

  for _, parser in ipairs(parsers) do
    print(parser)
  end
end

function M.file_lsps()
  stop_session_writes()
  edit_debug_file()
  print_file_header()
  print_lsp_clients()
end

function M.file_parsers()
  stop_session_writes()
  edit_debug_file()
  print_file_header()
  parser_report()
end

function M.file_plugins()
  stop_session_writes()
  local before = loaded_plugins()
  edit_debug_file()
  vim.wait(1000)
  print("file: " .. vim.api.nvim_buf_get_name(0))
  print_loaded_after(before)
end

function M.file_debug()
  stop_session_writes()
  local before = loaded_plugins()
  edit_debug_file()
  print_file_header()
  print_lsp_clients()
  parser_report()
  print_loaded_after(before)
end

function M.run(command)
  local fn = M[command]
  if not fn then
    error("unknown admin command: " .. tostring(command))
  end

  fn()
end

return M
