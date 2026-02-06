#!/usr/bin/env python3
"""
Fabric Network Bypass Tool
A PySide6 application for configuring proxies, Tor, and other network bypass solutions
to solve YouTube rate limiting issues.

Features:
1. Manual Proxy Configuration (HTTP, HTTPS, SOCKS5)
2. Tor Integration (automatic SOCKS5 proxy via Tor)
3. Free Proxy List Fetcher & Tester
4. Direct integration with Fabric YouTube transcript
"""

import sys
import os
import json
import socket
import subprocess
import threading
import requests
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit,
    QGroupBox, QFormLayout, QSpinBox, QCheckBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QMessageBox,
    QSplitter, QFrame, QStatusBar
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette, QIcon


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ProxyConfig:
    """Proxy configuration."""
    host: str
    port: int
    proxy_type: str = "http"  # http, https, socks5
    username: Optional[str] = None
    password: Optional[str] = None
    
    def to_url(self) -> str:
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"{self.proxy_type}://{auth}{self.host}:{self.port}"
    
    def to_dict(self) -> dict:
        return {
            "http": self.to_url(),
            "https": self.to_url(),
        }


# ============================================================================
# WORKER THREADS
# ============================================================================

class ProxyTestWorker(QThread):
    """Worker thread for testing proxies."""
    progress = Signal(int, str)  # index, status
    finished = Signal(list)  # list of working proxies
    
    def __init__(self, proxies: List[dict]):
        super().__init__()
        self.proxies = proxies
        self.working = []
        
    def run(self):
        for i, proxy in enumerate(self.proxies):
            try:
                proxy_url = f"{proxy['type']}://{proxy['host']}:{proxy['port']}"
                proxies = {"http": proxy_url, "https": proxy_url}
                
                # Quick test with a lightweight URL
                response = requests.get(
                    "https://www.google.com",
                    proxies=proxies,
                    timeout=10
                )
                if response.status_code == 200:
                    proxy['status'] = 'Working'
                    proxy['latency'] = response.elapsed.total_seconds() * 1000
                    self.working.append(proxy)
                    self.progress.emit(i, "✓ Working")
                else:
                    self.progress.emit(i, "✗ Failed")
            except Exception as e:
                self.progress.emit(i, f"✗ {str(e)[:30]}")
        
        self.finished.emit(self.working)


class YouTubeTestWorker(QThread):
    """Worker thread for testing YouTube transcript with proxy."""
    result = Signal(bool, str)  # success, message
    
    def __init__(self, proxy_config: Optional[ProxyConfig], video_id: str):
        super().__init__()
        self.proxy_config = proxy_config
        self.video_id = video_id
        
    def run(self):
        try:
            # Build environment with proxy
            env = os.environ.copy()
            if self.proxy_config:
                env['HTTP_PROXY'] = self.proxy_config.to_url()
                env['HTTPS_PROXY'] = self.proxy_config.to_url()
            
            # Find the transcript script
            script_paths = [
                Path("src-tauri/resources/youtube_transcript.py"),
                Path(__file__).parent / "youtube_transcript.py",
            ]
            
            script_path = None
            for p in script_paths:
                if p.exists():
                    script_path = p
                    break
            
            if not script_path:
                self.result.emit(False, "YouTube transcript script not found")
                return
            
            # Run the script
            result = subprocess.run(
                [sys.executable, str(script_path), "--url", self.video_id],
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )
            
            output = json.loads(result.stdout)
            if "error" in output:
                self.result.emit(False, output["error"])
            else:
                transcript = output.get("transcript", "")
                self.result.emit(True, f"Success! Got {len(transcript)} characters")
                
        except subprocess.TimeoutExpired:
            self.result.emit(False, "Request timed out")
        except json.JSONDecodeError:
            self.result.emit(False, f"Invalid response: {result.stdout[:100]}")
        except Exception as e:
            self.result.emit(False, str(e))


