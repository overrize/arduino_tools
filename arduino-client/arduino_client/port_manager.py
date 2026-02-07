"""串口管理工具"""
import time
import logging
import psutil
from typing import List, Optional

log = logging.getLogger("arduino_client")


class PortManager:
    """管理串口访问与占用冲突"""
    
    def __init__(self):
        self.monitored_ports = {}  # 端口 -> 进程信息
        log.debug("PortManager 已初始化")
    
    def find_port_users(self, port: str) -> List[dict]:
        """查找占用指定串口的进程"""
        users = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    connections = proc.info.get('connections', [])
                    if connections:
                        for conn in connections:
                            # 判断该进程是否占用该串口
                            if hasattr(conn, 'laddr') and port.upper() in str(conn).upper():
                                users.append({
                                    'pid': proc.info['pid'],
                                    'name': proc.info['name'],
                                    'process': proc
                                })
                                log.debug(f"发现占用 {port} 的进程: {proc.info['name']} (PID: {proc.info['pid']})")
                                break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            log.error(f"查找串口占用进程错误: {e}")
        
        return users
    
    def close_port_users(self, port: str, exclude_pids: List[int] = None) -> bool:
        """关闭占用该串口的进程（可排除指定 PID）"""
        exclude_pids = exclude_pids or []
        users = self.find_port_users(port)
        
        if not users:
            log.debug(f"无进程占用 {port}")
            return True
        
        log.info(f"发现 {len(users)} 个进程占用 {port}")
        
        for user in users:
            if user['pid'] in exclude_pids:
                log.debug(f"跳过排除的 PID: {user['pid']}")
                continue
            
            try:
                log.info(f"关闭 {user['name']} (PID: {user['pid']})")
                proc = user['process']
                proc.terminate()
                
                # 等待进程正常退出
                try:
                    proc.wait(timeout=2)
                except psutil.TimeoutExpired:
                    # 未退出则强制结束
                    log.warning(f"强制结束 {user['name']}")
                    proc.kill()
                    proc.wait(timeout=1)
                
                log.info(f"已关闭 {user['name']}")
            except Exception as e:
                log.error(f"关闭 {user['name']} 失败: {e}")
        
        # 稍等以便串口释放
        time.sleep(0.5)
        return True
    
    def is_port_available(self, port: str) -> bool:
        """检查串口是否可用"""
        try:
            import serial
            ser = serial.Serial(port, 9600, timeout=0.1)
            ser.close()
            log.debug(f"串口 {port} 可用")
            return True
        except Exception:
            log.debug(f"串口 {port} 不可用")
            return False
    
    def wait_for_port_available(self, port: str, timeout: int = 5) -> bool:
        """等待串口变为可用"""
        log.debug(f"等待 {port} 变为可用（超时: {timeout}秒）")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_port_available(port):
                log.info(f"串口 {port} 现在可用")
                return True
            time.sleep(0.2)
        
        log.warning(f"串口 {port} 在 {timeout} 秒内未变为可用")
        return False
    
    def prepare_port_for_upload(self, port: str) -> bool:
        """为上传准备串口：关闭占用进程并等待可用"""
        log.info(f"准备串口 {port} 用于上传...")
        
        # 关闭占用该串口的进程
        self.close_port_users(port)
        
        # 等待串口可用
        if self.wait_for_port_available(port, timeout=5):
            log.info(f"{port} 已准备好用于上传")
            return True
        else:
            log.warning(f"{port} 在准备后仍然忙碌")
            return False
