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

1. Clone the repository:
```bash
git clone git://git.openstack.org/stackforge/haos```

2. Make sure that ``sshpass`` is installed - on Ubuntu do ``sudo apt-get install sshpass``

3. Fill in your ``openrc`` file based on the sample provided in ``etc/openrc``

4. Import ``openrc`` into your environment by doing
```bash
. etc/openrc.local```

5. Run tox:
```bash
tox -erun```


How to run tests
----------------

Run scenario with the command:
```bash
tox -erun <scenario>```
