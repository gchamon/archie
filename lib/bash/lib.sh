#!/bin/bash
set -euo pipefail

LIB_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$LIB_DIR/../.." && pwd)"

matches_env_pattern() {
    local var_name="$1"
    shift
    local pattern=""

    for pattern in "$@"; do
        if [[ "$var_name" == $pattern ]]; then
            return 0
        fi
    done

    return 1
}

load_repo_env_file() {
    local env_file="${1:-$REPO_ROOT/.env.sh}"
    shift || true
    local -a patterns=("$@")
    local var_name=""
    local saved_name=""
    local -a preexisting_vars=()

    if [[ "${#patterns[@]}" -eq 0 ]]; then
        patterns=("ARCHIE_*")
    fi

    if [[ ! -f "$env_file" ]]; then
        return 0
    fi

    while IFS= read -r var_name; do
        if ! matches_env_pattern "$var_name" "${patterns[@]}"; then
            continue
        fi

        preexisting_vars+=("$var_name")
        saved_name="ARCHIE_SAVED_${var_name}"
        printf -v "$saved_name" '%s' "${!var_name}"
    done < <(compgen -A variable)

    # shellcheck source=/dev/null
    source "$env_file"

    for var_name in "${preexisting_vars[@]}"; do
        saved_name="ARCHIE_SAVED_${var_name}"
        printf -v "$var_name" '%s' "${!saved_name}"
        export "$var_name"
        unset "$saved_name"
    done

    log_info "Loaded overrides from $env_file"
}

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

apply_install_env_defaults() {
    ARCHIE_CHECKOUT_DIR_NAME="${ARCHIE_CHECKOUT_DIR_NAME:-$HOME/archie}"
    ARCHIE_ENABLE_SDDM_THEME="${ARCHIE_ENABLE_SDDM_THEME:-1}"
    ARCHIE_ENABLE_LID_CLOSE="${ARCHIE_ENABLE_LID_CLOSE:-1}"
    ARCHIE_ENABLE_POWER_BUTTON_CONFIRM="${ARCHIE_ENABLE_POWER_BUTTON_CONFIRM:-1}"
    ARCHIE_ENABLE_NVIDIA="${ARCHIE_ENABLE_NVIDIA:-0}"
    ARCHIE_ENABLE_XKB_CUSTOMIZATIONS="${ARCHIE_ENABLE_XKB_CUSTOMIZATIONS:-0}"
    DEFAULT_P10K_PACKAGE="${ARCHIE_P10K_PACKAGE:-p10k-lean}"
    GTK_THEME="${ARCHIE_GTK_THEME:-Adwaita-dark}"
    USER_STOW_BACKUP_ROOT="${ARCHIE_USER_STOW_BACKUP_ROOT:-$HOME/archie-pre-stow-backup}"
    SYSTEM_STOW_BACKUP_ROOT="${ARCHIE_SYSTEM_STOW_BACKUP_ROOT:-/root/archie-pre-stow-backup}"
}

manifest_packages() {
    local key="$1"

    jq -r --arg key "$key" '.[$key][]' "$REPO_ROOT/archinstall/package-manifest.json"
}

manifest_optional_packages() {
    local feature="$1"

    jq -r --arg feature "$feature" \
        '.optional_features[$feature] // [] | .[]' \
        "$REPO_ROOT/archinstall/package-manifest.json"
}

stow_package() {
    local target="$1"
    local package_name="$2"

    run_cmd stow --dir="$REPO_ROOT/deployment-packages" --target="$target" "$package_name"
}

stow_package_sudo() {
    local target="$1"
    local package_name="$2"

    run_sudo_cmd stow --dir="$REPO_ROOT/deployment-packages" --target="$target" "$package_name"
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

deploy_system_file() {
    local relative_path="$1"
    local source_path="$REPO_ROOT/copy-deployed-files/$relative_path"
    local deployed_path="/$relative_path"

    run_sudo_cmd mkdir -p "$(dirname "$deployed_path")"
    run_sudo_cmd rm -f "$deployed_path"
    run_sudo_cmd install -m 0644 "$source_path" "$deployed_path"
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

copy_deployed_template_to_target() {
    local deployed_template="$1"
    local target_path="$2"
    local template_path=""

    template_path="$(readlink -f "$deployed_template")"

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

    DEVICE_LUA_PATH="$(copy_deployed_template_to_target "$HOME/.config/hypr/config/device.dist.lua" "$HOME/.config/hypr/config/device.lua")"
    HYPRPAPER_CONF_PATH="$(copy_from_deployed_template "$HOME/.config/hypr/hyprpaper.dist.conf" ".dist.conf" ".conf")"
    OVERRIDES_SH_PATH="$(copy_from_deployed_template "$HOME/.local/lib/zsh/overrides.dist.sh" ".dist.sh" ".sh")"

    log_info "device.lua: $DEVICE_LUA_PATH"
    log_info "hyprpaper.conf: $HYPRPAPER_CONF_PATH"
    log_info "overrides.sh: $OVERRIDES_SH_PATH"
}

ensure_required_home_folders() {
    log_step "Create required home folders"
    run_cmd mkdir -p "$HOME/Pictures/Screenshots"
}

handle_help_and_args() {
    local usage_fn="$1"
    shift
    local expected_arg_count="${1:-0}"
    shift || true

    if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
        "$usage_fn"
        exit 0
    fi

    if [[ $# -gt "$expected_arg_count" ]]; then
        log_error "Expected at most $expected_arg_count argument(s), got $#"
        "$usage_fn" >&2
        exit 1
    fi
}

handle_help_and_no_args() {
    handle_help_and_args "$1" 0 "${@:2}"
}

log_step() {
    printf '\n==> %s\n' "$1"
}

log_info() {
    printf '  -> %s\n' "$1"
}

log_warn() {
    printf '  !! %s\n' "$1" >&2
}

log_error() {
    printf '  xx %s\n' "$1" >&2
}

print_command() {
    printf '+'
    for arg in "$@"; do
        printf ' %q' "$arg"
    done
    printf '\n'
}

run_cmd() {
    print_command "$@"
    "$@"
}

run_sudo_cmd() {
    if (( EUID == 0 )); then
        run_cmd "$@"
        return
    fi

    print_command sudo "$@"
    sudo "$@"
}

require_command() {
    local command_name="$1"

    if ! command -v "$command_name" >/dev/null 2>&1; then
        log_error "Missing required command: $command_name"
        exit 1
    fi
}
