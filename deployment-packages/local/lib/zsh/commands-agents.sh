#!/usr/bin/env zsh

# Oh My Pi model profile commands
_omp:set-default() {
  local default_model="$1"
  local roles

  roles="$(omp config get modelRoles | jq -c --arg default "$default_model" '.default = $default')" || return 1
  omp config set modelRoles "$roles"
}

omp:openai() {
  _omp:set-default "openai-codex/gpt-6-luna:medium" || return 1
  omp \
    --smol openai-codex/gpt-6-luna:medium \
    --slow openai-codex/gpt-6-sol:medium \
    --plan openai-codex/gpt-5.6-terra:medium \
    --model openai-codex/gpt-6-luna:medium "$@"
}

omp:anthropic() {
  _omp:set-default "anthropic/claude-sonnet-4-6:medium" || return 1
  omp \
    --thinking medium \
    --smol anthropic/claude-haiku-4-5 \
    --slow anthropic/claude-opus-4-6 \
    --plan anthropic/claude-opus-4-6 \
    --model anthropic/claude-sonnet-4-6 "$@"
}

omp:antigravity() {
  _omp:set-default "google-antigravity/gemini-3.8-flash:medium" || return 1
  omp \
    --thinking medium \
    --smol google-antigravity/gemini-3.8-flash:low \
    --slow google-antigravity/gemini-3.1-pro:high \
    --plan google-antigravity/gemini-3.8-flash:high \
    --model google-antigravity/gemini-3.8-flash "$@"
}

omp:kimi() {
  _omp:set-default "kimi-code/kimi-for-coding:low" || return 1
  omp \
    --thinking low \
    --smol kimi-code/kimi-k2-turbo-preview \
    --slow kimi-code/kimi-for-coding:high \
    --plan kimi-code/kimi-for-coding:medium \
    --model kimi-code/kimi-for-coding "$@"
}

omp:kiro-gpt() {
  _omp:set-default "kiro/gpt-5.6-terra:medium" || return 1
  omp \
    --thinking medium \
    --smol kiro/gpt-6-luna:low \
    --slow kiro/gpt-6-sol:high \
    --plan kiro/gpt-6-sol:medium \
    --model kiro/gpt-5.6-terra "$@"
}

omp:qwen() {
  _omp:set-default "llamacpp-qwen38/qwen38-27b-single-iq4xs:low" || return 1
  omp \
    --smol openai-codex/gpt-6-luna \
    --slow openai-codex/gpt-6-sol \
    --plan openai-codex/gpt-5.6-terra \
    --model llamacpp-qwen38/qwen38-27b-single-iq4xs "$@"
}

omp:kiro-claude() {
  _omp:set-default "kiro/claude-sonnet-5:high" || return 1
  omp \
    --thinking high \
    --smol kiro/claude-sonnet-5:low \
    --slow kiro/claude-opus-5:high \
    --plan kiro/claude-opus-5:medium \
    --model kiro/claude-sonnet-5 "$@"
}

alias omp:gpt='omp:openai'
alias omp:gemini='omp:antigravity'
alias omp:claude='omp:anthropic'
alias omp:local='omp:qwen'
