#!/usr/bin/env zsh

alias compton-restart='pkill compton && compton &> /dev/null &'
alias ffpm='firefox -ProfileManager'
alias myip='curl ipinfo.io/ip'
alias scheme='rlwrap scheme'
alias vm='vboxmanage'

alias archie:status='archie system status'
alias archie:gui='archie gui'
alias archie:applet='archie applet'

alias archie:get-lid='archie system get lid-close-behavior'
alias archie:get-notifications='archie system get notifications'
alias archie:get-shy='archie system get shy-mode'
alias archie:get-share='archie system get share-state'
alias archie:get-kdeconnect='archie system get kdeconnect'
alias archie:get-power-profile='archie system get power-profile'
alias archie:get-waybar-theme='archie system get waybar-theme'
alias archie:get-brightness='archie system get brightness'

alias archie:set-hibernate='archie system set lid-close-behavior hibernate'
alias archie:set-lock='archie system set lid-close-behavior lock'
alias archie:set-none='archie system set lid-close-behavior none'
alias archie:set-notifications-on='archie system set notifications on'
alias archie:set-notifications-off='archie system set notifications off'
alias archie:set-shy-on='archie system set shy-mode on'
alias archie:set-shy-off='archie system set shy-mode off'
alias archie:set-kdeconnect-on='archie system set kdeconnect on'
alias archie:set-kdeconnect-off='archie system set kdeconnect off'
alias archie:set-performance='archie system set power-profile performance'
alias archie:set-balanced='archie system set power-profile balanced'
alias archie:set-power-saver='archie system set power-profile power-saver'
alias archie:set-waybar-cjbassi='archie system set waybar-theme cjbassi'
alias archie:set-waybar-mechabar='archie system set waybar-theme mechabar'
alias archie:set-waybar-tokyonight='archie system set waybar-theme tokyonight'
alias archie:set-brightness='archie system set brightness'

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

kitty:save-session() {
  if [[ -z ${KITTY_WINDOW_ID:-} ]]; then
    print -u2 -- "Run kitty:save-session inside a Kitty window."
    return 1
  fi

  print -u2 -- "Restoring this session will rerun active foreground processes. Check the saved session before restoring it."
  local confirm
  read -q "confirm?Save the current Kitty session? [y/N] " || {
    print
    return 1
  }
  print

  local session_dir="${XDG_DATA_HOME:-$HOME/.local/share}/kitty/sessions"
  local session_file="$session_dir/session-$(date '+%Y%m%d-%H%M%S-%N').kitty-session"
  mkdir -p "$session_dir" || return $?

  if ! kitten @ action save_as_session "--use-foreground-process --save-only ${(q)session_file}"; then
    print -u2 -- "Kitty could not save the session. Reload the Kitty config and confirm allow_remote_control yes is active."
    return 1
  fi

  print -r -- "Session file: $session_file"
  print -r -- "Restore with: kitty --session ${(q)session_file}"
}
