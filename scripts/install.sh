#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/bash/lib.sh
source "$SCRIPT_DIR/../lib/bash/lib.sh"
CANONICAL_REPO_URL="https://gitlab.com/gabriel.chamon/archie.git"
RAW_SCRIPT_URL="https://gitlab.com/gabriel.chamon/archie/-/raw/main/scripts/install.sh"

BACKED_UP_USER_PATHS=0
BACKED_UP_SYSTEM_PATHS=0

is_interactive() {
    [[ -t 0 && -t 1 ]]
}

run_pacman_install() {
    run_sudo_cmd pacman -S --needed --noconfirm "$@"
}

run_yay_install() {
    run_cmd yay -S --needed --noconfirm --removemake \
        --answerclean N \
        --answerdiff N \
        --answeredit N \
        "$@"
}

confirm() {
    local prompt="$1"
    local answer=""

    if ! is_interactive; then
        return 1
    fi

    while true; do
        if [[ "${2:-n}" == "y" ]]; then
            read -r -p "$prompt [Y/n] " answer || return 1
            answer="${answer:-Y}"
        else
            read -r -p "$prompt [y/N] " answer || return 1
            answer="${answer:-N}"
        fi

        case "${answer,,}" in
            y|yes)
                return 0
                ;;
            n|no)
                return 1
                ;;
        esac
    done
}

choose_from_list() {
    local prompt="$1"
    shift
    local options=("$@")
    local choice=""
    local index=1

    if [[ "${#options[@]}" -eq 0 ]]; then
        return 1
    fi

    if ! is_interactive; then
        return 1
    fi

    printf '%s\n' "$prompt"
    for option in "${options[@]}"; do
        printf '  %d. %s\n' "$index" "$option"
        ((index++))
    done

    while true; do
        read -r -p "Choose 1-${#options[@]}: " choice || return 1
        if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#options[@]} )); then
            printf '%s\n' "${options[choice-1]}"
            return 0
        fi
    done
}

bootstrap_checkout_if_needed() {
    local checkout_dir=""

    if [[ -d "$REPO_ROOT/deployment-packages" ]]; then
        cd "$REPO_ROOT"
        return
    fi

    log_step "Bootstrap Archie checkout"
    checkout_dir="$ARCHIE_CHECKOUT_DIR_NAME"

    if [[ -e "$checkout_dir" ]]; then
        log_warn "Expected to clone Archie into $checkout_dir, but that path already exists."
        log_warn "Either remove it, rename it, or run this script from inside the existing Archie checkout."
        exit 1
    fi

    run_cmd git clone "$CANONICAL_REPO_URL" "$checkout_dir"
    cd "$checkout_dir"
    REPO_ROOT="$checkout_dir"
}

install_base_packages() {
    log_step "Install base packages"
    run_pacman_install git base-devel jq
}

package_is_installed() {
    pacman -Q "$1" >/dev/null 2>&1
}

bootstrap_yay() {
    local yay_build_dir=""

    log_step "Bootstrap yay"

    if package_is_installed yay-bin; then
        log_info "yay-bin is already installed"
        return
    fi

    if package_is_installed yay; then
        log_info "yay is installed but yay-bin is missing; normalizing to yay-bin"
        run_yay_install yay-bin
        run_cmd yay -Scc --noconfirm
        return
    fi

    yay_build_dir="$(mktemp -d)"
    run_cmd git clone https://aur.archlinux.org/yay-bin.git "$yay_build_dir/yay-bin"

    (
        cd "$yay_build_dir/yay-bin"
        run_cmd  makepkg -Cfsi --noconfirm
    )

    run_cmd rm -rf "$yay_build_dir"
    run_yay_install yay-bin
    run_cmd yay -Scc --noconfirm
}

install_yay_packages() {
    local -a official_packages=()
    local -a aur_packages=()

    log_step "Install Archie packages from the shared manifest"
    mapfile -t official_packages < <(manifest_packages official_runtime)
    mapfile -t aur_packages < <(manifest_packages aur_runtime)
    run_pacman_install "${official_packages[@]}"
    run_yay_install "${aur_packages[@]}"
}

