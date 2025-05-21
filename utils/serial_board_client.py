#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
串口转发板控制系统 - 辅助类
"""


class SerialBoardClient:
    """串口转发板客户端类 - 用于构建和解析通信帧"""

    def __init__(self):
        pass

    @staticmethod
    def build_frame(address, command, data):
        """构建通信帧"""
        frame = bytearray([0xAA, 0x55, address, command, len(data)])
        frame.extend(data)
        checksum = (address + command + len(data) + sum(data)) & 0xFFFF
        frame.append((checksum >> 8) & 0xFF)
        frame.append(checksum & 0xFF)
        frame.extend([0x0D, 0x0A])
        return bytes(frame)

    @staticmethod
    def parse_response(response):
        """解析响应帧"""
        if len(response) < 7:  # 帧头(2) + 地址(1) + 命令(1) + 长度(1) + 校验和(2) = 7字节
            raise ValueError("响应数据长度不足")

        address = response[2]
        command = response[3]
        data_len = response[4]
        data = response[5:5 + data_len] if data_len > 0 else b""

        # 校验响应
        if response[0] != 0xAA or response[1] != 0x55:
            raise ValueError("响应帧头错误")

        return {
            "address": address,
            "command": command,
            "data": data
        }