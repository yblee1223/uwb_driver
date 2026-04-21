#!/usr/bin/env python3

import os
import csv
from datetime import datetime

import rclpy
from rclpy.node import Node
from uwb_driver.msg import UwbRange


class UwbLoggerNode(Node):

    def __init__(self):
        super().__init__('uwb_logger_node')

        # logs 폴더 경로
        log_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'logs'
        )
        os.makedirs(log_dir, exist_ok=True)

        # 파일명 — 실행 시각 기준
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_path = os.path.join(log_dir, f'uwb_{timestamp}.csv')

        # CSV 헤더
        cir_cols = [f'cir_{i}' for i in range(40)]
        self._fieldnames = [
            'wall_time', 'ros_time', 'seq', 'tag', 'anchor_id',
            'dist', 'rsl', 'fpidx', 'fprsl', 'fpns',
            'ppidx', 'pprsl', 'ppns'
        ] + cir_cols

        self._file = open(log_path, 'w', newline='')
        self._writer = csv.DictWriter(self._file, fieldnames=self._fieldnames)
        self._writer.writeheader()

        self._sub = self.create_subscription(
            UwbRange, '/uwb/range', self._callback, 10)

        self.get_logger().info(f'Logging to {log_path}')

    def _callback(self, msg):
        wall_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        ros_time = msg.header.stamp.sec * 10**9 + msg.header.stamp.nanosec

        # CIR 분리 — 앵커별로 40개씩
        cir_by_anchor = {}
        offset = 0
        for i, length in enumerate(msg.cir_len):
            anchor_id = msg.anchor_ids[i]
            cir_by_anchor[anchor_id] = list(msg.cir_data[offset:offset + length])
            offset += length

        # 앵커당 1행
        for i, anchor_id in enumerate(msg.anchor_ids):
            cir_samples = cir_by_anchor.get(anchor_id, [])
            # 40개 고정
            cir_samples = (cir_samples + [0.0] * 40)[:40]

            row = {
                'wall_time': wall_time,
                'ros_time':  ros_time,
                'seq':       msg.seq_num,
                'tag':       msg.tag_id,
                'anchor_id': anchor_id,
                'dist':      int(msg.dist[i]),
                'rsl':       round(msg.rsl[i], 2),
                'fpidx':     msg.fpidx[i],
                'fprsl':     round(msg.fprsl[i], 2),
                'fpns':      round(msg.fpns[i], 2),
                'ppidx':     msg.ppidx[i],
                'pprsl':     round(msg.pprsl[i], 2),
                'ppns':      round(msg.ppns[i], 2),
            }
            for j, val in enumerate(cir_samples):
                row[f'cir_{j}'] = round(val, 2)

            self._writer.writerow(row)

        self._file.flush()

    def destroy_node(self):
        self._file.close()
        self.get_logger().info('CSV file closed')
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = UwbLoggerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
