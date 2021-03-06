#  Copyright 2018 U.C. Berkeley RISE Lab
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging

from . import utils
from include.functions_pb2 import *
from include import server_utils as sutils

def pin(pin_socket, client, status, pinned_functions, runtimes):
    name = pin_socket.recv_string()
    logging.info('Adding function %s to my local pinned functions.' % (name))

    if not status.running:
        sutils.error.error = INVALID_TARGET
        pin_sockt.send(sutils.error.SerializeToString())
        return

    func = utils._retrieve_function(name, client)

    # we send an error if we can't retrieve the requested function
    if not func:
        sutils.error.error = FUNC_NOT_FOUND
        pin_socket.send(sutils.error.SerializeToString())
        return

    pin_socket.send(sutils.ok_resp)

    status.functions.append(name)
    pinned_functions[name] = func
    runtimes[name] = 0.0

def unpin(unpin_socket, status, pinned_functions, runtimes):
    name = unpin_socket.recv_string() # the name of the func to unpin
    logging.info('Removing function %s from my local pinned functions.' %
            (name))

    if not status.running:
        sutils.error.error = INVALID_TARGET
        pin_sockt.send(sutils.error.SerializeToString())
        return

    if name not in status.functions:
        sutils.error.error = NOT_PINNED
        unpin_socket.send(sutils.error.SerializeToString())
        return

    unpin_socket.send(sutils.ok_resp)

    func_queue = queue[name]
    # if there are no currently pending requests, then we can simply
    # unpin the existing function
    if len(func_queue) == 0:
        del pinned_functions[name]

    status.functions.remove(name)
    del runtimes[name]
