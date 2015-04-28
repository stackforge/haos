High Availability OpenStack (HAOS)
==================================

Introduction
------------

HAOS is a suite of HA/destructive tests for OpenStack clouds. These tests
are written as Rally plugins and are executed by Rally and in
parallel with the load/performance tests to simulate some disaster/failover
scenarios with the OpenStack clouds. HAOS uses Shaker for remote execution
of commands on OpenStack nodes and for data-plane performance load.


How to install
--------------

1. git clone git://git.openstack.org/stackforge/haos


How to run tests
----------------

1. Fill in your ``openrc`` file based on the sample provided in etc/openrc

2. Import ``openrc`` into your environment by doing

    . etc/openrc.local

3. Run scenario with the command:

    tox -erun <scenario>
