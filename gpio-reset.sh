#!/usr/bin/env bash

set -euox pipefail

echo "Buttons"
pinctrl -e set 2,4,27 ip pd
echo "Lights"
pinctrl -e set 3,10,17 op pd
echo "Motors"
pinctrl -e set 9,11,22 op pd
