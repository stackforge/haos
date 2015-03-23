# How To Install And Run:
# 1. apt-get install -qy python-setuptools
# 2. easy_install pip
# 3. pip install flask
# 4. python dummy_shaker_agent.py &
# 5. Add to crontab on all OpenStack nodes: @reboot python /root/dummy_shaker_agent.py &

import subprocess
from flask import Flask, request


app = Flask(__name__)


@app.route('/run_command', methods=['POST'])
def run_command():
    r = request.get_json(force=True)
    process = subprocess.Popen(r["command"].split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]

    return output


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=1000, debug=True)
