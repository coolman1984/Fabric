#!/usr/bin/env python3
"""
Fabric Network Bypass - VPN Edition

This version integrates free VPN services to bypass YouTube rate limiting.
Supports:
- Windscribe (10GB free/month)
- ProtonVPN (Unlimited free, limited servers)
- OpenVPN configs (manual)

The app will:
1. Check if you have VPN installed
2. Help you install if needed
3. Connect automatically to change your IP
4. Verify YouTube works
"""

import sys
import os
import json
import time
import subprocess
import webbrowser
import threading
import winreg
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime

# PySide6 imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QProgressBar, QTabWidget,
    QGroupBox, QComboBox, QFrame, QMessageBox, QListWidget,
    QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QObject, QThread, QTimer
from PySide6.QtGui import QFont, QColor

try:
    import requests
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests


# ============================================================================
# VPN DETECTION & CONTROL
# ============================================================================

@dataclass
class VPNStatus:
    installed: bool = False
    connected: bool = False
    name: str = ""
    ip_address: str = ""
    location: str = ""


class VPNManager:
    """Manage VPN connections for various providers."""
    
    # Known VPN program paths
    VPN_PATHS = {
        "Windscribe": [
            r"C:\Program Files\Windscribe\windscribe-cli.exe",
            r"C:\Program Files (x86)\Windscribe\windscribe-cli.exe",
        ],
        "ProtonVPN": [
            r"C:\Program Files\Proton\VPN\ProtonVPN.exe",
            r"C:\Program Files (x86)\Proton\VPN\ProtonVPN.exe",
        ],
        "NordVPN": [
            r"C:\Program Files\NordVPN\NordVPN.exe",
            r"C:\Program Files (x86)\NordVPN\NordVPN.exe",
        ],
        "ExpressVPN": [
            r"C:\Program Files\ExpressVPN\expressvpn-ui.exe",
        ],
        "OpenVPN": [
            r"C:\Program Files\OpenVPN\bin\openvpn.exe",
            r"C:\Program Files (x86)\OpenVPN\bin\openvpn.exe",
        ],
    }
    
    # Free VPN download links
    FREE_VPN_DOWNLOADS = {
        "Windscribe": {
            "url": "https://windscribe.com/download",
            "info": "10GB free/month, easy CLI control",
            "recommended": True
        },
        "ProtonVPN": {
            "url": "https://protonvpn.com/download",
            "info": "Unlimited free, but slower servers",
            "recommended": True
        },
    }
    
    def __init__(self):
        self.detected_vpn = None
        self.vpn_path = None
    
    def detect_installed_vpn(self) -> Tuple[Optional[str], Optional[str]]:
        """Detect which VPN is installed."""
        for vpn_name, paths in self.VPN_PATHS.items():
            for path in paths:
                if Path(path).exists():
                    self.detected_vpn = vpn_name
                    self.vpn_path = path
                    return vpn_name, path
        return None, None
    
    def get_current_ip(self) -> Tuple[str, str]:
        """Get current public IP and location."""
        try:
            response = requests.get("https://ipapi.co/json/", timeout=10)
            data = response.json()
            ip = data.get("ip", "Unknown")
            location = f"{data.get('city', '')}, {data.get('country_name', '')}"
            return ip, location.strip(", ")
        except:
            try:
                response = requests.get("https://api.ipify.org?format=json", timeout=10)
                return response.json().get("ip", "Unknown"), "Unknown"
            except:
                return "Unknown", "Unknown"
    
    def connect_windscribe(self, location: str = "best") -> Tuple[bool, str]:
        """Connect using Windscribe CLI."""
        if not self.vpn_path or "windscribe" not in self.vpn_path.lower():
            return False, "Windscribe not found"
        
        try:
            # Connect to specified location
            cmd = [self.vpn_path, "connect", location]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if "connected" in result.stdout.lower():
                return True, f"Connected to {location}"
            else:
                return False, result.stdout or result.stderr
        except subprocess.TimeoutExpired:
            return False, "Connection timed out"
        except Exception as e:
            return False, str(e)
    
    def disconnect_windscribe(self) -> Tuple[bool, str]:
        """Disconnect Windscribe."""
        if not self.vpn_path or "windscribe" not in self.vpn_path.lower():
            return False, "Windscribe not found"
        
        try:
            result = subprocess.run([self.vpn_path, "disconnect"], 
                                   capture_output=True, text=True, timeout=30)
            return True, "Disconnected"
        except Exception as e:
            return False, str(e)
    
    def get_windscribe_locations(self) -> List[str]:
        """Get available Windscribe locations."""
        return ["best", "US", "US-West", "US-East", "UK", "CA", "DE", "NL", "CH", "JP"]
    
    def test_youtube_access(self) -> Tuple[bool, str]:
        """Test if YouTube transcripts work."""
        try:
            # Quick test using youtube-transcript-api
            from youtube_transcript_api import YouTubeTranscriptApi
            ytt = YouTubeTranscriptApi()
            data = ytt.fetch("jNQXAC9IVRw")  # First YouTube video ever (short)
            if data:
                return True, "YouTube access works!"
        except Exception as e:
            error = str(e).lower()
            if "429" in error or "rate" in error or "blocking" in error:
                return False, "Still rate limited"
            return False, str(e)[:50]
        
        return False, "Unknown error"


