# How To Install And Run:
# 1. apt-get install -qy python-setuptools
# 2. easy_install pip
# 3. pip install flask
# 4. iptables -F & service iptables save
# 5. python dummy_shaker_agent.py &
# 6. Add to crontab on all OpenStack nodes:
#    @reboot python /root/dummy_shaker_agent.py &

import traceback
import subprocess
from flask import Flask, request


app = Flask(__name__)


@app.route('/run_command', methods=['POST'])
def run_command():

    try:
        json_data = request.json
    except Exception:
        return "problems while get request data: {0}".format(
            traceback.print_exc()), 400

    process = subprocess.Popen(json_data["command"].split(),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    process.wait()
    returncode = process.returncode
    output = process.communicate()
    if returncode == 0:
        return output[0]
    else:
        return output[1], 400


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10707, debug=True)
