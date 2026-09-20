#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/bash/lib.sh
source "$SCRIPT_DIR/../lib/bash/lib.sh"

usage() {
    cat <<'EOF'
Usage: provision.sh --username USER
EOF
}

die() {
    log_error "$1"
    exit 1
}

parse_args() {
    TARGET_USERNAME=""
    TARGET_HOME=""
    TARGET_UID=""
    TARGET_GID=""

    while (($#)); do
        case "$1" in
            --username)
                TARGET_USERNAME="${2:-}"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                usage >&2
                die "Unknown argument: $1"
                ;;
        esac
    done

    [[ "$TARGET_USERNAME" =~ ^[a-z_][a-z0-9_-]*$ ]] || die "Invalid target username"
    TARGET_HOME="/home/$TARGET_USERNAME"
    if [[ "${ALLOW_NON_ROOT:-0}" != 1 ]]; then
        (( EUID == 0 )) || die "Provisioning must run as root"
    fi
}

run_as_target() {
    runuser -u "$TARGET_USERNAME" -- env HOME="$TARGET_HOME" USER="$TARGET_USERNAME" "$@"
}

prepare_target_identity() {
    TARGET_UID="$(id -u "$TARGET_USERNAME")"
    TARGET_GID="$(id -g "$TARGET_USERNAME")"

    install -d -m 0755 -o "$TARGET_UID" -g "$TARGET_GID" "$TARGET_HOME"
    install -d -m 0755 -o "$TARGET_UID" -g "$TARGET_GID" "$TARGET_HOME/.config"
    install -d -m 0755 -o "$TARGET_UID" -g "$TARGET_GID" "$TARGET_HOME/.local"
    install -d -m 0755 -o "$TARGET_UID" -g "$TARGET_GID" "$TARGET_HOME/.cache"
    install -d -m 0755 -o "$TARGET_UID" -g "$TARGET_GID" "$TARGET_HOME/.cache/archie"
    install -d -m 0755 -o "$TARGET_UID" -g "$TARGET_GID" "$TARGET_HOME/.cache/archie/aur"
}

build_and_install_aur_package() {
    local package_name="$1"
    local build_dir="$TARGET_HOME/.cache/archie/aur/$package_name"
    local source_revision=""
    local artifact=""
    local artifact_path=""
    local build_path=""
    local package_metadata=""
    local -a artifacts=()
    local -a validated_artifacts=()

    log_step "Build AUR package: $package_name"

    if [[ ! -d "$build_dir/.git" ]]; then
        run_as_target git clone --depth=1 \
            "https://aur.archlinux.org/$package_name.git" "$build_dir"
    else
        run_as_target git -C "$build_dir" fetch --depth=1 origin
        run_as_target git -C "$build_dir" reset --hard origin/HEAD
    fi

    source_revision="$(run_as_target git -C "$build_dir" rev-parse HEAD)"
    log_info "$package_name source revision: $source_revision"
    run_as_target makepkg --dir "$build_dir" --nodeps --nocheck --noconfirm --cleanbuild

    mapfile -t artifacts < <(run_as_target makepkg --dir "$build_dir" --packagelist)
    ((${#artifacts[@]} > 0)) || die "AUR package $package_name produced no artifacts"
    build_path="$(realpath -- "$build_dir")"

    for artifact in "${artifacts[@]}"; do
        artifact_path="$(realpath -m -- "$artifact")"
        [[ "$artifact_path" == "$build_path/"* ]] || die "AUR artifact escaped its build directory"
        [[ ! -L "$artifact" ]] || die "Invalid AUR artifact: $artifact"
        if [[ ! -e "$artifact" ]]; then
            if [[ "$(basename -- "$artifact")" == "$package_name-debug-"*.pkg.tar.* ]]; then
                log_warn "Skipping missing debug AUR artifact: $artifact"
                continue
            fi
            die "AUR artifact was not produced: $artifact"
        fi
        [[ -f "$artifact" ]] || die "Invalid AUR artifact: $artifact"
        package_metadata="$(pacman -Qpq -- "$artifact")"
        [[ "$(basename "$artifact")" == "$package_metadata-"*.pkg.tar.* ]] || \
            die "AUR artifact filename mismatch: $artifact"
        if [[ "$package_metadata" == "$package_name-debug" ]]; then
            log_warn "Skipping debug AUR artifact: $package_metadata"
            continue
        fi
        [[ "$package_metadata" == "$package_name" ]] || \
            die "AUR package $package_name produced unexpected package: $package_metadata"
        validated_artifacts+=("$artifact")
    done

    ((${#validated_artifacts[@]} == 1)) || \
        die "Missing primary AUR artifact package: $package_name"

    for artifact in "${validated_artifacts[@]}"; do
        run_sudo_cmd pacman -U --noconfirm "$artifact"
    done
    run_sudo_cmd rm -rf -- "$build_dir"
}

install_aur_packages() {
    local package_name=""
    local -a aur_packages=()
    local -a optional_packages=()

    mapfile -t aur_packages < <(manifest_packages aur_runtime)
    if quickstart_bool_enabled "$ARCHIE_ENABLE_SDDM_THEME"; then
        mapfile -t optional_packages < <(manifest_optional_packages sddm_theme)
        aur_packages+=("${optional_packages[@]}")
    fi
    for package_name in "${aur_packages[@]}"; do
        build_and_install_aur_package "$package_name"
    done
}

deploy_system_packages() {
    log_step "Deploy Archie system files"
    stow_package_sudo /etc etc
    stow_package_sudo /etc sddm-theme
    if quickstart_bool_enabled "$ARCHIE_ENABLE_NVIDIA"; then
        stow_package_sudo /etc nvidia
    fi
    deploy_system_file etc/systemd/logind.conf.d/lid-close.conf
    deploy_system_file etc/systemd/logind.conf.d/power-button-confirm.conf
}

provision_user() {
    log_step "Deploy Archie user files"
    HOME="$TARGET_HOME"
    USER="$TARGET_USERNAME"
    DEFAULT_P10K_PACKAGE="p10k-lean"
    stow_package "$TARGET_HOME" home
    stow_package "$TARGET_HOME/.config" config
    stow_package "$TARGET_HOME/.local" local
    deploy_p10k_default
    scaffold_local_files
    ensure_required_home_folders
}

initialize_store_and_services() {
    log_step "Initialize Archie store and services"
    if ! getent group archie >/dev/null; then
        run_sudo_cmd groupadd --system archie
    fi
    run_sudo_cmd usermod --append --groups archie "$TARGET_USERNAME"
    run_as_target archie system initialize-store --legacy-home "$TARGET_HOME"
    run_sudo_cmd systemctl enable bluetooth.service power-profiles-daemon.service sddm.service
    run_sudo_cmd usermod --shell "$(command -v zsh)" "$TARGET_USERNAME"
}

main() {
    parse_args "$@"
    LOG_PATH="/var/log/archie/provision.log"
    install -d -m 0755 /var/log/archie
    exec > >(tee -a "$LOG_PATH") 2>&1
    apply_install_env_defaults
    ARCHIE_ENABLE_SDDM_THEME=1
    ARCHIE_ENABLE_LID_CLOSE=1
    ARCHIE_ENABLE_POWER_BUTTON_CONFIRM=1
    ARCHIE_ENABLE_XKB_CUSTOMIZATIONS=0
    if pacman -Q nvidia-open-dkms >/dev/null 2>&1 || pacman -Q nvidia-open >/dev/null 2>&1; then
        ARCHIE_ENABLE_NVIDIA=1
    else
        ARCHIE_ENABLE_NVIDIA=0
    fi
    prepare_target_identity
    deploy_system_packages
    install_aur_packages
    initialize_store_and_services
    runuser -u "$TARGET_USERNAME" -- env \
        HOME="$TARGET_HOME" USER="$TARGET_USERNAME" \
        "$SCRIPT_DIR/provision.sh" --user-phase \
        --username "$TARGET_USERNAME"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    if [[ "${1:-}" == "--user-phase" ]]; then
        shift
        ALLOW_NON_ROOT=1
        parse_args "$@"
        HOME="$TARGET_HOME"
        USER="$TARGET_USERNAME"
        DEFAULT_P10K_PACKAGE="p10k-lean"
        provision_user
    else
        main "$@"
    fi
fi
