#!/bin/bash
# This script allows to install and run dummy shaker agent on all controllers

for i in `fuel nodes 2>/dev/null | grep controller | awk '{print $1}'`
do

  scp dummy_shaker_agent.py root@node-$i:~/
  ssh root@node-$i 'route del default gw 172.16.0.1'
  ssh root@node-$i 'route add default gw 10.20.0.2'
  ssh root@node-$i 'easy_install pip'
  ssh root@node-$i 'pip install flask'
  ssh root@node-$i 'iptables -A INPUT -m state --state NEW -p tcp --dport 10707 -j ACCEPT'
  ssh root@node-$i 'iptables-save > /etc/iptables.rules'
  ssh root@node-$i 'python dummy_shaker_agent.py &'
  ssh root@node-$i '(crontab -l ; echo "@reboot python /root/dummy_shaker_agent.py &") | sort - | uniq - | crontab -'

done
