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
    app.run(host="0.0.0.0", debug=True)
