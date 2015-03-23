mkdir -p /opt/rally/plugins
cp rally-scenarios/* /opt/rally/plugins/
cp rally-contexts/* /opt/rally/plugins/
export PYTHONPATH=/opt/rally/plugins/
