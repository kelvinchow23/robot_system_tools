"""
Network utilities for UR3 Robot Arm Camera System
Clean implementations of file transfer and logging functions
"""

import logging
import socket
from typing import Optional

def setup_logger(name: str, level: int = logging.INFO, format_str: str = None) -> logging.Logger:
    """Setup a logger with specified configuration"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            format_str or '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def send_file_name(conn: socket.socket, filename: str, logger: logging.Logger) -> bool:
    """Send filename over socket connection"""
    try:
        filename_bytes = filename.encode('utf-8')
        filename_length = len(filename_bytes)
        conn.sendall(filename_length.to_bytes(4, byteorder='big'))
        conn.sendall(filename_bytes)
        logger.debug(f"Sent filename: {filename}")
        return True
    except Exception as e:
        logger.error(f"Error sending filename: {e}")
        return False

def receive_file_name(conn: socket.socket, logger: logging.Logger) -> Optional[str]:
    """Receive filename from socket connection"""
    try:
        length_bytes = conn.recv(4)
        if len(length_bytes) != 4:
            return None
        length = int.from_bytes(length_bytes, byteorder='big')
        filename_bytes = conn.recv(length)
        filename = filename_bytes.decode('utf-8')
        logger.debug(f"Received filename: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error receiving filename: {e}")
        return None

def send_file_size(conn: socket.socket, size: int, logger: logging.Logger) -> bool:
    """Send file size over socket connection"""
    try:
        size_str = str(size)
        size_bytes = size_str.encode('utf-8')
        size_length = len(size_bytes)
        conn.sendall(size_length.to_bytes(4, byteorder='big'))
        conn.sendall(size_bytes)
        logger.debug(f"Sent file size: {size}")
        return True
    except Exception as e:
        logger.error(f"Error sending file size: {e}")
        return False

def receive_file_size(conn: socket.socket, logger: logging.Logger) -> Optional[int]:
    """Receive file size from socket connection"""
    try:
        length_bytes = conn.recv(4)
        if len(length_bytes) != 4:
            return None
        length = int.from_bytes(length_bytes, byteorder='big')
        size_bytes = conn.recv(length)
        size_str = size_bytes.decode('utf-8')
        size = int(size_str)
        logger.debug(f"Received file size: {size}")
        return size
    except Exception as e:
        logger.error(f"Error receiving file size: {e}")
        return None

def get_local_ip() -> str:
    """Get the local IP address of this machine"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
