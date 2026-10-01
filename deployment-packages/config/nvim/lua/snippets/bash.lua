local snippet = require("luasnip").snippet
local text = require("luasnip").text_node

return {
  snippet({
    trig = "scriptdir",
    name = "Script directory",
    dscr = "Resolve the directory containing this Bash script",
  }, text([[SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )]])),
}
