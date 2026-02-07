"""串口管理工具"""

import subprocess
import time
import logging
import psutil
from typing import Optional, List

logger = logging.getLogger(__name__)


class PortManager:
    """管理串口访问与占用冲突"""
    
    def __init__(self):
        self.monitored_ports = {}  # 端口 -> 进程信息
        logger.debug("PortManager initialized")
    
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
                                logger.debug(f"Found process using {port}: {proc.info['name']} (PID: {proc.info['pid']})")
                                break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"Error finding port users: {e}")
        
        return users
    
    def close_port_users(self, port: str, exclude_pids: List[int] = None) -> bool:
        """关闭占用该串口的进程（可排除指定 PID）"""
        exclude_pids = exclude_pids or []
        users = self.find_port_users(port)
        
        if not users:
            logger.debug(f"No processes using {port}")
            return True
        
        logger.info(f"Found {len(users)} process(es) using {port}")
        
        for user in users:
            if user['pid'] in exclude_pids:
                logger.debug(f"Skipping excluded PID: {user['pid']}")
                continue
            
            try:
                logger.info(f"Closing {user['name']} (PID: {user['pid']})")
                proc = user['process']
                proc.terminate()
                
                # 等待进程正常退出
                try:
                    proc.wait(timeout=2)
                except psutil.TimeoutExpired:
                    # 未退出则强制结束
                    logger.warning(f"Force killing {user['name']}")
                    proc.kill()
                    proc.wait(timeout=1)
                
                logger.info(f"Closed {user['name']}")
            except Exception as e:
                logger.error(f"Failed to close {user['name']}: {e}")
        
        # 稍等以便串口释放
        time.sleep(0.5)
        return True
    
    def is_port_available(self, port: str) -> bool:
        """检查串口是否可用"""
        import serial
        try:
            ser = serial.Serial(port, 9600, timeout=0.1)
            ser.close()
            logger.debug(f"Port {port} is available")
            return True
        except serial.SerialException:
            logger.debug(f"Port {port} is not available")
            return False
    
    def wait_for_port_available(self, port: str, timeout: int = 5) -> bool:
        """等待串口变为可用"""
        logger.debug(f"Waiting for {port} to become available (timeout: {timeout}s)")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_port_available(port):
                logger.info(f"Port {port} is now available")
                return True
            time.sleep(0.2)
        
        logger.warning(f"Port {port} did not become available within {timeout}s")
        return False
    
    def prepare_port_for_upload(self, port: str) -> bool:
        """为上传准备串口：关闭占用进程并等待可用"""
        logger.info(f"Preparing {port} for upload...")
        
        # 关闭占用该串口的进程
        self.close_port_users(port)
        
        # 等待串口可用
        if self.wait_for_port_available(port, timeout=5):
            logger.info(f"{port} is ready for upload")
            return True
        else:
            logger.warning(f"{port} is still busy after preparation")
            return False
    
    def reset_port(self, port: str) -> bool:
        """重置串口"""
        import serial
        try:
            logger.debug(f"Resetting port {port}")
            # 打开再关闭以实现复位
            ser = serial.Serial(port, 1200, timeout=0.1)
            ser.setDTR(False)
            time.sleep(0.1)
            ser.setDTR(True)
            ser.close()
            time.sleep(0.5)
            logger.info(f"Port {port} reset successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to reset port {port}: {e}")
            return False
