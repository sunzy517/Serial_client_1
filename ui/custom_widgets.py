#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
串口转发板控制系统 - 自定义UI组件
"""

from PyQt5.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt


class TechButton(QPushButton):
    """自定义按钮类"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        effect = QGraphicsDropShadowEffect()
        effect.setOffset(0, 2)
        effect.setBlurRadius(15)
        effect.setColor(QColor(0, 255, 170, 70))
        self.setGraphicsEffect(effect)