# ============================================================================
# WORKER THREADS
# ============================================================================

class WorkerSignals(QObject):
    output = Signal(str)
    finished = Signal(bool, str)
    progress = Signal(str)
    ip_updated = Signal(str, str)


class IPCheckWorker(QThread):
    """Background worker to check IP."""
    signals = WorkerSignals()
    
    def __init__(self, vpn_manager: VPNManager):
        super().__init__()
        self.vpn = vpn_manager
    
    def run(self):
        ip, location = self.vpn.get_current_ip()
        self.signals.ip_updated.emit(ip, location)


class VPNConnectWorker(QThread):
    """Background worker to connect VPN."""
    signals = WorkerSignals()
    
    def __init__(self, vpn_manager: VPNManager, location: str = "best"):
        super().__init__()
        self.vpn = vpn_manager
        self.location = location
    
    def run(self):
        self.signals.output.emit(f"Connecting to {self.location}...")
        success, msg = self.vpn.connect_windscribe(self.location)
        
        if success:
            time.sleep(3)  # Wait for connection to stabilize
            ip, location = self.vpn.get_current_ip()
            self.signals.ip_updated.emit(ip, location)
            
            # Test YouTube
            self.signals.output.emit("Testing YouTube access...")
            yt_success, yt_msg = self.vpn.test_youtube_access()
            
            if yt_success:
                self.signals.finished.emit(True, f"Connected! YouTube works! IP: {ip}")
            else:
                self.signals.finished.emit(True, f"Connected (IP: {ip}) but YouTube still blocked. Try different server.")
        else:
            self.signals.finished.emit(False, msg)


class YouTubeTestWorker(QThread):
    """Background worker to test YouTube."""
    signals = WorkerSignals()
    
    def __init__(self, vpn_manager: VPNManager):
        super().__init__()
        self.vpn = vpn_manager
    
    def run(self):
        self.signals.output.emit("Testing YouTube transcript access...")
        success, msg = self.vpn.test_youtube_access()
        self.signals.finished.emit(success, msg)


# ============================================================================
# MAIN GUI
# ============================================================================

