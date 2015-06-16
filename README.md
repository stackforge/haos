High Availability OpenStack (HAOS)
==================================

Introduction
------------

HAOS is a suite of HA/destructive tests for OpenStack clouds. These tests
are written as Rally plugins and are executed by Rally and in
parallel with the load/performance tests to simulate some disaster/failover
scenarios with the OpenStack clouds. HAOS uses HAOS agent for remote execution
of commands on OpenStack nodes and virtual machines in the cloud.


How to install
--------------

1. Clone the repository:
``git clone git://git.openstack.org/stackforge/haos``
2. Make sure that ``sshpass`` is installed - for example, on Ubuntu execute the following command: ``sudo apt-get install sshpass``
3. Edit etc/openrc.local file, set IP addresses, credentials and parameters for your cloud
4. Import ``openrc`` into your environment by doing
``source etc/openrc.local``
5. Run tox:
``tox -e run``

How to run tests
----------------

Run scenario with the command:
``tox -e run <scenario>``

How to run tests on MOS environments
------------------------------------

Run scenario with the command:
``tox -e run-for-mos <scenario>``