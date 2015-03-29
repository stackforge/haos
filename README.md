High Availability OpenStack (HAOS)
==================

## Introduction
HAOS is a suite of HA/destructive tests for OpenStack clouds. These tests
are written like Rally plugins which can be executed with Rally and in
parallel with the load/performance tests to simulate some disaster/failover
scenarios with the OpenStack clouds.

## How To Run Tests
These tests require to manually configure OpenStack environment before the
tests, because we need to install shaker agents on all OpenStack nodes.
The tests also require to install Rally and add all Rally plugins from this
repository to Rally plugins folder.

1. Run dummy_shaker_agent.py on all controller nodes in daemon mode
(on MOS environments you can use script install_dummy_shaker_agent.sh
from master node).
2. Install HAOS:

  ./install.sh

3. Export PYTHONPATH:

  export PYTHONPATH=/opt/rally/plugins/

4. Configure scenario file (in folder samples/tasks/scenarios), set parameters
for all controller nodes and power control node, where we can manage the power
state of virtual/baremetal servers (or public IP addresses).
5. Create shaker image in OpenStack cloud:

  git clone https://github.com/stackforge/shaker
  cd shaker
  sudo python setup.py install
  shaker-image-builder --os-auth-url 'http://172.16.0.2:5000/v2.0/' --os-password 'admin' --os-username 'admin' --os-tenant 'admin' --external-net net04_ext

6. Run Rally task with the required HA/disaster test scenario multiple times
and verify that it will pass:

  rally task start samples/tasks/scenarios/SampleScenario.json
