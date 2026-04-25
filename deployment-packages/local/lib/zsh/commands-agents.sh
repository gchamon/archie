#!/usr/bin/env zsh

# oh-my-pi aliases
alias omp:openai="omp --thinking medium --smol openai/gpt-5.4-nano --slow openai/gpt-5.4-pro --plan openai/gpt-5.4-pro --model openai/gpt-5.4 "
alias omp:anthropic="omp --thinking medium --smol anthropic/claude-haiku-4-5 --slow anthropic/claude-opus-4-6 --plan anthropic/claude-opus-4-6 --model anthropic/claude-sonnet-4-6 "
alias omp:google="omp --thinking high --smol google-gemini-cli/gemini-3.1-flash-lite-preview --slow google-gemini-cli/gemini-3.1-pro-preview --plan google-gemini-cli/gemini-3.1-pro-preview --model google-gemini-cli/gemini-3-flash-preview "
alias omp:kimi="omp --smol kimi-code/kimi-k2-turbo-preview --slow kimi-code/kimi-for-coding:high --plan kimi-code/kimi-for-coding:medium --model kimi-code/kimi-for-coding:low"
