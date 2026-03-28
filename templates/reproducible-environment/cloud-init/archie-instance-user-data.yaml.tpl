#cloud-config

write_files:
  - path: /home/${ARCHIE_VM_USERNAME}/pull-archie-repo.sh
    owner: ${ARCHIE_VM_USERNAME}:${ARCHIE_VM_USERNAME}
    permissions: "0755"
    content: |
      #!/bin/bash
      set -euo pipefail

      if [[ -d "/home/${ARCHIE_VM_USERNAME}/archie/.git" ]]; then
          git -C "/home/${ARCHIE_VM_USERNAME}/archie" pull --ff-only
      else
          git clone "${ARCHIE_REPO_URL}" "/home/${ARCHIE_VM_USERNAME}/archie"
      fi

final_message: "Archie instance cloud-init finished for ${ARCHIE_IMAGE_INSTANCE_NAME}"
