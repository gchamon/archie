# Keyboard Customizations

Keyboard customizations serve to facilitate typing in a language different from
that the keyboard in use is designed to.

## Deployment

Keyboard customizations are deployed from the repo root with the `etc` and
`xkb` Stow packages:

```bash
sudo stow --dir deployment-packages --target /etc etc
sudo stow --dir deployment-packages --target /usr/share/xkeyboard-config-2 xkb
```

The `etc` package deploys `/etc/xkb-customizations/us-br/...` and the pacman
hook at `/etc/pacman.d/hooks/00-xkb.hook`. The `xkb` package deploys the active
override into `/usr/share/xkeyboard-config-2/symbols/us`.

## US - BR

This layout makes it easier to type Brazilian Portuguese with a US
international keyboard. Target layout: `us-intl`

Customizations:

| Keystrokes | Output |
|------------|--------|
| AltGR + A  | Ã      |
| AltGR + C  | Ç      |
| AltGR + O  | Õ      |
