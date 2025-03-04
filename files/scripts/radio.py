#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: 3UE_2Cell_scenario
# GNU Radio version: 3.8.1.0

from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import zeromq
import asyncio
import websockets
import urllib.request
import json
from functools import partial


class dynamic_scenario(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "dynamic_scenario")

        with urllib.request.urlopen("http://localhost:3000/configs/test.json") as url:
            data = json.load(url)
        
        cells = data['gnbs']
        ues = data['ues']

        ##################################################
        # Variables
        ##################################################
        self.zmq_timeout = zmq_timeout = 100
        self.zmq_hwm = zmq_hwm = -1
        self.samp_rate = samp_rate = 11520000

        ##################################################
        # Blocks
        ##################################################
        source_adders = {}
        sink_adders = {}
        sink_throttles = {}
        self.source_mults = source_mults ={}
        self.sink_mults = sink_mults ={}

        port = 2000
        for cell in cells:
            cell['tx'] = port
            cell['rx'] = port + 100
            port += 1
            sink_mults[cell['id']] = {}
            cell['source'] = zeromq.req_source(gr.sizeof_gr_complex, 1, f"tcp://127.0.0.1:{cell['tx']}", zmq_timeout, False, zmq_hwm)
            print(f"{cell['id']} source tcp://127.0.0.1:{cell['tx']}")
            cell['sink'] = zeromq.rep_sink(gr.sizeof_gr_complex, 1, f"tcp://127.0.0.1:{cell['rx']}", zmq_timeout, False, zmq_hwm)
            print(f"{cell['id']} sink tcp://127.0.0.1:{cell['rx']}")
            source_adders[cell['id']] = blocks.add_vcc(1)
        
        port = 2200
        for ue in ues:
            source_mults[ue['id']] = {}
            print(f"{ue['id']} sink tcp://127.0.0.1:{port}")
            ue['sink'] = zeromq.rep_sink(gr.sizeof_gr_complex, 1, f"tcp://127.0.0.1:{port}", zmq_timeout, False, zmq_hwm)
            port += 1
            print(f"{ue['id']} source tcp://127.0.0.1:{port}")
            ue['source'] = zeromq.req_source(gr.sizeof_gr_complex, 1, f"tcp://127.0.0.1:{port}", zmq_timeout, False, zmq_hwm)
            port += 1
            sink_adders[ue['id']] = blocks.add_vcc(1)
            sink_throttles[ue['id']] = blocks.throttle(gr.sizeof_gr_complex*1, samp_rate, True)
            for cell in cells:
                sink_mults[cell['id']][ue['id']] = blocks.multiply_const_cc(1)
                sink_mults[cell['id']][ue['id']].set_k(0)
                source_mults[ue['id']][cell['id']] = blocks.multiply_const_cc(1)
                source_mults[ue['id']][cell['id']].set_k(0)
            
        ##################################################
        # Connections
        ##################################################
        for i, ue in enumerate(ues):
            for j, cell in enumerate(cells):
                self.connect(
                    (ue['source'], 0), 
                    (source_mults[ue['id']][cell['id']], 0)
                )
                print("Connect", ue['source'], source_mults[ue['id']][cell['id']])
                self.connect(
                    (source_mults[ue['id']][cell['id']], 0), 
                    (source_adders[cell['id']], i)
                )
                print("Connect", source_mults[ue['id']][cell['id']], source_adders[cell['id']])
            self.connect(
                (sink_adders[ue['id']], 0), 
                (sink_throttles[ue['id']], 0)
            )
            print("Connect", sink_adders[ue['id']], sink_throttles[ue['id']])
            self.connect(
                (sink_throttles[ue['id']], 0), 
                (ue['sink'], 0)
            )
            print("Connect", sink_throttles[ue['id']], ue['sink'])
        
        for i, cell in enumerate(cells):
            self.connect(
                (source_adders[cell['id']], 0), 
                (cell['sink'], 0)
            )
            print("Connect", source_adders[cell['id']], cell['sink'])
            for j, ue in enumerate(ues):
                self.connect(
                    (cell['source'], 0), 
                    (sink_mults[cell['id']][ue['id']], 0)
                )
                print("Connect", cell['source'], sink_mults[cell['id']][ue['id']])
                self.connect(
                    (sink_mults[cell['id']][ue['id']], 0), 
                    (sink_adders[ue['id']], i)
                )
                print("Connect", sink_mults[cell['id']][ue['id']], sink_adders[ue['id']])


    def get_zmq_timeout(self):
        return self.zmq_timeout

    def set_zmq_timeout(self, zmq_timeout):
        self.zmq_timeout = zmq_timeout

    def get_zmq_hwm(self):
        return self.zmq_hwm

    def set_zmq_hwm(self, zmq_hwm):
        self.zmq_hwm = zmq_hwm

    # def get_samp_rate(self):
    #     return self.samp_rate

    # def set_samp_rate(self, samp_rate):
    #     self.samp_rate = samp_rate
    #     self.blocks_throttle_0.set_sample_rate(self.samp_rate)

    def connect_ue_to_cell(self, ue, cell):
        self.source_mults[ue][cell].set_k(1)
        self.sink_mults[cell][ue].set_k(1)
    
    def disconnect_ue_from_cell(self, ue, cell):
        self.source_mults[ue][cell].set_k(0)
        self.sink_mults[cell][ue].set_k(0)


async def handle_connection(websocket, path, tb=dynamic_scenario):
    async for message in websocket:
        print("Received:", message, path)
        try:
            data = json.loads(message)
            if 'action' in data and 'ue' in data and 'cell' in data:
                if data['action'] == 'connect':
                    tb.connect_ue_to_cell(data['ue'], data['cell'])
                elif data['action'] == 'disconnect':
                    tb.disconnect_ue_from_cell(data['ue'], data['cell'])
            else:
                print("Unknown command", file=sys.stderr)    
        except ValueError as e:
            print(f"Cannot parse message as JSON: {e}", file=sys.stderr)


async def listen(tb):
    async with websockets.serve(partial(handle_connection, tb=tb), "0.0.0.0", 8765):
        await asyncio.Future()


def main(top_block_cls=dynamic_scenario, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)
    
    print("Starting GNU Radio")
    tb.start()
    asyncio.run(listen(tb))
    print("Stopping GNU Radio")
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