install_zsh_packages() {
    log_info "Zsh packages are included in the shared manifest"
}

install_theme_packages() {
    log_info "Theme packages are included in the shared manifest"
}

install_sddm_theme_package() {
    local -a theme_packages=()

    if ! quickstart_bool_enabled "$ARCHIE_ENABLE_SDDM_THEME"; then
        log_info "Skipping SDDM theme package install; set ARCHIE_ENABLE_SDDM_THEME=1 to enable it again"
        return
    fi

    log_step "Install SDDM theme package"
    mapfile -t theme_packages < <(manifest_optional_packages sddm_theme)
    ((${#theme_packages[@]} > 0)) || {
        log_info "No SDDM theme packages are declared in the manifest"
        return
    }
    run_yay_install "${theme_packages[@]}"
}

install_keyring_packages() {
    log_info "Keyring packages are included in the shared manifest"
}

find_conflicting_deployed_path() {
    local deploy_root="$1"
    local deployed_path="$2"
    local current_path=""

    if [[ -L "$deployed_path" ]]; then
        printf '%s\n' "$deployed_path"
        return 0
    fi

    current_path="$(dirname "$deployed_path")"
    while [[ "$current_path" != "$deploy_root" ]]; do
        if [[ -L "$current_path" ]]; then
            printf '%s\n' "$current_path"
            return 0
        fi

        current_path="$(dirname "$current_path")"
    done

    if [[ -e "$deployed_path" ]]; then
        printf '%s\n' "$deployed_path"
        return 0
    fi

    return 1
}

is_managed_deployed_path() {
    local deploy_root="$1"
    local package_dir="$2"
    local conflicting_path="$3"
    local relative_path=""
    local managed_target=""

    [[ -L "$conflicting_path" ]] || return 1
    relative_path="${conflicting_path#"$deploy_root"/}"
    managed_target="$package_dir/$relative_path"

    [[ -e "$managed_target" || -L "$managed_target" ]] || return 1
    [[ "$(readlink -f "$conflicting_path")" == "$(readlink -f "$managed_target")" ]]
}

backup_stow_conflicts() {
    local package_name="$1"
    local deploy_root="$2"
    local backup_root="$3"
    local package_dir="$REPO_ROOT/deployment-packages/$package_name"
    local package_path=""
    local relative_path=""
    local deployed_path=""
    local conflicting_path=""
    local backup_path=""
    declare -A handled_conflicts=()

    while IFS= read -r -d '' package_path; do
        relative_path="${package_path#"$package_dir"/}"
        deployed_path="$deploy_root/$relative_path"

        if ! conflicting_path="$(find_conflicting_deployed_path "$deploy_root" "$deployed_path")"; then
            continue
        fi

        if [[ -n "${handled_conflicts[$conflicting_path]:-}" ]]; then
            continue
        fi

        handled_conflicts["$conflicting_path"]=1

        if is_managed_deployed_path "$deploy_root" "$package_dir" "$conflicting_path"; then
            continue
        fi

        backup_path="$backup_root/${conflicting_path#"$deploy_root"/}"
        run_cmd mkdir -p "$(dirname "$backup_path")"
        run_cmd mv "$conflicting_path" "$backup_path"
        ((BACKED_UP_USER_PATHS += 1))
    done < <(find "$package_dir" -type f -print0)
}

backup_stow_conflicts_sudo() {
    local package_name="$1"
    local deploy_root="$2"
    local backup_root="$3"
    local package_dir="$REPO_ROOT/deployment-packages/$package_name"
    local package_path=""
    local relative_path=""
    local deployed_path=""
    local conflicting_path=""
    local backup_path=""
    declare -A handled_conflicts=()

    while IFS= read -r -d '' package_path; do
        relative_path="${package_path#"$package_dir"/}"
        deployed_path="$deploy_root/$relative_path"

        if ! conflicting_path="$(find_conflicting_deployed_path "$deploy_root" "$deployed_path")"; then
            continue
        fi

        if [[ -n "${handled_conflicts[$conflicting_path]:-}" ]]; then
            continue
        fi

        handled_conflicts["$conflicting_path"]=1

        if is_managed_deployed_path "$deploy_root" "$package_dir" "$conflicting_path"; then
            continue
        fi

        backup_path="$backup_root/${conflicting_path#"$deploy_root"/}"
        run_sudo_cmd mkdir -p "$(dirname "$backup_path")"
        run_sudo_cmd mv "$conflicting_path" "$backup_path"
        ((BACKED_UP_SYSTEM_PATHS += 1))
    done < <(find "$package_dir" -type f -print0)
}

backup_copy_deployed_target_sudo() {
    local source_path="$1"
    local deployed_path="$2"
    local backup_root="$3"
    local backup_relative_path="${deployed_path#/}"
    local backup_path=""

    if [[ ! -e "$deployed_path" && ! -L "$deployed_path" ]]; then
        return
    fi

    if cmp -s "$source_path" "$deployed_path"; then
        return
    fi

    if [[ "$deployed_path" == /etc/* ]]; then
        backup_relative_path="${deployed_path#/etc/}"
    fi

    backup_path="$backup_root/$backup_relative_path"
    run_sudo_cmd mkdir -p "$(dirname "$backup_path")"
    run_sudo_cmd mv "$deployed_path" "$backup_path"
    ((BACKED_UP_SYSTEM_PATHS += 1))
}

backup_copy_deployed_file_sudo() {
    local relative_path="$1"
    local source_path="$REPO_ROOT/copy-deployed-files/$relative_path"
    local deployed_path="/$relative_path"

    backup_copy_deployed_target_sudo "$source_path" "$deployed_path" "$SYSTEM_STOW_BACKUP_ROOT"
}

backup_copy_deployed_target() {
    local source_path="$1"
    local deployed_path="$2"
    local backup_root="$3"
    local backup_path="$backup_root/${deployed_path#"$HOME"/}"

    if [[ ! -e "$deployed_path" && ! -L "$deployed_path" ]]; then
        return
    fi

    if cmp -s "$source_path" "$deployed_path"; then
        return
    fi

    run_cmd mkdir -p "$(dirname "$backup_path")"
    run_cmd mv "$deployed_path" "$backup_path"
    ((BACKED_UP_USER_PATHS += 1))
}

backup_copy_deployed_file() {
    local relative_path="$1"
    local source_path="$REPO_ROOT/copy-deployed-files/$relative_path"
    local home_relative_path="${relative_path#home/}"
    local deployed_path="$HOME/$home_relative_path"

    backup_copy_deployed_target "$source_path" "$deployed_path" "$USER_STOW_BACKUP_ROOT"
}

backup_existing_stow_targets() {
    log_step "Back up conflicting deployment targets"
    log_info "User backup root: $USER_STOW_BACKUP_ROOT"
    log_info "System backup root: $SYSTEM_STOW_BACKUP_ROOT"

    run_cmd mkdir -p "$USER_STOW_BACKUP_ROOT"
    run_sudo_cmd mkdir -p "$SYSTEM_STOW_BACKUP_ROOT"

    backup_stow_conflicts home "$HOME" "$USER_STOW_BACKUP_ROOT"
    backup_stow_conflicts "$DEFAULT_P10K_PACKAGE" "$HOME" "$USER_STOW_BACKUP_ROOT"
    backup_stow_conflicts config "$HOME/.config" "$USER_STOW_BACKUP_ROOT/.config"
    backup_stow_conflicts local "$HOME/.local" "$USER_STOW_BACKUP_ROOT/.local"
    backup_stow_conflicts_sudo etc /etc "$SYSTEM_STOW_BACKUP_ROOT"

    if quickstart_bool_enabled "$ARCHIE_ENABLE_SDDM_THEME"; then
        backup_stow_conflicts_sudo sddm-theme /etc "$SYSTEM_STOW_BACKUP_ROOT"
    else
        log_info "Skipping SDDM theme backup; set ARCHIE_ENABLE_SDDM_THEME=1 to enable it again"
    fi

    if quickstart_bool_enabled "$ARCHIE_ENABLE_LID_CLOSE"; then
        backup_copy_deployed_file_sudo etc/systemd/logind.conf.d/lid-close.conf
    else
        log_info "Skipping lid-close backup; set ARCHIE_ENABLE_LID_CLOSE=1 to enable it again"
    fi

    if quickstart_bool_enabled "$ARCHIE_ENABLE_POWER_BUTTON_CONFIRM"; then
        backup_copy_deployed_file_sudo etc/systemd/logind.conf.d/power-button-confirm.conf
    else
        log_info "Skipping power-button confirmation backup; set ARCHIE_ENABLE_POWER_BUTTON_CONFIRM=1 to enable it again"
    fi

    if quickstart_bool_enabled "$ARCHIE_ENABLE_NVIDIA"; then
        backup_stow_conflicts_sudo nvidia /etc "$SYSTEM_STOW_BACKUP_ROOT"
    else
        log_info "Skipping Nvidia backup; set ARCHIE_ENABLE_NVIDIA=1 to enable Archie Nvidia overrides"
    fi

    if quickstart_bool_enabled "$ARCHIE_ENABLE_XKB_CUSTOMIZATIONS"; then
        backup_stow_conflicts_sudo xkb /usr/share/xkeyboard-config-2 "$SYSTEM_STOW_BACKUP_ROOT/usr-share-xkeyboard-config-2"
    else
        log_info "Skipping XKB backup; set ARCHIE_ENABLE_XKB_CUSTOMIZATIONS=1 to enable Archie keyboard customizations"
    fi

    if (( BACKED_UP_USER_PATHS == 0 && BACKED_UP_SYSTEM_PATHS == 0 )); then
        log_info "No pre-existing deployment targets needed backup"
        return
    fi

    log_info "Moved $BACKED_UP_USER_PATHS user path(s) and $BACKED_UP_SYSTEM_PATHS system path(s) aside before deployment"
}

initialize_archie_store() {
    log_step "Initialize shared Archie store"

    if ! getent group archie >/dev/null; then
        run_sudo_cmd groupadd --system archie
    fi
    run_sudo_cmd usermod --append --groups archie "$USER"
    run_sudo_cmd archie system initialize-store --legacy-home "$HOME"
    log_info "Archie settings are stored in /var/lib/archie/store.sqlite3."
    log_info "Log out and back in, or reboot, before changing policy without sudo."
}

reload_logind_if_active() {
    if ! sudo systemctl is-active --quiet systemd-logind.service; then
        log_info "systemd-logind is not active; skipping logind reload"
        return
    fi

    run_sudo_cmd systemctl kill -s HUP systemd-logind.service
}

deploy_copy_deployed_files() {
    local deployed_logind_file=0

    log_step "Deploy copy-managed files"

    if quickstart_bool_enabled "$ARCHIE_ENABLE_LID_CLOSE"; then
        deploy_system_file etc/systemd/logind.conf.d/lid-close.conf
        deployed_logind_file=1
    else
        log_info "Skipping lid-close deployment; set ARCHIE_ENABLE_LID_CLOSE=1 to enable it again"
    fi

    if quickstart_bool_enabled "$ARCHIE_ENABLE_POWER_BUTTON_CONFIRM"; then
        deploy_system_file etc/systemd/logind.conf.d/power-button-confirm.conf
        deployed_logind_file=1
    else
        log_info "Skipping power-button confirmation deployment; set ARCHIE_ENABLE_POWER_BUTTON_CONFIRM=1 to enable it again"
    fi

    if (( deployed_logind_file == 1 )); then
        reload_logind_if_active
    fi
}

deploy_stow_packages() {
    log_step "Deploy Archie with Stow"
    stow_package "$HOME" home
    stow_package "$HOME/.config" config
    stow_package "$HOME/.local" local
    stow_package_sudo /etc etc

    if quickstart_bool_enabled "$ARCHIE_ENABLE_SDDM_THEME"; then
        stow_package_sudo /etc sddm-theme
    else
        log_info "Skipping SDDM theme deployment; set ARCHIE_ENABLE_SDDM_THEME=1 to enable it again"
    fi

    if quickstart_bool_enabled "$ARCHIE_ENABLE_NVIDIA"; then
        stow_package_sudo /etc nvidia
    else
        log_info "Skipping Nvidia deployment; set ARCHIE_ENABLE_NVIDIA=1 to enable Archie Nvidia overrides"
    fi

    if quickstart_bool_enabled "$ARCHIE_ENABLE_XKB_CUSTOMIZATIONS"; then
        stow_package_sudo /usr/share/xkeyboard-config-2 xkb
    else
        log_info "Skipping XKB deployment; set ARCHIE_ENABLE_XKB_CUSTOMIZATIONS=1 to enable Archie keyboard customizations"
    fi

    deploy_p10k_default
}

set_login_shell() {
    local zsh_path=""

    log_step "Set login shell to zsh"
    zsh_path="$(command -v zsh)"

    if [[ "${SHELL:-}" == "$zsh_path" ]]; then
        log_info "zsh is already the login shell"
        return
    fi

    if confirm "Change the login shell to zsh now?" "y"; then
        run_cmd chsh -s "$zsh_path"
    else
        log_warn "Skipping chsh. Run 'chsh -s $zsh_path' later if needed."
    fi
}

apply_gtk_theme() {
    log_step "Apply GTK theme"

    if command -v gsettings >/dev/null 2>&1; then
        print_command gsettings set org.gnome.desktop.interface gtk-theme "$GTK_THEME"
        if gsettings set org.gnome.desktop.interface gtk-theme "$GTK_THEME"; then
            log_info "Updated gsettings with $GTK_THEME"
        else
            log_warn "gsettings update failed. Verify the theme later with NWG Look."
        fi

        print_command gsettings set org.gnome.desktop.interface color-scheme prefer-dark
        if gsettings set org.gnome.desktop.interface color-scheme prefer-dark; then
            log_info "Updated gsettings color-scheme to prefer-dark"
        else
            log_warn "gsettings dark preference update failed. Verify it later in your desktop settings."
        fi
    else
        log_warn "gsettings is not available. Verify the theme later with NWG Look."
    fi

    log_info "GTK settings files are deployed through the config Stow package."
    log_info "Privileged GTK apps also rely on the matching /etc GTK settings deployed through the etc Stow package."
    log_info "Qt support is configured through qt6ct for current Archie Qt apps, with matching qt5ct defaults also deployed."
    log_info "GNOME/libadwaita apps use the GNOME dark preference together with xdg-desktop-portal-gnome in the running session."
    log_info "If the running session does not pick up the theme, open GTK Settings from rofi and confirm $GTK_THEME."
}

enable_system_services() {
    log_step "Enable system services"
    run_sudo_cmd systemctl enable power-profiles-daemon.service
}

print_manual_follow_up() {
    log_step "Manual follow-up still required"
    log_info "Review $DEVICE_LUA_PATH for monitor geometry and AQ_DRM_DEVICES."
    log_info "Review $HYPRPAPER_CONF_PATH for wallpaper paths and optional external monitor mapping."
    log_info "Review $OVERRIDES_SH_PATH for any machine-specific zsh overrides."
    log_info "Inspect monitors with: hyprctl monitors"
    log_info "Inspect workspaces with: hyprctl workspaces"
    log_info "Inspect brightness devices with: brightnessctl -l"
    log_info "Inspect /sys backlight entries with: ls -1 /sys/class/backlight"
    log_info "Reload Hyprland after editing Hyprland files with: hyprctl reload"
    log_info "See docs/user/GUIDE.md for optional post-install and machine-specific topics."
}

main() {
    load_repo_env_file "$REPO_ROOT/.env.sh" 'ARCHIE_*'
    apply_install_env_defaults
    install_base_packages
    bootstrap_checkout_if_needed
    bootstrap_yay
    if package_is_installed archie-cli-nightly; then
        log_step "Remove Archie CLI nightly package"
        run_sudo_cmd pacman -R --noconfirm archie-cli-nightly
    fi
    run_yay_install archie-cli
    initialize_archie_store
    install_yay_packages
    install_zsh_packages
    install_theme_packages
    install_sddm_theme_package
    install_keyring_packages
    backup_existing_stow_targets
    deploy_stow_packages
    deploy_copy_deployed_files
    scaffold_local_files
    ensure_required_home_folders
    enable_system_services
    set_login_shell
    apply_gtk_theme
    print_manual_follow_up
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
