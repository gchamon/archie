# Keyboard Customizations

Keyboard customizations serve to facilitate typing in a language different from
that the keyboard in use is designed to.

## Deployment

Choose a customization which can be listed with `ls xkb-customizations`:

```bash
sudo rsync -va ./xkb-customizations/us-br/ /etc/xkb-customizations
sudo rsync -va ./xkb-customizations/us-br/ /usr/share/xkeyboard-config-2/
```

Deploy the `00-xkb.hook`, which always redeploy the customization whenever
`xkeyboard-config` is updated:

```bash
sudo cp ./xkb-customizations/00-xkb.hook /etc/pacman.d/hooks/00-xkb.hook
```

## US - BR

This layout makes it easier to type Brazilian Portuguese with a US
international keyboard. Target layout: `us-intl`

Customizations:

| Keystrokes | Output |
|------------|--------|
| AltGR + A  | Ã      |
| AltGR + C  | Ç      |
| AltGR + O  | Õ      |
