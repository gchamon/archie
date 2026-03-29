#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/bash/lib.sh
source "$SCRIPT_DIR/../lib/bash/lib.sh"
CANONICAL_REPO_URL="https://gitlab.com/gabriel.chamon/archie.git"
RAW_SCRIPT_URL="https://gitlab.com/gabriel.chamon/archie/-/raw/main/scripts/install.sh"

ESSENTIAL_PACKAGES=(
    acpi
    bc
    bind
    blueman
    brightnessctl
    calibre
    cliphist
    dunst
    fd
    frece
    fzf
    gnome-system-monitor
    grimblast-git
    htop
    hyprcursor
    hyprlock
    hyprpaper
    inotify-tools
    jq
    kdeconnect
    ksnip
    less
    lsd
    man-db
    ncdu
    noto-fonts
    noto-fonts-emoji
    otf-font-awesome
    pamixer
    pavucontrol
    polkit-kde-agent
    plocate
    ranger
    ripgrep
    rofi-wayland
    rsync
    stow
    unzip
    waybar
    wl-clip-persist
    xorg-xhost
    zen-browser-bin
    zip
    zsh-fast-syntax-highlighting
)

ZSH_PACKAGES=(
    zsh
    zsh-completions
    oh-my-zsh-git
    zsh-theme-powerlevel10k
    ttf-meslo-nerd
)

THEME_PACKAGES=(
    archlinux-wallpaper
    gnome-themes-extra
    qt5ct
    qt5-graphicaleffects
    qt6ct
    xcursor-breeze5
    xdg-desktop-portal-gnome
    xdg-desktop-portal-gtk
    nwg-look
)

KEYRING_PACKAGES=(
    gnome-keyring
    seahorse
)

DEFAULT_P10K_PACKAGE="p10k-lean"
GTK_THEME="Adwaita-dark"
USER_STOW_BACKUP_ROOT="$HOME/archie-pre-stow-backup"
SYSTEM_STOW_BACKUP_ROOT="/root/archie-pre-stow-backup"

BACKED_UP_USER_PATHS=0
BACKED_UP_SYSTEM_PATHS=0

quickstart_bool_enabled() {
    case "${1,,}" in
        1|true|yes|on)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

is_interactive() {
    [[ -t 0 && -t 1 ]]
}

apply_quickstart_env_defaults() {
    ARCHIE_CHECKOUT_DIR_NAME="${ARCHIE_CHECKOUT_DIR_NAME:-$HOME/archie}"
    ARCHIE_ENABLE_SDDM_THEME="${ARCHIE_ENABLE_SDDM_THEME:-1}"
    ARCHIE_ENABLE_LID_CLOSE="${ARCHIE_ENABLE_LID_CLOSE:-1}"
    ARCHIE_ENABLE_NVIDIA="${ARCHIE_ENABLE_NVIDIA:-0}"
    ARCHIE_ENABLE_XKB_CUSTOMIZATIONS="${ARCHIE_ENABLE_XKB_CUSTOMIZATIONS:-0}"
    DEFAULT_P10K_PACKAGE="${ARCHIE_P10K_PACKAGE:-p10k-lean}"
    GTK_THEME="${ARCHIE_GTK_THEME:-Adwaita-dark}"
    USER_STOW_BACKUP_ROOT="${ARCHIE_USER_STOW_BACKUP_ROOT:-$HOME/archie-pre-stow-backup}"
    SYSTEM_STOW_BACKUP_ROOT="${ARCHIE_SYSTEM_STOW_BACKUP_ROOT:-/root/archie-pre-stow-backup}"
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
    run_pacman_install git base-devel
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
        run_cmd makepkg -si --noconfirm
    )

    run_cmd rm -rf "$yay_build_dir"
    run_yay_install yay-bin
    run_cmd yay -Scc --noconfirm
}

install_yay_packages() {
    log_step "Install Archie packages with yay"
    run_yay_install "${ESSENTIAL_PACKAGES[@]}"
}

install_zsh_packages() {
    log_step "Install zsh packages"
    run_yay_install "${ZSH_PACKAGES[@]}"
}

install_theme_packages() {
    log_step "Install theme packages"
    run_yay_install "${THEME_PACKAGES[@]}"
}

install_sddm_theme_package() {
    if ! quickstart_bool_enabled "$ARCHIE_ENABLE_SDDM_THEME"; then
        log_info "Skipping SDDM theme package install; set ARCHIE_ENABLE_SDDM_THEME=1 to enable it again"
        return
    fi

    log_step "Install SDDM theme package"
    run_yay_install sddm-slice-qt6-git
}

