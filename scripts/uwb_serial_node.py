#!/usr/bin/env python3

import os
import sys
import time
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import Header

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from uwb_parser import is_block_start, parse_block

from uwb_driver.msg import UwbRange
import serial


class UwbSerialNode(Node):

    def __init__(self):
        super().__init__('uwb_serial_node')

        self.declare_parameter('port',         '/dev/ttyACM0')
        self.declare_parameter('baud',         115200)
        self.declare_parameter('topic',        '/uwb/range')
        self.declare_parameter('frame_id',     'uwb_link')
        self.declare_parameter('init_cmds',    [''])
        self.declare_parameter('read_timeout', 1.0)

        self._port         = self.get_parameter('port').value
        self._baud         = self.get_parameter('baud').value
        self._topic        = self.get_parameter('topic').value
        self._frame_id     = self.get_parameter('frame_id').value
        self._init_cmds    = [c for c in self.get_parameter('init_cmds').value if c]
        self._read_timeout = self.get_parameter('read_timeout').value

        self._pub = self.create_publisher(UwbRange, self._topic, 10)
        self.get_logger().info(f'Publishing on {self._topic}')

        self._ser = None
        self._serial_lock = threading.Lock()
        self._open_serial()

        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _open_serial(self):
        try:
            self._ser = serial.Serial(
                port=self._port,
                baudrate=self._baud,
                timeout=self._read_timeout,
            )
            self.get_logger().info(f'Opened {self._port} at {self._baud} baud')
            time.sleep(0.5)
            for cmd in self._init_cmds:
                self._send_command(cmd)
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open {self._port}: {e}')
            self._ser = None

    def _send_command(self, cmd):
        if self._ser is None or not self._ser.is_open:
            self.get_logger().warning(f'Cannot send "{cmd}": port not open')
            return
        with self._serial_lock:
            self._ser.write((cmd.strip() + '\r\n').encode())
            self.get_logger().info(f'Sent: {cmd.strip()}')

    def _read_loop(self):
        block_lines = []

        while self._running:
            if self._ser is None or not self._ser.is_open:
                time.sleep(1.0)
                self._open_serial()
                continue

            try:
                with self._serial_lock:
                    raw = self._ser.readline()
            except serial.SerialException as e:
                self.get_logger().error(f'Read error: {e}')
                self._ser = None
                continue

            if not raw:
                continue

            line = raw.decode('utf-8', errors='replace').strip()
            if not line:
                continue

            if is_block_start(line):
                if block_lines:
                    self._process_block(block_lines)
                block_lines = [line]
            else:
                block_lines.append(line)

    def _process_block(self, lines):
        parsed = parse_block(lines)
        if parsed is None:
            self.get_logger().warning('Failed to parse block')
            return

        msg = UwbRange()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = self._frame_id
        msg.seq_num         = int(parsed.get('seq_num', 0))
        msg.tag_id          = str(parsed.get('tag_id', ''))
        msg.anchor_ids      = [int(x)   for x in parsed.get('anchor_ids', [])]
        msg.dist            = [float(x) for x in parsed.get('dist',  [])]
        msg.rsl             = [float(x) for x in parsed.get('rsl',   [])]
        msg.fpidx           = [int(x)   for x in parsed.get('fpidx', [])]
        msg.fprsl           = [float(x) for x in parsed.get('fprsl', [])]
        msg.fpns            = [float(x) for x in parsed.get('fpns',  [])]
        msg.ppidx           = [int(x)   for x in parsed.get('ppidx', [])]
        msg.pprsl           = [float(x) for x in parsed.get('pprsl', [])]
        msg.ppns            = [float(x) for x in parsed.get('ppns',  [])]

        cir_dict = parsed.get('cir', {})
        flat, lengths = [], []
        for idx in sorted(cir_dict.keys()):
            samples = [float(x) for x in cir_dict[idx]]
            flat.extend(samples)
            lengths.append(len(samples))
        msg.cir_data = flat
        msg.cir_len  = lengths

        self._pub.publish(msg)
        self.get_logger().info(
            f'seq={msg.seq_num} tag={msg.tag_id} '
            f'anchors={msg.anchor_ids} dist={msg.dist} rsl={msg.rsl} '
            f'fpidx={msg.fpidx} fprsl={msg.fprsl} fpns={msg.fpns} '
            f'ppidx={msg.ppidx} pprsl={msg.pprsl} ppns={msg.ppns} '
            f'cir_len={msg.cir_len}')

    def destroy_node(self):
        self._running = False
        self._thread.join(timeout=2.0)
        if self._ser and self._ser.is_open:
            self._send_command('STOP')
            self._ser.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = UwbSerialNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._running = False
        if node._ser and node._ser.is_open:
            node._send_command('STOP')
            node._ser.close()
            node.get_logger().info('Serial port closed')
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
