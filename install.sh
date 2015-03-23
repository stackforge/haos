mkdir -p /opt/rally/plugins/
cp rally-scenarios/* /opt/rally/plugins/
cp rally-contexts/* /opt/rally/plugins/
export PYTHONPATH=PYTHONPATH;/opt/rally/plugins/