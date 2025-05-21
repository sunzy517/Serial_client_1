import sys
import time
from datetime import datetime
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QLineEdit, QTextEdit,
    QVBoxLayout, QHBoxLayout, QComboBox, QSlider, QStatusBar, QFileDialog,
    QGroupBox, QGridLayout, QSplitter, QGraphicsDropShadowEffect,
    QProgressBar, QMessageBox, QApplication, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QThread

from ui.custom_widgets import TechButton
from workers.communication_worker import CommunicationWorker
from workers.status_polling_worker import StatusPollingWorker
from utils.serial_board_client import SerialBoardClient
from utils.response_handler import ResponseHandler


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("串口转发板控制系统 V3.0")
        self.setMinimumSize(1100, 700)

        # 初始化状态变量
        self.client = SerialBoardClient()
        self.temperature_history = [20] * 20  # 假数据用于初始化
        self.voltage_history = [12] * 20  # 假数据用于初始化
        self.current_slider_value = 0
        self.response_handler = ResponseHandler(self)

        # 设置图标
        icon_path = "logo.png"
        self.setWindowIcon(QIcon(icon_path))

        # 创建工作线程
        self.setup_workers()

        # 创建UI元素
        self.create_ui_elements()
        self.init_ui()
        self.bind_events()
        self.apply_styles()

        # 连接动画
        self.connection_animation = QPropertyAnimation(self.connection_indicator, b"geometry")
        self.connection_animation.setDuration(1500)
        self.connection_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.connection_animation.setLoopCount(-1)  # 无限循环

    def setup_workers(self):
        """设置工作线程"""
        # 通信工作线程
        self.comm_worker = CommunicationWorker()
        self.comm_thread = QThread()
        self.comm_worker.moveToThread(self.comm_thread)

        # 连接信号和槽
        self.comm_worker.response_received.connect(self.handle_response)
        self.comm_worker.connection_error.connect(self.handle_connection_error)
        self.comm_worker.connection_status_changed.connect(self.handle_connection_status)

        # 启动通信线程
        self.comm_thread.started.connect(self.comm_worker.run)
        self.comm_thread.start()

        # 状态查询工作线程
        self.status_worker = StatusPollingWorker(self.comm_worker)
        self.status_thread = QThread()
        self.status_worker.moveToThread(self.status_thread)

        # 连接信号和槽
        self.status_worker.status_updated.connect(self.update_status_display)
        self.status_worker.status_error.connect(self.handle_status_error)

        # 启动状态查询线程
        self.status_thread.started.connect(self.status_worker.run)
        # 状态查询线程在连接成功后启动

    def create_ui_elements(self):
        """创建UI元素"""
        # 连接区域
        self.ip_input = QLineEdit("127.0.0.1")
        self.port_input = QLineEdit("9420")
        self.connect_btn = TechButton("连接系统")
        self.disconnect_btn = TechButton("断开连接")
        self.connection_indicator = QLabel()
        self.connection_indicator.setFixedSize(16, 16)
        self.connection_indicator.setStyleSheet("background-color: #FF3333; border-radius: 8px;")

        # 设备选择区域
        self.device_selector = QComboBox()
        self.device_selector.addItems([f"设备 {i:02d}" for i in range(16)])

        # 控制区域
        self.scr_read_btn = TechButton("读取 SCR 数据")
        self.scr_write_btn = TechButton("写入 SCR 配置")

        # 电流控制滑块
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(255)
        self.slider.setTickInterval(5)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider_label = QLabel("电流值: 0")
        self.slider_confirm_btn = TechButton("应用电流设置")
        self.current_progress = QProgressBar()
        self.current_progress.setRange(0, 255)
        self.current_progress.setValue(0)
        self.current_progress.setTextVisible(True)
        self.current_progress.setFormat("%v / 255")

        # 自由发送数据区域
        self.custom_data_input = QLineEdit()
        self.custom_data_input.setPlaceholderText("输入要发送内容")
        self.hex_mode_checkbox = QCheckBox("十六进制模式")
        self.hex_mode_checkbox.setChecked(True)  # 默认使用十六进制
        self.custom_send_btn = TechButton("发送自定义数据")

        # 状态显示区域
        self.temp_label = QLabel("温度: -- °C")
        self.volt_label = QLabel("电压: -- V")
        self.time_label = QLabel("运行时间: 00:00:00")
        self.mcu_status_label = QLabel("系统状态: 离线")

        # 日志区域
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.save_log_btn = TechButton("导出日志记录")
        self.clear_log_btn = TechButton("清除日志")

        # 状态栏
        self.status_bar = self.statusBar()
        self.status_message = QLabel("系统就绪")
        self.status_bar.addWidget(self.status_message)

    def init_ui(self):
        """初始化UI布局"""
        main_layout = QVBoxLayout()

        # 顶部标题（带logo）
        header_layout = QHBoxLayout()

        # Logo
        logo_label = QLabel()
        pixmap = QPixmap("logo.png")
        if not pixmap.isNull():
            # 设置logo大小，高度与标题字体相匹配
            scaled_pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            # 如果logo文件不存在，显示一个默认的占位符
            logo_label.setText("🏭")
            logo_label.setFont(QFont("Arial", 10))

        # 标题文本
        header_text = QLabel("串口转发板控制系统")
        header_text.setFont(QFont("Arial", 16, QFont.Bold))
        header_text.setStyleSheet("color: #00FFAA; margin: 10px;")

        # 添加到水平布局
        header_layout.addStretch()  # 左侧弹性空间
        header_layout.addWidget(logo_label)
        header_layout.addSpacing(10)  # logo和标题之间的间距
        header_layout.addWidget(header_text)
        header_layout.addStretch()  # 右侧弹性空间

        main_layout.addLayout(header_layout)

        # 创建水平分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧控制面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # 连接控制组
        conn_group = QGroupBox("系统连接")
        conn_layout = QGridLayout()
        conn_layout.addWidget(QLabel("服务器IP:"), 0, 0)
        conn_layout.addWidget(self.ip_input, 0, 1)
        conn_layout.addWidget(QLabel("端口:"), 1, 0)
        conn_layout.addWidget(self.port_input, 1, 1)
        conn_layout.addWidget(self.connect_btn, 2, 0)
        conn_layout.addWidget(self.disconnect_btn, 2, 1)
        conn_status_layout = QHBoxLayout()
        conn_status_layout.addWidget(QLabel("连接状态:"))
        conn_status_layout.addWidget(self.connection_indicator)
        conn_status_layout.addWidget(self.mcu_status_label)
        conn_status_layout.addStretch()
        conn_layout.addLayout(conn_status_layout, 3, 0, 1, 2)
        conn_group.setLayout(conn_layout)
        left_layout.addWidget(conn_group)

        # 设备控制组
        device_group = QGroupBox("设备控制")
        device_layout = QGridLayout()
        device_layout.addWidget(QLabel("设备地址:"), 0, 0)
        device_layout.addWidget(self.device_selector, 0, 1)
        device_layout.addWidget(self.scr_read_btn, 1, 0)
        device_layout.addWidget(self.scr_write_btn, 1, 1)
        device_group.setLayout(device_layout)
        left_layout.addWidget(device_group)

        # 电流控制组
        current_group = QGroupBox("电流控制")
        current_layout = QVBoxLayout()
        current_layout.addWidget(self.slider_label)

        slider_progress_layout = QHBoxLayout()
        slider_progress_layout.addWidget(self.slider, 7)
        slider_progress_layout.addWidget(self.current_progress, 3)
        current_layout.addLayout(slider_progress_layout)

        current_layout.addWidget(self.slider_confirm_btn)
        current_group.setLayout(current_layout)
        left_layout.addWidget(current_group)

        # 自定义数据发送组
        custom_send_group = QGroupBox("自定义数据发送")
        custom_send_layout = QVBoxLayout()

        # 数据输入框
        custom_send_layout.addWidget(QLabel("数据内容:"))
        custom_send_layout.addWidget(self.custom_data_input)

        # 模式选择和发送按钮
        mode_send_layout = QHBoxLayout()
        mode_send_layout.addWidget(self.hex_mode_checkbox)
        mode_send_layout.addStretch()
        mode_send_layout.addWidget(self.custom_send_btn)
        custom_send_layout.addLayout(mode_send_layout)

        # 使用说明
        help_label = QLabel()  # "说明:\n• 十六进制模式: AA BB CC 或 AABBCC\n• 十进制模式: 170 187 204"
        help_label.setStyleSheet("color: #888888; font-size: 10px;")
        help_label.setWordWrap(True)
        custom_send_layout.addWidget(help_label)

        custom_send_group.setLayout(custom_send_layout)
        left_layout.addWidget(custom_send_group)

        # 状态信息组
        status_group = QGroupBox("系统状态")
        status_layout = QGridLayout()
        status_layout.addWidget(self.temp_label, 0, 0)
        status_layout.addWidget(self.volt_label, 0, 1)
        status_layout.addWidget(self.time_label, 1, 0, 1, 2)
        status_group.setLayout(status_layout)
        left_layout.addWidget(status_group)

        left_layout.addStretch()

        # 右侧日志面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        log_group = QGroupBox("系统日志")
        log_layout = QVBoxLayout()
        log_layout.addWidget(self.log_output)

        log_buttons = QHBoxLayout()
        log_buttons.addWidget(self.save_log_btn)
        log_buttons.addWidget(self.clear_log_btn)
        log_layout.addLayout(log_buttons)

        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)

        # 添加左右面板到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 700])  # 设置初始大小比例

        main_layout.addWidget(splitter)

        # 创建中央窗口部件
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # 初始化按钮状态
        self.disconnect_btn.setEnabled(False)

    def bind_events(self):
        """绑定事件处理函数"""
        self.connect_btn.clicked.connect(self.connect_to_server)
        self.disconnect_btn.clicked.connect(self.disconnect_from_server)
        self.slider.valueChanged.connect(self.update_slider_label)
        self.slider_confirm_btn.clicked.connect(self.send_current_value)
        self.scr_read_btn.clicked.connect(self.read_scr)
        self.scr_write_btn.clicked.connect(self.write_scr)
        self.custom_send_btn.clicked.connect(self.send_custom_data)
        self.save_log_btn.clicked.connect(self.save_log)
        self.clear_log_btn.clicked.connect(self.clear_log)

        # 回车键快捷发送
        self.custom_data_input.returnPressed.connect(self.send_custom_data)

    def apply_styles(self):
        """应用样式表"""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0A1929;
                color: #E0E0E0;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            QGroupBox {
                border: 1px solid #00BFFF;
                border-radius: 8px;
                margin-top: 12px;
                padding: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                color: #00FFAA;
            }
            QPushButton {
                background-color: #001F3F;
                color: #00FFAA;
                border: 1px solid #00BFFF;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #003366;
                border: 1px solid #00FFAA;
            }
            QPushButton:pressed {
                background-color: #004080;
            }
            QLineEdit, QComboBox {
                background-color: #0F2D45;
                color: #E0E0E0;
                border: 1px solid #00BFFF;
                border-radius: 4px;
                padding: 6px;
                selection-background-color: #00BFFF;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #00FFAA;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: right;
                width: 20px;
                border-left: 1px solid #00BFFF;
            }
            QCheckBox {
                spacing: 8px;
                color: #E0E0E0;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #00BFFF;
                border-radius: 3px;
                background-color: #0F2D45;
            }
            QCheckBox::indicator:checked {
                background-color: #00FFAA;
                border: 1px solid #00FFAA;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #00FFC3;
            }
            QSlider::groove:horizontal {
                border: 1px solid #00BFFF;
                height: 8px;
                background: #0F2D45;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00FFAA;
                border: 1px solid #005566;
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #00FFC3;
            }
            QTextEdit {
                background-color: #0F2D45;
                color: #00FFAA;
                border: 1px solid #00BFFF;
                border-radius: 5px;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QProgressBar {
                border: 1px solid #00BFFF;
                border-radius: 4px;
                text-align: center;
                background-color: #0F2D45;
            }
            QProgressBar::chunk {
                background-color: #00BFFF;
                border-radius: 3px;
            }
            QLabel {
                color: #E0E0E0;
            }
            QStatusBar {
                background-color: #001F3F;
                color: #00FFAA;
            }
        """)

    def connect_to_server(self):
        """连接到服务器"""
        try:
            ip = self.ip_input.text()
            port = int(self.port_input.text())

            # 禁用连接按钮，避免重复点击
            self.connect_btn.setEnabled(False)
            self.status_message.setText("正在连接...")

            # 在通信线程中执行连接操作
            if self.comm_worker.connect(ip, port):
                # 启动状态查询线程
                if not self.status_thread.isRunning():
                    self.status_thread.start()

                self.log("系统连接成功")
                self.status_message.setText("系统已连接")
        except ValueError:
            self.connect_btn.setEnabled(True)
            QMessageBox.warning(self, "输入错误", "请输入有效的端口号")
        except Exception as e:
            self.connect_btn.setEnabled(True)
            self.log(f"连接失败: {e}")
            self.status_message.setText(f"连接失败: {str(e)[:30]}...")

    def disconnect_from_server(self):
        """断开服务器连接"""
        # 停止状态查询
        if self.status_thread.isRunning():
            self.status_worker.stop()
            self.status_thread.quit()
            self.status_thread.wait()
            # 重新创建状态查询工作线程，以备下次连接
            self.status_worker = StatusPollingWorker(self.comm_worker)
            self.status_worker.moveToThread(self.status_thread)
            self.status_worker.status_updated.connect(self.update_status_display)
            self.status_worker.status_error.connect(self.handle_status_error)
            self.status_thread.started.connect(self.status_worker.run)

        # 断开通信连接
        self.comm_worker.disconnect()

        # 重置UI状态
        self.stop_connection_animation()
        self.log("系统连接已断开")
        self.status_message.setText("系统已断开连接")

        # 重置状态显示
        self.temp_label.setText("温度: -- °C")
        self.volt_label.setText("电压: -- V")
        self.time_label.setText("运行时间: 00:00:00")

    def start_connection_animation(self):
        """启动连接指示器动画"""
        rect = self.connection_indicator.geometry()
        self.connection_animation.setStartValue(rect)
        self.connection_animation.setEndValue(rect)
        self.connection_animation.start()
        self.connection_indicator.setStyleSheet("background-color: #00FF00; border-radius: 8px;")

    def stop_connection_animation(self):
        """停止连接指示器动画"""
        self.connection_animation.stop()
        self.connection_indicator.setStyleSheet("background-color: #FF3333; border-radius: 8px;")

    def update_slider_label(self, value):
        """更新滑块标签显示"""
        self.current_slider_value = value
        self.slider_label.setText(f"电流值: {value}")
        self.current_progress.setValue(value)

    def send_current_value(self):
        """发送电流设置值"""
        if not self.comm_worker.is_connected():
            self.log("错误: 系统未连接，无法发送")
            return

        try:
            addr = self.device_selector.currentIndex()
            data = bytes([self.current_slider_value])
            frame = self.client.build_frame(addr, 0x03, data)

            self.log(f"设置电流值: {self.current_slider_value} ({frame.hex(' ').upper()})")

            # 添加任务并设置上下文
            context = {
                "type": "current_setting",
                "value": self.current_slider_value,
                "address": addr
            }
            self.comm_worker.add_task(frame, context)

            # 简单的动画效果
            self.current_progress.setStyleSheet("QProgressBar::chunk { background-color: #00FFAA; }")
            QTimer.singleShot(500, lambda: self.current_progress.setStyleSheet(
                "QProgressBar::chunk { background-color: #00BFFF; }"))

            self.status_message.setText(f"正在设置设备 {addr:02X} 电流值...")
        except Exception as e:
            self.log(f"发送失败: {e}")
            self.status_message.setText("电流设置失败")

    def send_custom_data(self):
        """发送自定义数据"""
        if not self.comm_worker.is_connected():
            self.log("错误: 系统未连接，无法发送自定义数据")
            QMessageBox.warning(self, "连接错误", "系统未连接，请先连接到服务器")
            return

        try:
            input_text = self.custom_data_input.text().strip()
            if not input_text:
                QMessageBox.warning(self, "输入错误", "请输入要发送的数据")
                return

            # 解析数据
            data_bytes = self.parse_input_data(input_text)
            if data_bytes is None:
                return

            # 发送数据
            frame = bytes(data_bytes)
            self.log(f"发送自定义数据: {input_text} → {frame.hex(' ').upper()}")

            # 添加任务并设置上下文
            context = {
                "type": "custom_data",
                "input": input_text,
                "format": "hex" if self.hex_mode_checkbox.isChecked() else "dec"
            }
            self.comm_worker.add_task(frame, context)

            self.status_message.setText("正在发送自定义数据...")

            # 发送成功后清空输入框
            self.custom_data_input.clear()

        except Exception as e:
            self.log(f"自定义数据发送失败: {e}")
            self.status_message.setText("自定义数据发送失败")
            QMessageBox.critical(self, "发送错误", f"发送失败: {str(e)}")

    def parse_input_data(self, input_text):
        """解析输入的数据文本"""
        try:
            if self.hex_mode_checkbox.isChecked():
                # 十六进制模式
                # 移除所有空格和常见分隔符
                hex_str = input_text.replace(' ', '').replace('-', '').replace(':', '').replace(',', '')

                # 确保长度为偶数
                if len(hex_str) % 2 != 0:
                    # 如果输入了空格分隔的格式，尝试按空格分割
                    parts = input_text.split()
                    data_bytes = []
                    for part in parts:
                        if len(part) == 1:
                            part = '0' + part  # 单个字符前补0
                        data_bytes.append(int(part, 16))
                    return data_bytes
                else:
                    # 按两个字符一组解析
                    data_bytes = []
                    for i in range(0, len(hex_str), 2):
                        byte_str = hex_str[i:i + 2]
                        data_bytes.append(int(byte_str, 16))
                    return data_bytes
            else:
                # 十进制模式
                # 按空格、逗号等分隔符分割
                import re
                parts = re.split(r'[,\s]+', input_text)
                data_bytes = []
                for part in parts:
                    if part:  # 忽略空字符串
                        value = int(part)
                        if 0 <= value <= 255:
                            data_bytes.append(value)
                        else:
                            raise ValueError(f"字节值 {value} 超出范围 [0-255]")
                return data_bytes

        except ValueError as e:
            error_msg = f"数据格式错误: {str(e)}"
            if self.hex_mode_checkbox.isChecked():
                error_msg += "\n十六进制格式示例: AA BB CC 或 AABBCC"
            else:
                error_msg += "\n十进制格式示例: 170 187 204"

            QMessageBox.warning(self, "数据格式错误", error_msg)
            self.log(f"数据解析错误: {error_msg}")
            return None

    def read_scr(self):
        """读取SCR寄存器"""
        if not self.comm_worker.is_connected():
            self.log("错误: 系统未连接，无法读取SCR")
            return

        try:
            addr = self.device_selector.currentIndex()
            frame = self.client.build_frame(addr, 0x04, b"")

            self.log(f"读取SCR: {frame.hex(' ').upper()}")

            # 添加任务并设置上下文
            context = {
                "type": "read_scr",
                "address": addr
            }
            self.comm_worker.add_task(frame, context)

            self.status_message.setText(f"正在读取设备 {addr:02X} SCR数据...")
        except Exception as e:
            self.log(f"SCR读取失败: {e}")
            self.status_message.setText("SCR读取失败")

    def write_scr(self):
        """写入SCR寄存器"""
        if not self.comm_worker.is_connected():
            self.log("错误: 系统未连接，无法写入SCR")
            return

        try:
            addr = self.device_selector.currentIndex()
            frame = self.client.build_frame(addr, 0x05, bytes([0x48]))  # 固定写入0x48

            self.log(f"写入SCR: {frame.hex(' ').upper()}")

            # 添加任务并设置上下文
            context = {
                "type": "write_scr",
                "address": addr,
                "value": 0x48
            }
            self.comm_worker.add_task(frame, context)

            self.status_message.setText(f"正在向设备 {addr:02X} 写入SCR配置...")
        except Exception as e:
            self.log(f"SCR写入失败: {e}")
            self.status_message.setText("SCR写入失败")

    def handle_response(self, response, context):
        """处理通信响应，委托给ResponseHandler处理"""
        self.response_handler.handle_response(response, context)

    def handle_connection_error(self, error_msg):
        """处理连接错误"""
        self.log(f"连接错误: {error_msg}")
        self.status_message.setText(f"连接错误: {error_msg[:30]}...")

        # 如果错误表明连接已断开，更新UI状态
        if "未连接" in error_msg or "超时" in error_msg or "连接" in error_msg:
            self.handle_connection_status(False)

    def handle_connection_status(self, connected):
        """处理连接状态变化"""
        if connected:
            # 连接成功
            self.mcu_status_label.setText("系统状态: 在线")
            self.start_connection_animation()
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
        else:
            # 连接断开
            self.mcu_status_label.setText("系统状态: 离线")
            self.stop_connection_animation()
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)

    def handle_status_error(self, error_msg):
        """处理状态查询错误"""
        self.log(f"状态更新错误: {error_msg}")
        # 仅在严重错误时显示到状态栏，避免太频繁的错误消息
        if "连接" in error_msg or "通信" in error_msg:
            self.status_message.setText(f"状态更新错误: {error_msg[:30]}...")

    def update_status_display(self, status_dict):
        """更新状态显示"""
        # 更新运行时间
        if "runtime" in status_dict:
            self.time_label.setText(f"运行时间: {status_dict['runtime']}")

    def log(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] {message}"

        # 使用Qt的主线程安全的方式更新UI
        QApplication.instance().processEvents()
        self.log_output.append(formatted_message)

        # 自动滚动到底部
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def save_log(self):
        """保存日志到文件"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存日志",
            f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_output.toPlainText())
            self.status_message.setText(f"日志已保存至: {filename}")
            self.log(f"日志已导出到文件: {filename}")

    def clear_log(self):
        """清除日志"""
        self.log_output.clear()
        self.status_message.setText("日志已清除")

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 停止所有线程，并确保清理资源
        self.status_worker.stop()
        self.status_thread.quit()
        self.status_thread.wait()

        self.comm_worker.stop()
        self.comm_thread.quit()
        self.comm_thread.wait()

        event.accept()