class FreeProxyFetcher(QThread):
    """Fetches free proxies from public lists."""
    proxies_found = Signal(list)
    status = Signal(str)
    
    def run(self):
        proxies = []
        
        # Try multiple free proxy sources
        sources = [
            self.fetch_from_proxylist,
            self.fetch_from_github,
        ]
        
        for fetch_func in sources:
            try:
                self.status.emit(f"Fetching from {fetch_func.__name__}...")
                new_proxies = fetch_func()
                proxies.extend(new_proxies)
            except Exception as e:
                self.status.emit(f"Error: {str(e)[:50]}")
        
        self.status.emit(f"Found {len(proxies)} proxies")
        self.proxies_found.emit(proxies)
    
    def fetch_from_proxylist(self) -> List[dict]:
        """Fetch from free-proxy-list API."""
        proxies = []
        try:
            # Public proxy list API
            response = requests.get(
                "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
                timeout=10
            )
            for line in response.text.strip().split('\n'):
                if ':' in line:
                    host, port = line.strip().split(':')
                    proxies.append({
                        'host': host,
                        'port': int(port),
                        'type': 'http',
                        'status': 'Unknown',
                        'source': 'ProxyScrape'
                    })
        except:
            pass
        return proxies[:50]  # Limit to 50
    
    def fetch_from_github(self) -> List[dict]:
        """Fetch from GitHub proxy lists."""
        proxies = []
        try:
            # Popular GitHub proxy list
            response = requests.get(
                "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
                timeout=10
            )
            for line in response.text.strip().split('\n')[:50]:
                if ':' in line:
                    host, port = line.strip().split(':')
                    proxies.append({
                        'host': host,
                        'port': int(port),
                        'type': 'http',
                        'status': 'Unknown',
                        'source': 'GitHub'
                    })
        except:
            pass
        return proxies


# ============================================================================
# MAIN WINDOW
# ============================================================================

