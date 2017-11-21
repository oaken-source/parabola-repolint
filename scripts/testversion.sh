#!/bin/bash

python - << EOF
import arthur.versions
from arthur.parabola import VersionMaster
package = lambda _: '/'
package.pkgname = "$1"
print(VersionMaster.get_latest_version(package))
EOF