class VPNBypassGUI(QMainWindow):
    """Main VPN Bypass application window."""
    
    def __init__(self):
        super().__init__()
        self.vpn = VPNManager()
        self.setWindowTitle("Fabric Network Bypass - VPN Edition")
        self.setMinimumSize(750, 600)
        
        self.setup_ui()
        self.apply_theme()
        
        # Check VPN status on startup
        QTimer.singleShot(500, self.check_vpn_status)
    
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("🛡️ Fabric Network Bypass")
        header.setFont(QFont("Segoe UI", 22, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        subtitle = QLabel("VPN-Powered YouTube Unblocking")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #888; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # Status Panel
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout(status_group)
        
        # IP Address display
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("Your IP:"))
        self.ip_label = QLabel("Checking...")
        self.ip_label.setFont(QFont("Consolas", 12))
        self.ip_label.setStyleSheet("color: #4ade80; font-weight: bold;")
        ip_layout.addWidget(self.ip_label)
        ip_layout.addStretch()
        
        self.location_label = QLabel("")
        self.location_label.setStyleSheet("color: #888;")
        ip_layout.addWidget(self.location_label)
        status_layout.addLayout(ip_layout)
        
        # VPN Status
        vpn_status_layout = QHBoxLayout()
        vpn_status_layout.addWidget(QLabel("VPN Status:"))
        self.vpn_status_label = QLabel("Detecting...")
        self.vpn_status_label.setFont(QFont("Segoe UI", 11))
        vpn_status_layout.addWidget(self.vpn_status_label)
        vpn_status_layout.addStretch()
        status_layout.addLayout(vpn_status_layout)
        
        # YouTube Status
        yt_layout = QHBoxLayout()
        yt_layout.addWidget(QLabel("YouTube Access:"))
        self.youtube_status_label = QLabel("Not tested")
        self.youtube_status_label.setFont(QFont("Segoe UI", 11))
        yt_layout.addWidget(self.youtube_status_label)
        yt_layout.addStretch()
        
        self.test_yt_btn = QPushButton("Test Now")
        self.test_yt_btn.clicked.connect(self.test_youtube)
        self.test_yt_btn.setStyleSheet("padding: 5px 15px;")
        yt_layout.addWidget(self.test_yt_btn)
        status_layout.addLayout(yt_layout)
        
        layout.addWidget(status_group)
        
        # VPN Control Panel
        control_group = QGroupBox("VPN Control")
        control_layout = QVBoxLayout(control_group)
        
        # Install section (shown if no VPN)
        self.install_widget = QWidget()
        install_layout = QVBoxLayout(self.install_widget)
        install_layout.setContentsMargins(0, 0, 0, 0)
        
        install_label = QLabel("⚠️ No VPN detected. Install one of these free VPNs:")
        install_label.setStyleSheet("color: #f59e0b; font-weight: bold;")
        install_layout.addWidget(install_label)
        
        vpn_buttons_layout = QHBoxLayout()
        
        windscribe_btn = QPushButton("📥 Install Windscribe (Recommended)")
        windscribe_btn.clicked.connect(lambda: self.open_vpn_download("Windscribe"))
        windscribe_btn.setStyleSheet("padding: 12px 20px; background: #059669;")
        vpn_buttons_layout.addWidget(windscribe_btn)
        
        proton_btn = QPushButton("📥 Install ProtonVPN")
        proton_btn.clicked.connect(lambda: self.open_vpn_download("ProtonVPN"))
        proton_btn.setStyleSheet("padding: 12px 20px;")
        vpn_buttons_layout.addWidget(proton_btn)
        
        install_layout.addLayout(vpn_buttons_layout)
        
        refresh_btn = QPushButton("🔄 I've installed a VPN - Refresh")
        refresh_btn.clicked.connect(self.check_vpn_status)
        refresh_btn.setStyleSheet("padding: 8px;")
        install_layout.addWidget(refresh_btn)
        
        control_layout.addWidget(self.install_widget)
        
        # Connect section (shown if VPN installed)
        self.connect_widget = QWidget()
        connect_layout = QVBoxLayout(self.connect_widget)
        connect_layout.setContentsMargins(0, 0, 0, 0)
        
        server_layout = QHBoxLayout()
        server_layout.addWidget(QLabel("Server Location:"))
        self.location_combo = QComboBox()
        self.location_combo.addItems(["best", "US", "US-West", "US-East", "UK", "CA", "DE", "NL", "CH", "JP"])
        self.location_combo.setMinimumWidth(150)
        server_layout.addWidget(self.location_combo)
        server_layout.addStretch()
        connect_layout.addLayout(server_layout)
        
        btn_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("🔗 Connect VPN")
        self.connect_btn.clicked.connect(self.connect_vpn)
        self.connect_btn.setStyleSheet("padding: 15px 30px; font-size: 14px; background: #059669;")
        btn_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("⛔ Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_vpn)
        self.disconnect_btn.setStyleSheet("padding: 15px 30px; font-size: 14px;")
        btn_layout.addWidget(self.disconnect_btn)
        
        connect_layout.addLayout(btn_layout)
        
        self.connect_widget.hide()
        control_layout.addWidget(self.connect_widget)
        
        layout.addWidget(control_group)
        
        # Log Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 10))
        self.output.setMaximumHeight(150)
        self.output.setPlaceholderText("Activity log will appear here...")
        layout.addWidget(self.output)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setMaximumHeight(6)
        self.progress.hide()
        layout.addWidget(self.progress)
        
        # Action Buttons
        action_layout = QHBoxLayout()
        
        done_btn = QPushButton("✓ Done - Back to Fabric GUI")
        done_btn.clicked.connect(self.close)
        done_btn.setStyleSheet("padding: 12px 25px; font-size: 13px; background: #4f46e5;")
        action_layout.addWidget(done_btn)
        
        layout.addLayout(action_layout)
    
    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 1px solid #3a3a5a;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
            QTextEdit {
                background: #0d0d1a;
                border: 1px solid #3a3a5a;
                border-radius: 8px;
                padding: 10px;
                color: #a0a0a0;
            }
            QPushButton {
                background: #4f46e5;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #6366f1;
            }
            QPushButton:disabled {
                background: #3a3a5a;
                color: #666;
            }
            QComboBox {
                background: #2a2a3a;
                border: 1px solid #3a3a5a;
                border-radius: 4px;
                padding: 8px;
                color: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: #2a2a3a;
                border: 1px solid #3a3a5a;
                color: white;
                selection-background-color: #4f46e5;
            }
            QProgressBar {
                border: none;
                border-radius: 3px;
                background: #2a2a3a;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5, stop:1 #7c3aed);
                border-radius: 3px;
            }
        """)
    
    def log(self, message: str):
        self.output.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        self.output.verticalScrollBar().setValue(
            self.output.verticalScrollBar().maximum()
        )
    
    def check_vpn_status(self):
        self.log("Checking for installed VPNs...")
        
        # Check IP
        worker = IPCheckWorker(self.vpn)
        worker.signals.ip_updated.connect(self.update_ip_display)
        worker.start()
        self._ip_worker = worker  # Keep reference
        
        # Check installed VPN
        vpn_name, vpn_path = self.vpn.detect_installed_vpn()
        
        if vpn_name:
            self.log(f"✓ Found {vpn_name}")
            self.vpn_status_label.setText(f"✅ {vpn_name} installed")
            self.vpn_status_label.setStyleSheet("color: #4ade80;")
            self.install_widget.hide()
            self.connect_widget.show()
        else:
            self.log("⚠ No VPN detected")
            self.vpn_status_label.setText("❌ No VPN installed")
            self.vpn_status_label.setStyleSheet("color: #ef4444;")
            self.install_widget.show()
            self.connect_widget.hide()
    
    def update_ip_display(self, ip: str, location: str):
        self.ip_label.setText(ip)
        self.location_label.setText(f"📍 {location}")
        self.log(f"Current IP: {ip} ({location})")
    
    def open_vpn_download(self, vpn_name: str):
        info = self.vpn.FREE_VPN_DOWNLOADS.get(vpn_name, {})
        url = info.get("url", "")
        if url:
            self.log(f"Opening {vpn_name} download page...")
            webbrowser.open(url)
            
            QMessageBox.information(
                self,
                f"Install {vpn_name}",
                f"1. Download and install {vpn_name}\n"
                f"2. Create a free account\n"
                f"3. Return here and click 'Refresh'\n\n"
                f"Tip: {info.get('info', '')}"
            )
    
    def connect_vpn(self):
        location = self.location_combo.currentText()
        self.log(f"Connecting to {location}...")
        
        self.progress.show()
        self.connect_btn.setEnabled(False)
        
        worker = VPNConnectWorker(self.vpn, location)
        worker.signals.output.connect(self.log)
        worker.signals.ip_updated.connect(self.update_ip_display)
        worker.signals.finished.connect(self.on_vpn_connect_finished)
        worker.start()
        self._connect_worker = worker
    
    def on_vpn_connect_finished(self, success: bool, message: str):
        self.progress.hide()
        self.connect_btn.setEnabled(True)
        
        if success:
            self.log(f"✓ {message}")
            if "YouTube works" in message:
                self.youtube_status_label.setText("✅ Working!")
                self.youtube_status_label.setStyleSheet("color: #4ade80;")
            else:
                self.youtube_status_label.setText("⚠️ Still blocked - try another server")
                self.youtube_status_label.setStyleSheet("color: #f59e0b;")
        else:
            self.log(f"✗ Connection failed: {message}")
    
    def disconnect_vpn(self):
        self.log("Disconnecting VPN...")
        success, msg = self.vpn.disconnect_windscribe()
        if success:
            self.log("✓ Disconnected")
            # Refresh IP
            worker = IPCheckWorker(self.vpn)
            worker.signals.ip_updated.connect(self.update_ip_display)
            worker.start()
            self._ip_worker = worker
        else:
            self.log(f"✗ {msg}")
    
    def test_youtube(self):
        self.log("Testing YouTube access...")
        self.test_yt_btn.setEnabled(False)
        self.youtube_status_label.setText("Testing...")
        self.youtube_status_label.setStyleSheet("color: #888;")
        
        worker = YouTubeTestWorker(self.vpn)
        worker.signals.finished.connect(self.on_youtube_test_finished)
        worker.start()
        self._yt_worker = worker
    
    def on_youtube_test_finished(self, success: bool, message: str):
        self.test_yt_btn.setEnabled(True)
        
        if success:
            self.log(f"✓ YouTube works: {message}")
            self.youtube_status_label.setText("✅ Working!")
            self.youtube_status_label.setStyleSheet("color: #4ade80;")
        else:
            self.log(f"✗ YouTube blocked: {message}")
            self.youtube_status_label.setText(f"❌ {message}")
            self.youtube_status_label.setStyleSheet("color: #ef4444;")


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    app = QApplication(sys.argv)
    window = VPNBypassGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
