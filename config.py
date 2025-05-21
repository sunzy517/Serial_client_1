#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
改进版配置管理器 - 集中管理所有配置项
"""

import json
import os
from enum import Enum


class Commands(Enum):
    """命令枚举，避免魔法数字"""
    SET_CURRENT = 0x03
    READ_SCR = 0x04
    WRITE_SCR = 0x05
    GET_TEMPERATURE = 0xF6
    GET_VOLTAGE = 0xF7


class Config:
    """配置管理类"""

    # 默认配置
    DEFAULT_CONFIG = {
        "network": {
            "default_ip": "127.0.0.1",
            "default_port": 9420,
            "socket_timeout": 3,
            "reconnect_attempts": 3,
            "reconnect_delay": 1
        },
        "polling": {
            "status_interval": 1.0,
            "temperature_interval": 2.0,
            "voltage_interval": 2.0
        },
        "ui": {
            "max_history_length": 20,
            "log_max_lines": 1000,
            "animation_duration": 1500
        },
        "protocol": {
            "frame_header": [0xAA, 0x55],
            "frame_footer": [0x0D, 0x0A],
            "max_data_length": 255,
            "checksum_bytes": 2
        }
    }

    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # 合并用户配置和默认配置
                return self._merge_config(self.DEFAULT_CONFIG, user_config)
            except Exception as e:
                print(f"加载配置文件失败: {e}，使用默认配置")
        return self.DEFAULT_CONFIG.copy()

    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def _merge_config(self, default, user):
        """递归合并配置"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, path, default=None):
        """获取配置值，支持点号路径"""
        try:
            keys = path.split('.')
            value = self.config
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, path, value):
        """设置配置值"""
        keys = path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value

    # 便捷属性访问
    @property
    def default_ip(self):
        return self.get('network.default_ip')

    @property
    def default_port(self):
        return self.get('network.default_port')

    @property
    def socket_timeout(self):
        return self.get('network.socket_timeout')

    @property
    def status_interval(self):
        return self.get('polling.status_interval')

    @property
    def max_history_length(self):
        return self.get('ui.max_history_length')

    @property
    def frame_header(self):
        return self.get('protocol.frame_header')

    @property
    def frame_footer(self):
        return self.get('protocol.frame_footer')


# 全局配置实例
config = Config()