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

GET_ADDR = "ipc:///requests/get"
PUT_ADDR = "ipc:///requests/put"

from .kvs_pb2 import *
from .lattices import *
import zmq

class IpcAnnaClient:
    def __init__(self, offset=0):
        self.context = zmq.Context(1)

        self.get_socket = self.context.socket(zmq.REQ)
        self.get_socket.connect(GET_ADDR)

        self.put_socket = self.context.socket(zmq.REQ)
        self.put_socket.connect(PUT_ADDR)

    def get(self, key, ltype):
        request = KeyRequest()
        request.type = GET

        tp = request.tuples.add()
        tp.lattice_type = ltype
        tp.key = key

        self.get_socket.send(request.SerializeToString())

        resp = KeyResponse()
        resp.ParseFromString(self.get_socket.recv())

        tp = resp.tuples[0]

        if tp.error == 1:
            print('Key %s does not exist!' % (key))
            return None

        if tp.lattice_type == LWW:
            val = LWWValue()
            val.ParseFromString(tp.payload)

            return LWWPairLattice(val.timestamp, val.value)
        elif tp.lattice_type == SET:
            res = set()

            val = SetValue()
            val.ParseFromString(tp.payload)

            for v in val.values:
                res.add(v)

            return SetLattice(res)
        else:
            raise ValueError('Invalid Lattice type: ' + str(tp.lattice_type))

    def put(self, key, value):
        request = KeyRequest()
        request.type = PUT

        tp = request.tuples.add()
        tp.key = key

        if type(value) == LWWPairLattice:
            tp.lattice_type = LWW

            ser = LWWValue()
            ser.timestamp = value.reveal()[0]
            ser.value = value.reveal()[1]

            tp.payload = ser.SerializeToString()
        elif type(value) == SetLattice:
            tp.lattice_type = SET

            ser = SetValue()
            ser.values.extend(list(value.reveal()))

            tp.payload = ser.SerializeToString()
        else:
            raise ValueError('Invalid PUT type: ' + str(type(value)))

        self.put_socket.send(request.SerializeToString())

        resp = KeyResponse()
        resp.ParseFromString(self.put_socket.recv())

        return resp.tuples[0].error == 0
