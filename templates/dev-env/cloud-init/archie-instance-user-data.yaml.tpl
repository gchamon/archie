#cloud-config

packages:
  - wl-clipboard

write_files:
  - path: /home/${ARCHIE_INSTANCE_USERNAME}/pull-archie-repo.sh
    owner: ${ARCHIE_INSTANCE_USERNAME}:${ARCHIE_INSTANCE_USERNAME}
    permissions: "0755"
    content: |
      #!/bin/bash
      set -euo pipefail

      if [[ -d "/home/${ARCHIE_INSTANCE_USERNAME}/archie/.git" ]]; then
          git -C "/home/${ARCHIE_INSTANCE_USERNAME}/archie" pull --ff-only
      else
          git clone "${ARCHIE_INSTANCE_REPO_URL}" "/home/${ARCHIE_INSTANCE_USERNAME}/archie"
      fi

final_message: "Archie instance cloud-init finished for ${ARCHIE_INSTANCE_NAME}"
