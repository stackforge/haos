#!/bin/bash -xe

tools/verify.sh || exit 1
tools/install_rally.sh || exit 1
tools/install_haos_agents.sh || exit 1
tools/build_image.sh || exit 1