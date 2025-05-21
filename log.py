#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
改进版日志系统 - 使用标准logging模块
"""

import logging
import sys
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QTextEdit


class QTextEditHandler(logging.Handler):
    """自定义日志处理器，输出到QTextEdit"""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        """发送日志记录到UI"""
        try:
            msg = self.format(record)
            # 确保在主线程中更新UI
            self.text_widget.append(msg)

            # 控制日志行数，避免内存泄漏
            cursor = self.text_widget.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor, 1000)

            # 如果超过1000行，删除最早的行
            if cursor.hasSelection():
                cursor.removeSelectedText()

        except Exception:
            # 避免日志处理器本身出错影响程序
            pass


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""

    COLORS = {
        'DEBUG': '#888888',  # 灰色
        'INFO': '#00FFAA',  # 绿色
        'WARNING': '#FFD700',  # 金色
        'ERROR': '#FF4444',  # 红色
        'CRITICAL': '#FF0000'  # 亮红色
    }

    def format(self, record):
        # 添加时间戳
        record.timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # 基本格式化
        formatted = super().format(record)

        # 添加颜色（仅用于UI显示）
        color = self.COLORS.get(record.levelname, '#E0E0E0')
        return f'<span style="color: {color}">{formatted}</span>'


class LogManager(QObject):
    """日志管理器"""

    # 信号：用于在非主线程中安全记录日志
    log_signal = pyqtSignal(str, int)

    def __init__(self, text_widget=None, log_file=None):
        super().__init__()
        self.logger = logging.getLogger('SerialBoard')
        self.logger.setLevel(logging.DEBUG)

        # 清除已有的处理器
        self.logger.handlers.clear()

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '[%(timestamp)s] %(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # 文件处理器
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d]: %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        # UI处理器
        if text_widget:
            ui_handler = QTextEditHandler(text_widget)
            ui_formatter = ColoredFormatter('[%(timestamp)s] %(levelname)s: %(message)s')
            ui_handler.setFormatter(ui_formatter)
            self.logger.addHandler(ui_handler)

            # 连接信号槽，支持跨线程日志
            self.log_signal.connect(self._emit_to_ui)

    def _emit_to_ui(self, message, level):
        """在主线程中发送日志到UI"""
        log_method = getattr(self.logger, logging.getLevelName(level).lower())
        log_method(message)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

    # 跨线程日志方法
    def thread_safe_info(self, message):
        self.log_signal.emit(message, logging.INFO)

    def thread_safe_error(self, message):
        self.log_signal.emit(message, logging.ERROR)

    def thread_safe_warning(self, message):
        self.log_signal.emit(message, logging.WARNING)

    def set_level(self, level):
        """设置日志级别"""
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self.logger.setLevel(level)

    def add_context(self, **kwargs):
        """添加上下文信息到日志"""
        extra = kwargs
        return LoggerAdapter(self.logger, extra)


class LoggerAdapter(logging.LoggerAdapter):
    """日志适配器，用于添加上下文信息"""

    def process(self, msg, kwargs):
        return f"[{', '.join(f'{k}={v}' for k, v in self.extra.items())}] {msg}", kwargs


# 使用示例
def create_logger(text_widget=None, log_file=None):
    """创建日志管理器的工厂函数"""
    return LogManager(text_widget, log_file)