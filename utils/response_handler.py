from utils.serial_board_client import SerialBoardClient


class ResponseHandler:
    """负责处理各种类型的响应"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.client = SerialBoardClient()

    def handle_response(self, response, context):
        """处理通信响应"""
        try:
            # 根据上下文类型处理不同的响应
            if context and "type" in context:
                resp_type = context["type"]

                if resp_type == "current_setting":
                    # 处理电流设置响应
                    self.main_window.log(f"电流设置响应: {response.hex(' ').upper()}")
                    addr = context.get("address", 0)
                    value = context.get("value", 0)
                    self.main_window.status_message.setText(f"已设置设备 {addr:02X} 电流值为 {value}")

                elif resp_type == "read_scr":
                    # 处理SCR读取响应
                    try:
                        parsed = self.client.parse_response(response)
                        if parsed and "data" in parsed and len(parsed["data"]) > 0:
                            scr_value = parsed["data"][0]
                            self.main_window.log(f"SCR值: {scr_value} ({response.hex(' ').upper()})")
                            addr = context.get("address", 0)
                            self.main_window.status_message.setText(f"已读取设备 {addr:02X} SCR值: {scr_value}")
                        else:
                            self.main_window.log(f"SCR读取响应数据解析错误: {response.hex(' ').upper()}")
                    except Exception as e:
                        self.main_window.log(f"SCR读取响应解析失败: {e}")

                elif resp_type == "write_scr":
                    # 处理SCR写入响应
                    self.main_window.log(f"SCR写入响应: {response.hex(' ').upper()}")
                    addr = context.get("address", 0)
                    self.main_window.status_message.setText(f"已向设备 {addr:02X} 写入SCR配置")

                elif resp_type == "temperature":
                    # 处理温度查询响应
                    try:
                        parsed = self.client.parse_response(response)
                        if parsed and "data" in parsed and len(parsed["data"]) > 0:
                            temp_value = int.from_bytes(parsed["data"], 'big')
                            self.main_window.temp_label.setText(f"温度: {temp_value} °C")
                            # 更新历史数据
                            self.main_window.temperature_history.append(temp_value)
                            self.main_window.temperature_history = self.main_window.temperature_history[-20:]
                    except Exception as e:
                        self.main_window.log(f"温度数据解析失败: {e}")

                elif resp_type == "voltage":
                    # 处理电压查询响应
                    try:
                        parsed = self.client.parse_response(response)
                        if parsed and "data" in parsed and len(parsed["data"]) > 0:
                            volt_value = int.from_bytes(parsed["data"], 'big')
                            self.main_window.volt_label.setText(f"电压: {volt_value / 10:.1f} V")
                            # 更新历史数据
                            self.main_window.voltage_history.append(volt_value / 10)
                            self.main_window.voltage_history = self.main_window.voltage_history[-20:]
                    except Exception as e:
                        self.main_window.log(f"电压数据解析失败: {e}")

                else:
                    # 处理其他未知类型的响应
                    self.main_window.log(f"未分类响应: {response.hex(' ').upper()}")
            else:
                # 无上下文的响应处理
                self.main_window.log(f"收到响应: {response.hex(' ').upper()}")

        except Exception as e:
            self.main_window.log(f"响应处理错误: {str(e)}")