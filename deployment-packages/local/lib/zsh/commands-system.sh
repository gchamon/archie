#!/usr/bin/env zsh

alias compton-restart="pkill compton && compton &> /dev/null &"
alias ffpm="firefox -ProfileManager "
alias myip='curl ipinfo.io/ip '
alias scheme='rlwrap scheme'
alias vm="vboxmanage "

cpi() {
  rsync -va --progress "$@"
}

de-reload() {
  hyprctl reload
  sleep 5
  hyprctl reload
}

dunst-history() {
  dunstctl history |
    jq -cr '.data | flatten(1) | .[] | {"html_text": .message.data, "timestamp": .timestamp.data}' |
    while read -r notification_data; do
      html_text=$(jq -r '.html_text' <<<$notification_data)
      timestamp=$(jq -r '.timestamp' <<<$notification_data)
      rendered=$(html2text <<<$html_text)
      if [[ -n $rendered ]]; then
        converted_timestamp=$(bc <<<"$(stat -c %Y /proc/1) + ($timestamp / 1000000)")
        rendered_timestamp=$(date +"%Y-%m-%dT%H:%M:%S%z" -d "@$converted_timestamp")
        echo timestamp: $rendered_timestamp
        echo message: $rendered
        echo ---------------------------------------
      fi
    done
}
