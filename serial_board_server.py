import socket
import threading

# 模拟 MCU 的服务端逻辑，支持基本命令响应
class MockMCUServer:
    def __init__(self, host='0.0.0.0', port=9420):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f"模拟MCU服务端启动，监听 {self.host}:{self.port}")
        while self.running:
            client_socket, addr = self.server_socket.accept()
            print(f"连接来自: {addr}")
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()

    def handle_client(self, client_socket):
        with client_socket:
            while self.running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    print(f"收到数据: {data.hex(' ').upper()}")
                    response = self.build_response(data)
                    if response:
                        client_socket.sendall(response)
                        print(f"发送响应: {response.hex(' ').upper()}")
                except Exception as e:
                    print(f"客户端处理异常: {e}")
                    break

    def build_response(self, data: bytes) -> bytes:
        if len(data) < 7 or data[0] != 0xAA or data[1] != 0x55:
            return b''

        addr = data[2]
        cmd = data[3]

        if cmd == 0x00:  # 透传
            return self.make_frame(addr, cmd, data[5:-4])
        elif cmd == 0x01:  # 串口配置
            return self.make_frame(addr, cmd, b'\x01')
        elif cmd == 0x04:  # 读SCR
            return self.make_frame(addr, cmd, b'\x48')
        elif cmd == 0x05:  # 写SCR确认
            return self.make_frame(addr, cmd, b'\x06')
        elif cmd == 0xF2:  # 运行时间
            return self.make_frame(addr, cmd, b'\x00\x00\x03\xE8')  # 1000s
        elif cmd == 0xF6:  # MCU温度
            return self.make_frame(addr, cmd, b'\x00\x2D')  # 45°C
        elif cmd == 0xF7:  # MCU电压
            return self.make_frame(addr, cmd, b'\x09\xC4')  # 2500mV
        else:
            return self.make_frame(addr, cmd, b'\x00')

    def make_frame(self, addr, cmd, payload):
        frame = bytearray([0xAA, 0x55, addr, cmd, len(payload)])
        frame.extend(payload)
        checksum = (addr + cmd + len(payload) + sum(payload)) & 0xFFFF
        frame.append((checksum >> 8) & 0xFF)
        frame.append(checksum & 0xFF)
        frame.extend([0x0D, 0x0A])
        return bytes(frame)


if __name__ == "__main__":
    server = MockMCUServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("服务端退出...")
        server.stop()
