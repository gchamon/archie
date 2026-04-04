# `dev-env`

This epic covers building a repeatable Archie development VM workflow around an
Incus-managed Arch guest. It starts with cloud-init bootstrap to a
graphical-ready baseline, then layers Archie deployment automation and only
later standardizes runtime operations and smoke tests where they prove useful.

This initiative was previously named `reproducible-environment`. The shorter
`dev-env` name is now the canonical term across docs, scripts, and planning
artifacts.

## Work items

- [dev-env-01-bootstrap](../work-items/dev-env-01-bootstrap.md)
- [dev-env-02-archie-deploy-automation](../work-items/dev-env-02-archie-deploy-automation.md)
- [dev-env-03-runtime-and-smoke-tests](../work-items/dev-env-03-runtime-and-smoke-tests.md)
