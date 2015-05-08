# Copyright (c) 2015 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import multiprocessing

import flask
from rally.common import log as logging


LOG = logging.getLogger(__name__)

app = flask.Flask(__name__)


@app.route('/reply/<agent_id>', methods=['POST'])
def reply(agent_id):
    data = flask.request.data
    LOG.debug('Got reply from agent: %s, %s', agent_id, data)

    pipe = app.config['HAOS_PIPE']
    if pipe:
        pipe.send({agent_id: data})
    return ''


@app.route('/poll/<agent_id>')
def poll(agent_id):
    LOG.debug('Poll request from agent: %s', agent_id)

    pipe = app.config['HAOS_PIPE']
    if pipe:
        has_data = pipe.poll()
        tasks = app.config['HAOS_TASKS']

        if has_data:
            tasks.update(pipe.recv())

        if agent_id in tasks:
            command = tasks[agent_id]
            LOG.debug('Scheduling command %s on agent %s', command, agent_id)

            del tasks[agent_id]
            return command

    return ''


def _split_address(address):
    try:
        host, port = address.split(':')
        port = int(port)
        return host, port
    except ValueError:
        raise ValueError('Invalid address: %s, "host:port" expected', address)


def start_server(pipe, server_endpoint):
    app.config['HAOS_PIPE'] = pipe
    app.config['HAOS_TASKS'] = dict()

    host, port = _split_address(server_endpoint)

    LOG.info('Running the server at %s:%d', host, port)
    app.run(host=host, port=port, debug=False)


def run(pipe, agent_id, command, timeout):
    LOG.info('Running command %s on agent %s', command, agent_id)

    pipe.send({agent_id: command})
    has_data = pipe.poll(timeout)
    if has_data:
        data = pipe.recv()[agent_id]
        LOG.debug('Received data %s from agent %s', data, agent_id)
        return data
    else:
        LOG.warn('Timeout while receiving data from agent %s', agent_id)
        return None


class Server(object):
    def __init__(self, server_endpoint):
        LOG.info('Server listens at %s', server_endpoint)

        self.parent_conn, self.child_conn = multiprocessing.Pipe()
        self.child = multiprocessing.Process(
            target=start_server, args=(self.child_conn, server_endpoint))
        self.child.start()

    def __del__(self):
        LOG.info('Server stops')

        self.parent_conn.close()
        self.child.terminate()

    def remote_control(self, agent_id, command, timeout):
        return run(self.parent_conn, agent_id, command, timeout)
