openstack-ha-tests
==================

## Introduction
HAOS is a suite of HA/destructive tests for OpenStack clouds. These tests are written
like Rally plugins which can be executed with Rally and in parallel with the
load/performance tests to simulate some disaster/failover scenarios with the OpenStack clouds.

## How To Run Tests
These tests require to manually configure OpenStack environment before the tests, because we need
to install shaker agents on all OpenStack nodes. The tests also require to install Rally and add
all Rally plugins from this repository to Rally plugins folder.

1. Run dummy_shaker_agent.py on all controller nodes in daemon mode - just follow the instructions which are available in dummy_shaker_agent.py (this is temporary solution while we have no the proper shaker support for our cases)
2. Install HAOS: bash ./install.sh
3. Configure scenario file (in folder samples/tasks/scenarios), set parameters for all controller nodes and power control node, where we can manage the power state of virtual/baremetal servers (or public IP addresses).
4. Run Rally task with the required HA/disaster test scenario multiple times and verify that it will pass.