class NetworkBypassTool(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fabric Network Bypass Tool")
        self.setMinimumSize(900, 700)
        self.current_proxy: Optional[ProxyConfig] = None
        self.free_proxies: List[dict] = []
        
        self.setup_ui()
        self.apply_dark_theme()
        self.load_settings()
        
    def setup_ui(self):
        """Setup the user interface."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QLabel("🌐 Fabric Network Bypass Tool")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Status bar at top
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("background: #2a2a3a; border-radius: 8px; padding: 10px;")
        status_layout = QHBoxLayout(self.status_frame)
        
        self.ip_label = QLabel("Current IP: Checking...")
        self.ip_label.setStyleSheet("color: #888;")
        status_layout.addWidget(self.ip_label)
        
        self.proxy_status = QLabel("Proxy: Not configured")
        self.proxy_status.setStyleSheet("color: #f59e0b;")
        status_layout.addWidget(self.proxy_status)
        
        refresh_ip_btn = QPushButton("Refresh IP")
        refresh_ip_btn.clicked.connect(self.check_current_ip)
        status_layout.addWidget(refresh_ip_btn)
        
        layout.addWidget(self.status_frame)
        
        # Tab widget
        tabs = QTabWidget()
        tabs.addTab(self.create_manual_proxy_tab(), "📡 Manual Proxy")
        tabs.addTab(self.create_free_proxy_tab(), "🆓 Free Proxies")
        tabs.addTab(self.create_tor_tab(), "🧅 Tor Network")
        tabs.addTab(self.create_test_tab(), "🧪 Test YouTube")
        layout.addWidget(tabs)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Check current IP on startup
        QTimer.singleShot(500, self.check_current_ip)
    
    def create_manual_proxy_tab(self) -> QWidget:
        """Create manual proxy configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Proxy configuration group
        config_group = QGroupBox("Proxy Configuration")
        config_layout = QFormLayout(config_group)
        
        self.proxy_type = QComboBox()
        self.proxy_type.addItems(["http", "https", "socks5"])
        config_layout.addRow("Type:", self.proxy_type)
        
        self.proxy_host = QLineEdit()
        self.proxy_host.setPlaceholderText("e.g., proxy.example.com or 192.168.1.1")
        config_layout.addRow("Host:", self.proxy_host)
        
        self.proxy_port = QSpinBox()
        self.proxy_port.setRange(1, 65535)
        self.proxy_port.setValue(8080)
        config_layout.addRow("Port:", self.proxy_port)
        
        self.proxy_user = QLineEdit()
        self.proxy_user.setPlaceholderText("Optional")
        config_layout.addRow("Username:", self.proxy_user)
        
        self.proxy_pass = QLineEdit()
        self.proxy_pass.setPlaceholderText("Optional")
        self.proxy_pass.setEchoMode(QLineEdit.Password)
        config_layout.addRow("Password:", self.proxy_pass)
        
        layout.addWidget(config_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Apply Proxy")
        apply_btn.setStyleSheet("background: #4f46e5; color: white; padding: 10px 20px;")
        apply_btn.clicked.connect(self.apply_manual_proxy)
        btn_layout.addWidget(apply_btn)
        
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self.test_current_proxy)
        btn_layout.addWidget(test_btn)
        
        clear_btn = QPushButton("Clear Proxy")
        clear_btn.clicked.connect(self.clear_proxy)
        btn_layout.addWidget(clear_btn)
        
        layout.addLayout(btn_layout)
        
        # Info text
        info = QTextEdit()
        info.setReadOnly(True)
        info.setMaximumHeight(150)
        info.setHtml("""
        <h3>How to Use</h3>
        <p>Configure a proxy server to route your YouTube requests through a different IP address.</p>
        <ul>
            <li><b>HTTP/HTTPS Proxy:</b> Standard web proxy</li>
            <li><b>SOCKS5 Proxy:</b> More versatile, works with more protocols</li>
        </ul>
        <p>Popular proxy providers: BrightData, Oxylabs, SmartProxy</p>
        """)
        layout.addWidget(info)
        
        layout.addStretch()
        return widget
    
    def create_free_proxy_tab(self) -> QWidget:
        """Create free proxy list tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Fetch button
        btn_layout = QHBoxLayout()
        
        fetch_btn = QPushButton("🔍 Fetch Free Proxies")
        fetch_btn.setStyleSheet("background: #059669; color: white; padding: 10px 20px;")
        fetch_btn.clicked.connect(self.fetch_free_proxies)
        btn_layout.addWidget(fetch_btn)
        
        test_all_btn = QPushButton("🧪 Test All Proxies")
        test_all_btn.clicked.connect(self.test_all_proxies)
        btn_layout.addWidget(test_all_btn)
        
        self.fetch_status = QLabel("")
        btn_layout.addWidget(self.fetch_status)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Proxy table
        self.proxy_table = QTableWidget()
        self.proxy_table.setColumnCount(5)
        self.proxy_table.setHorizontalHeaderLabels(["Host", "Port", "Type", "Status", "Source"])
        self.proxy_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.proxy_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.proxy_table.doubleClicked.connect(self.use_selected_proxy)
        layout.addWidget(self.proxy_table)
        
        # Use selected button
        use_btn = QPushButton("Use Selected Proxy")
        use_btn.clicked.connect(self.use_selected_proxy)
        layout.addWidget(use_btn)
        
        # Warning
        warning = QLabel("⚠️ Free proxies may be slow, unreliable, or insecure. Use at your own risk.")
        warning.setStyleSheet("color: #f59e0b;")
        layout.addWidget(warning)
        
        return widget
    
    def create_tor_tab(self) -> QWidget:
        """Create Tor network tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tor info
        info_group = QGroupBox("About Tor")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel("""
Tor (The Onion Router) is a free, open-source network that provides anonymity.
It routes your traffic through multiple servers worldwide.

<b>How it works:</b>
1. Install Tor Browser or Tor Expert Bundle
2. Tor runs a local SOCKS5 proxy on port 9050
3. Configure this tool to use 127.0.0.1:9050
        """)
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        layout.addWidget(info_group)
        
        # Tor configuration
        config_group = QGroupBox("Tor Configuration")
        config_layout = QFormLayout(config_group)
        
        self.tor_host = QLineEdit("127.0.0.1")
        config_layout.addRow("Tor Host:", self.tor_host)
        
        self.tor_port = QSpinBox()
        self.tor_port.setRange(1, 65535)
        self.tor_port.setValue(9050)
        config_layout.addRow("Tor Port:", self.tor_port)
        
        layout.addWidget(config_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        check_tor_btn = QPushButton("Check Tor Status")
        check_tor_btn.clicked.connect(self.check_tor_status)
        btn_layout.addWidget(check_tor_btn)
        
        use_tor_btn = QPushButton("Use Tor Proxy")
        use_tor_btn.setStyleSheet("background: #7c3aed; color: white;")
        use_tor_btn.clicked.connect(self.use_tor_proxy)
        btn_layout.addWidget(use_tor_btn)
        
        layout.addLayout(btn_layout)
        
        # Tor status
        self.tor_status = QTextEdit()
        self.tor_status.setReadOnly(True)
        self.tor_status.setMaximumHeight(150)
        layout.addWidget(self.tor_status)
        
        # Download link
        download_label = QLabel('<a href="https://www.torproject.org/download/">Download Tor Browser</a>')
        download_label.setOpenExternalLinks(True)
        layout.addWidget(download_label)
        
        layout.addStretch()
        return widget
    
    def create_test_tab(self) -> QWidget:
        """Create YouTube test tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Test configuration
        config_group = QGroupBox("Test YouTube Transcript")
        config_layout = QFormLayout(config_group)
        
        self.test_video = QLineEdit("dQw4w9WgXcQ")
        self.test_video.setPlaceholderText("YouTube video ID or URL")
        config_layout.addRow("Video:", self.test_video)
        
        layout.addWidget(config_group)
        
        # Current proxy display
        self.current_proxy_display = QLabel("Current Proxy: None")
        self.current_proxy_display.setStyleSheet("padding: 10px; background: #2a2a3a; border-radius: 5px;")
        layout.addWidget(self.current_proxy_display)
        
        # Run test button
        self.test_youtube_btn = QPushButton("🧪 Test YouTube Transcript")
        self.test_youtube_btn.setStyleSheet("background: #4f46e5; color: white; padding: 15px; font-size: 14px;")
        self.test_youtube_btn.clicked.connect(self.test_youtube_transcript)
        layout.addWidget(self.test_youtube_btn)
        
        # Progress
        self.test_progress = QProgressBar()
        self.test_progress.setTextVisible(False)
        self.test_progress.hide()
        layout.addWidget(self.test_progress)
        
        # Results
        self.test_results = QTextEdit()
        self.test_results.setReadOnly(True)
        layout.addWidget(self.test_results)
        
        return widget
    
    # ========================================================================
    # ACTIONS
    # ========================================================================
    
    def apply_dark_theme(self):
        """Apply dark theme to the application."""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 1px solid #3a3a5a;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QSpinBox, QComboBox {
                background: #2a2a3a;
                border: 1px solid #3a3a5a;
                border-radius: 5px;
                padding: 8px;
                color: #e0e0e0;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #4f46e5;
            }
            QPushButton {
                background: #3a3a5a;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: #4a4a6a;
            }
            QTableWidget {
                background: #2a2a3a;
                border: 1px solid #3a3a5a;
                border-radius: 5px;
                gridline-color: #3a3a5a;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background: #3a3a5a;
                padding: 8px;
                border: none;
            }
            QTextEdit {
                background: #2a2a3a;
                border: 1px solid #3a3a5a;
                border-radius: 5px;
            }
            QTabWidget::pane {
                border: 1px solid #3a3a5a;
                border-radius: 5px;
            }
            QTabBar::tab {
                background: #2a2a3a;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background: #4f46e5;
            }
            QProgressBar {
                border: none;
                border-radius: 5px;
                background: #2a2a3a;
                height: 10px;
            }
            QProgressBar::chunk {
                background: #4f46e5;
                border-radius: 5px;
            }
        """)
    
    def check_current_ip(self):
        """Check current public IP address."""
        def fetch_ip():
            try:
                response = requests.get("https://api.ipify.org?format=json", timeout=5)
                ip = response.json()["ip"]
                return ip
            except:
                return "Unknown"
        
        def update_ui(ip):
            self.ip_label.setText(f"Current IP: {ip}")
            self.ip_label.setStyleSheet("color: #4ade80;")
        
        # Run in thread
        thread = threading.Thread(target=lambda: update_ui(fetch_ip()))
        thread.start()
    
    def apply_manual_proxy(self):
        """Apply manually configured proxy."""
        host = self.proxy_host.text().strip()
        if not host:
            QMessageBox.warning(self, "Error", "Please enter a proxy host")
            return
        
        self.current_proxy = ProxyConfig(
            host=host,
            port=self.proxy_port.value(),
            proxy_type=self.proxy_type.currentText(),
            username=self.proxy_user.text() or None,
            password=self.proxy_pass.text() or None
        )
        
        self.update_proxy_display()
        self.save_settings()
        self.statusBar().showMessage(f"Proxy applied: {self.current_proxy.to_url()}")
    
    def test_current_proxy(self):
        """Test the currently configured proxy."""
        if not self.current_proxy:
            QMessageBox.warning(self, "Error", "No proxy configured")
            return
        
        self.statusBar().showMessage("Testing proxy...")
        
        def test():
            try:
                response = requests.get(
                    "https://api.ipify.org?format=json",
                    proxies=self.current_proxy.to_dict(),
                    timeout=15
                )
                ip = response.json()["ip"]
                return True, f"Proxy working! IP: {ip}"
            except Exception as e:
                return False, str(e)
        
        def show_result(result):
            success, message = result
            if success:
                QMessageBox.information(self, "Success", message)
                self.proxy_status.setText(f"Proxy: ✓ Active")
                self.proxy_status.setStyleSheet("color: #4ade80;")
            else:
                QMessageBox.warning(self, "Failed", f"Proxy test failed: {message}")
        
        # Run in thread
        thread = threading.Thread(target=lambda: show_result(test()))
        thread.start()
    
    def clear_proxy(self):
        """Clear proxy configuration."""
        self.current_proxy = None
        self.proxy_host.clear()
        self.proxy_user.clear()
        self.proxy_pass.clear()
        self.update_proxy_display()
        self.proxy_status.setText("Proxy: Not configured")
        self.proxy_status.setStyleSheet("color: #f59e0b;")
        self.statusBar().showMessage("Proxy cleared")
    
    def update_proxy_display(self):
        """Update proxy display in test tab."""
        if self.current_proxy:
            self.current_proxy_display.setText(f"Current Proxy: {self.current_proxy.to_url()}")
            self.current_proxy_display.setStyleSheet("padding: 10px; background: #1e3a5f; border-radius: 5px; color: #4ade80;")
        else:
            self.current_proxy_display.setText("Current Proxy: None (Direct connection)")
            self.current_proxy_display.setStyleSheet("padding: 10px; background: #2a2a3a; border-radius: 5px;")
    
    def fetch_free_proxies(self):
        """Fetch free proxies from public lists."""
        self.fetch_status.setText("Fetching...")
        self.proxy_table.setRowCount(0)
        
        self.fetcher = FreeProxyFetcher()
        self.fetcher.status.connect(lambda s: self.fetch_status.setText(s))
        self.fetcher.proxies_found.connect(self.display_proxies)
        self.fetcher.start()
    
    def display_proxies(self, proxies: List[dict]):
        """Display fetched proxies in table."""
        self.free_proxies = proxies
        self.proxy_table.setRowCount(len(proxies))
        
        for i, proxy in enumerate(proxies):
            self.proxy_table.setItem(i, 0, QTableWidgetItem(proxy['host']))
            self.proxy_table.setItem(i, 1, QTableWidgetItem(str(proxy['port'])))
            self.proxy_table.setItem(i, 2, QTableWidgetItem(proxy['type']))
            self.proxy_table.setItem(i, 3, QTableWidgetItem(proxy['status']))
            self.proxy_table.setItem(i, 4, QTableWidgetItem(proxy.get('source', 'Unknown')))
    
    def test_all_proxies(self):
        """Test all fetched proxies."""
        if not self.free_proxies:
            QMessageBox.warning(self, "Error", "No proxies to test. Fetch proxies first.")
            return
        
        self.statusBar().showMessage("Testing proxies...")
        
        self.tester = ProxyTestWorker(self.free_proxies)
        self.tester.progress.connect(self.update_proxy_status)
        self.tester.finished.connect(self.proxy_test_complete)
        self.tester.start()
    
    def update_proxy_status(self, index: int, status: str):
        """Update proxy status in table."""
        if index < self.proxy_table.rowCount():
            self.proxy_table.setItem(index, 3, QTableWidgetItem(status))
    
    def proxy_test_complete(self, working: List[dict]):
        """Handle proxy test completion."""
        self.statusBar().showMessage(f"Testing complete: {len(working)} working proxies")
        QMessageBox.information(self, "Complete", f"Found {len(working)} working proxies!")
    
    def use_selected_proxy(self):
        """Use the selected proxy from the table."""
        row = self.proxy_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a proxy from the table")
            return
        
        host = self.proxy_table.item(row, 0).text()
        port = int(self.proxy_table.item(row, 1).text())
        proxy_type = self.proxy_table.item(row, 2).text()
        
        self.current_proxy = ProxyConfig(host=host, port=port, proxy_type=proxy_type)
        self.update_proxy_display()
        self.statusBar().showMessage(f"Using proxy: {self.current_proxy.to_url()}")
    
    def check_tor_status(self):
        """Check if Tor is running."""
        host = self.tor_host.text()
        port = self.tor_port.value()
        
        self.tor_status.clear()
        self.tor_status.append("Checking Tor connection...")
        
        def check():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    # Try to get IP through Tor
                    try:
                        proxies = {"http": f"socks5://{host}:{port}", "https": f"socks5://{host}:{port}"}
                        response = requests.get("https://check.torproject.org/api/ip", proxies=proxies, timeout=15)
                        data = response.json()
                        return True, f"Tor is running!\nIP: {data.get('IP', 'Unknown')}\nIs Tor: {data.get('IsTor', False)}"
                    except:
                        return True, "Tor port is open but couldn't verify connection"
                else:
                    return False, "Tor is not running. Please start Tor Browser or Tor service."
            except Exception as e:
                return False, str(e)
        
        def show_result(result):
            success, message = result
            self.tor_status.clear()
            if success:
                self.tor_status.setStyleSheet("color: #4ade80;")
            else:
                self.tor_status.setStyleSheet("color: #f87171;")
            self.tor_status.append(message)
        
        thread = threading.Thread(target=lambda: show_result(check()))
        thread.start()
    
    def use_tor_proxy(self):
        """Configure to use Tor as proxy."""
        host = self.tor_host.text()
        port = self.tor_port.value()
        
        self.current_proxy = ProxyConfig(host=host, port=port, proxy_type="socks5")
        self.update_proxy_display()
        self.statusBar().showMessage(f"Using Tor proxy: {self.current_proxy.to_url()}")
    
    def test_youtube_transcript(self):
        """Test YouTube transcript with current proxy."""
        video = self.test_video.text().strip()
        if not video:
            QMessageBox.warning(self, "Error", "Please enter a video ID or URL")
            return
        
        self.test_youtube_btn.setEnabled(False)
        self.test_progress.show()
        self.test_progress.setRange(0, 0)  # Indeterminate
        self.test_results.clear()
        self.test_results.append(f"Testing YouTube transcript for: {video}")
        self.test_results.append(f"Using proxy: {self.current_proxy.to_url() if self.current_proxy else 'Direct connection'}")
        self.test_results.append("Please wait...")
        
        self.yt_worker = YouTubeTestWorker(self.current_proxy, video)
        self.yt_worker.result.connect(self.youtube_test_complete)
        self.yt_worker.start()
    
    def youtube_test_complete(self, success: bool, message: str):
        """Handle YouTube test completion."""
        self.test_youtube_btn.setEnabled(True)
        self.test_progress.hide()
        
        self.test_results.append("\n" + "="*50)
        if success:
            self.test_results.append(f"✅ SUCCESS: {message}")
            self.test_results.setStyleSheet("color: #4ade80;")
        else:
            self.test_results.append(f"❌ FAILED: {message}")
            self.test_results.setStyleSheet("color: #f87171;")
    
    def save_settings(self):
        """Save current settings to file."""
        settings = {
            "proxy": {
                "host": self.current_proxy.host if self.current_proxy else "",
                "port": self.current_proxy.port if self.current_proxy else 8080,
                "type": self.current_proxy.proxy_type if self.current_proxy else "http",
            } if self.current_proxy else None
        }
        
        settings_path = Path(__file__).parent / "network_bypass_settings.json"
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=2)
    
    def load_settings(self):
        """Load settings from file."""
        settings_path = Path(__file__).parent / "network_bypass_settings.json"
        if settings_path.exists():
            try:
                with open(settings_path) as f:
                    settings = json.load(f)
                
                if settings.get("proxy"):
                    p = settings["proxy"]
                    self.current_proxy = ProxyConfig(
                        host=p["host"],
                        port=p["port"],
                        proxy_type=p["type"]
                    )
                    self.proxy_host.setText(p["host"])
                    self.proxy_port.setValue(p["port"])
                    self.proxy_type.setCurrentText(p["type"])
                    self.update_proxy_display()
            except:
                pass


# ============================================================================
# MAIN
# ============================================================================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Fabric Network Bypass Tool")
    
    window = NetworkBypassTool()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