install_keyring_packages() {
    log_step "Install keyring packages"
    run_yay_install "${KEYRING_PACKAGES[@]}"
}

stow_package() {
    local target="$1"
    local package_name="$2"

    run_cmd stow --dir deployment-packages --target "$target" "$package_name"
}

stow_package_sudo() {
    local target="$1"
    local package_name="$2"

    run_sudo_cmd stow --dir deployment-packages --target "$target" "$package_name"
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
        backup_stow_conflicts_sudo lid-close /etc "$SYSTEM_STOW_BACKUP_ROOT"
    else
        log_info "Skipping lid-close backup; set ARCHIE_ENABLE_LID_CLOSE=1 to enable it again"
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

    log_info "Moved $BACKED_UP_USER_PATHS user path(s) and $BACKED_UP_SYSTEM_PATHS system path(s) aside before stow"
}

deploy_p10k_default() {
    local p10k_path="$HOME/.p10k.zsh"
    local desired_target="$REPO_ROOT/deployment-packages/$DEFAULT_P10K_PACKAGE/.p10k.zsh"

    log_step "Deploy default Powerlevel10k theme"

    if [[ -L "$p10k_path" ]] && [[ "$(readlink -f "$p10k_path")" == "$desired_target" ]]; then
        log_info "$DEFAULT_P10K_PACKAGE is already active"
        return
    fi

    if [[ -e "$p10k_path" || -L "$p10k_path" ]]; then
        log_warn "$p10k_path already exists and is not managed by $DEFAULT_P10K_PACKAGE"
        log_warn "Leaving the existing file in place. Switch themes manually if needed."
        return
    fi

    stow_package "$HOME" "$DEFAULT_P10K_PACKAGE"
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

    if quickstart_bool_enabled "$ARCHIE_ENABLE_LID_CLOSE"; then
        stow_package_sudo /etc lid-close
    else
        log_info "Skipping lid-close deployment; set ARCHIE_ENABLE_LID_CLOSE=1 to enable it again"
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

copy_from_deployed_template() {
    local deployed_template="$1"
    local dist_suffix="$2"
    local replacement_suffix="$3"
    local template_path=""
    local target_path=""

    template_path="$(readlink -f "$deployed_template")"
    target_path="${template_path%$dist_suffix}$replacement_suffix"

    if [[ -e "$target_path" || -L "$target_path" ]]; then
        printf '  -> Keeping existing local file: %s\n' "$target_path" >&2
        printf '%s\n' "$target_path"
        return 0
    fi

    print_command cp "$template_path" "$target_path" >&2
    cp "$template_path" "$target_path"
    printf '%s\n' "$target_path"
}

scaffold_local_files() {
    log_step "Scaffold machine-local files from deployed templates"

    DEVICE_CONF_PATH="$(copy_from_deployed_template "$HOME/.config/hypr/config/device.dist.conf" ".dist.conf" ".conf")"
    HYPRPAPER_CONF_PATH="$(copy_from_deployed_template "$HOME/.config/hypr/hyprpaper.dist.conf" ".dist.conf" ".conf")"
    OVERRIDES_SH_PATH="$(copy_from_deployed_template "$HOME/.local/lib/zsh/overrides.dist.sh" ".dist.sh" ".sh")"

    log_info "device.conf: $DEVICE_CONF_PATH"
    log_info "hyprpaper.conf: $HYPRPAPER_CONF_PATH"
    log_info "overrides.sh: $OVERRIDES_SH_PATH"
}

ensure_required_home_folders() {
    log_step "Create required home folders"
    run_cmd mkdir -p "$HOME/Pictures/Screenshots"
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

print_manual_follow_up() {
    log_step "Manual follow-up still required"
    log_info "Review $DEVICE_CONF_PATH for monitor geometry and AQ_DRM_DEVICES."
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
    apply_quickstart_env_defaults
    install_base_packages
    bootstrap_checkout_if_needed
    bootstrap_yay
    install_yay_packages
    install_zsh_packages
    install_theme_packages
    install_sddm_theme_package
    install_keyring_packages
    backup_existing_stow_targets
    deploy_stow_packages
    scaffold_local_files
    ensure_required_home_folders
    set_login_shell
    apply_gtk_theme
    print_manual_follow_up
}

main "$@"
