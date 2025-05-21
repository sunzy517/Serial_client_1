#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
串口转发板控制系统 - 通信工作线程类
"""

import socket
import queue
from PyQt5.QtCore import QObject, QMutex, pyqtSignal


class CommunicationWorker(QObject):
    """负责处理网络通信的工作线程类"""
    response_received = pyqtSignal(bytes, object)  # 信号：返回响应和请求上下文
    connection_error = pyqtSignal(str)  # 信号：连接错误
    connection_status_changed = pyqtSignal(bool)  # 信号：连接状态改变

    def __init__(self):
        super().__init__()
        self.sock = None
        self.is_running = False
        self.mutex = QMutex()
        self.task_queue = queue.Queue()
        self.ip = '127.0.0.1'
        self.port = 9420

    def connect(self, ip, port):
        """连接到服务器"""
        try:
            self.mutex.lock()
            if self.sock:
                self.sock.close()

            self.ip = ip
            self.port = port
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(3)
            self.sock.connect((self.ip, self.port))
            self.connection_status_changed.emit(True)
            self.mutex.unlock()
            return True
        except Exception as e:
            self.mutex.unlock()
            self.connection_error.emit(str(e))
            return False

    def disconnect(self):
        """断开连接"""
        self.mutex.lock()  # 互斥锁
        if self.sock:
            self.sock.close()
            self.sock = None
            self.connection_status_changed.emit(False)
        self.mutex.unlock()

    def is_connected(self):
        """检查是否已连接"""
        self.mutex.lock()
        result = self.sock is not None
        self.mutex.unlock()
        return result

    def add_task(self, frame, context=None):
        """添加通信任务到队列"""
        self.task_queue.put((frame, context))

    def run(self):
        """工作线程主循环"""
        self.is_running = True
        while self.is_running:
            try:
                # 尝试获取任务，最多等待0.1秒
                try:
                    frame, context = self.task_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # 发送数据并接收响应
                self.mutex.lock()
                if not self.sock:
                    self.mutex.unlock()
                    self.connection_error.emit("未连接到服务器")
                    continue

                try:
                    self.sock.sendall(frame)
                    response = self.sock.recv(1024)
                    self.mutex.unlock()
                    # 发送信号，传递响应和上下文
                    self.response_received.emit(response, context)
                except socket.timeout:
                    self.mutex.unlock()
                    self.connection_error.emit("服务器响应超时")
                except Exception as e:
                    self.mutex.unlock()
                    self.connection_error.emit(f"通信错误: {str(e)}")
            except Exception as e:
                # 捕获循环中可能的其他异常
                self.connection_error.emit(f"工作线程错误: {str(e)}")

    def stop(self):
        """停止工作线程"""
        self.is_running = False
        self.disconnect()