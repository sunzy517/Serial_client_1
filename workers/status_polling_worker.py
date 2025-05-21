#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
串口转发板控制系统 - 状态查询工作线程类
"""

import time
from PyQt5.QtCore import QObject, pyqtSignal


class StatusPollingWorker(QObject):
    """负责定期查询设备状态的工作线程类"""
    status_updated = pyqtSignal(dict)  # 信号：状态更新
    status_error = pyqtSignal(str)  # 信号：状态查询错误

    def __init__(self, comm_worker):
        super().__init__()
        self.comm_worker = comm_worker
        self.is_running = False
        self.interval = 1.0  # 查询间隔，默认1秒
        self.start_time = None

    def build_frame(self, address, command, data):
        """构建通信帧"""
        frame = bytearray([0xAA, 0x55, address, command, len(data)])
        frame.extend(data)
        checksum = (address + command + len(data) + sum(data)) & 0xFFFF
        frame.append((checksum >> 8) & 0xFF)
        frame.append(checksum & 0xFF)
        frame.extend([0x0D, 0x0A])
        return bytes(frame)

    def run(self):
        """工作线程主循环"""
        self.is_running = True
        self.start_time = time.time()

        while self.is_running:
            if self.comm_worker.is_connected():
                try:
                    # 查询温度 - 命令0xF6
                    temp_frame = self.build_frame(0xFF, 0xF6, b"")
                    self.comm_worker.add_task(temp_frame, {"type": "temperature"})

                    # 查询电压 - 命令0xF7
                    volt_frame = self.build_frame(0xFF, 0xF7, b"")
                    self.comm_worker.add_task(volt_frame, {"type": "voltage"})

                    # 计算运行时间
                    elapsed = int(time.time() - self.start_time)
                    hours = elapsed // 3600
                    minutes = (elapsed % 3600) // 60
                    seconds = elapsed % 60

                    # 发送信号，包含运行时间
                    self.status_updated.emit({
                        "runtime": f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    })
                except Exception as e:
                    self.status_error.emit(f"状态查询错误: {str(e)}")

            # 睡眠指定间隔时间
            time.sleep(self.interval)

    def stop(self):
        """停止工作线程"""
        self.is_running = False