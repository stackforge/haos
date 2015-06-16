import paramiko

from rally.common import log as logging


LOG = logging.getLogger(__name__)


def run(host, username, password, command, timeout):
    msg = 'Running command "{0}" on server {1}'
    LOG.info(msg.format(command, host))

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=username, password=password)
    _, ssh_stdout, ssh_stderr = ssh.exec_command(command, timeout=timeout)

    while not ssh_stdout.channel.exit_status_ready():
        "Wait while all commands will be finished successfully."
        pass

    return ssh_stdout, ssh_stderr


class SSHConnection(object):

    def remote_control(self, host, command, timeout=30):
        return run(host["public_ip"], host["user"], host["password"], command,
                   timeout)
