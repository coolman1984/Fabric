#!/usr/bin/env python3
"""
Fabric Network Bypass - GUI Launcher
A simple PySide6 wrapper around the auto_bypass script.
"""

import sys
import os
import subprocess
import threading
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont


class OutputSignals(QObject):
    """Signals for thread communication."""
    output = Signal(str)
    finished = Signal(bool)


class BypassGUI(QMainWindow):
    """Main GUI window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fabric Network Bypass")
        self.setMinimumSize(700, 500)
        self.signals = OutputSignals()
        self.signals.output.connect(self.append_output)
        self.signals.finished.connect(self.on_finished)
        
        self.setup_ui()
        self.apply_theme()
        
        # Auto-start on launch
        self.start_auto_bypass()
    
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("🌐 Fabric Network Bypass")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        subtitle = QLabel("Automatic YouTube Rate Limit Fixer")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(subtitle)
        
        # Status
        self.status_label = QLabel("⏳ Auto-configuring...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 14))
        self.status_label.setStyleSheet("color: #f59e0b; padding: 10px;")
        layout.addWidget(self.status_label)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setMaximumHeight(8)
        layout.addWidget(self.progress)
        
        # Output console
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 10))
        layout.addWidget(self.output)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.run_btn = QPushButton("🔄 Re-run Auto-Bypass")
        self.run_btn.setEnabled(False)
        self.run_btn.clicked.connect(self.start_auto_bypass)
        self.run_btn.setStyleSheet("padding: 12px 25px; font-size: 13px;")
        btn_layout.addWidget(self.run_btn)
        
        self.test_btn = QPushButton("🧪 Quick Test")
        self.test_btn.setEnabled(False)
        self.test_btn.clicked.connect(self.quick_test)
        self.test_btn.setStyleSheet("padding: 12px 25px; font-size: 13px;")
        btn_layout.addWidget(self.test_btn)
        
        close_btn = QPushButton("✓ Done")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("padding: 12px 25px; font-size: 13px; background: #059669;")
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
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
            }
            QPushButton:hover {
                background: #6366f1;
            }
            QPushButton:disabled {
                background: #3a3a5a;
                color: #666;
            }
            QProgressBar {
                border: none;
                border-radius: 4px;
                background: #2a2a3a;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5, stop:1 #7c3aed);
                border-radius: 4px;
            }
        """)
    
    def append_output(self, text: str):
        self.output.append(text)
        # Auto-scroll
        self.output.verticalScrollBar().setValue(
            self.output.verticalScrollBar().maximum()
        )
    
    def on_finished(self, success: bool):
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.run_btn.setEnabled(True)
        self.test_btn.setEnabled(True)
        
        if success:
            self.status_label.setText("✅ Configuration Complete!")
            self.status_label.setStyleSheet("color: #4ade80; padding: 10px;")
        else:
            self.status_label.setText("⚠️ Configuration may need manual intervention")
            self.status_label.setStyleSheet("color: #f59e0b; padding: 10px;")
    
    def start_auto_bypass(self):
        self.output.clear()
        self.status_label.setText("⏳ Auto-configuring...")
        self.status_label.setStyleSheet("color: #f59e0b; padding: 10px;")
        self.progress.setRange(0, 0)
        self.run_btn.setEnabled(False)
        self.test_btn.setEnabled(False)
        
        thread = threading.Thread(target=self.run_auto_bypass)
        thread.daemon = True
        thread.start()
    
    def run_auto_bypass(self):
        script = Path(__file__).parent / "auto_bypass.py"
        
        process = subprocess.Popen(
            [sys.executable, str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(script.parent)
        )
        
        success = False
        for line in iter(process.stdout.readline, ''):
            self.signals.output.emit(line.rstrip())
            if "AUTO-CONFIGURATION COMPLETE" in line or "Direct connection works" in line:
                success = True
        
        process.wait()
        self.signals.finished.emit(success or process.returncode == 0)
    
    def quick_test(self):
        self.output.clear()
        self.status_label.setText("⏳ Running quick test...")
        self.status_label.setStyleSheet("color: #f59e0b; padding: 10px;")
        
        thread = threading.Thread(target=self.run_quick_test)
        thread.daemon = True
        thread.start()
    
    def run_quick_test(self):
        script = Path(__file__).parent / "auto_bypass.py"
        
        process = subprocess.Popen(
            [sys.executable, str(script), "--test"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(script.parent)
        )
        
        success = False
        for line in iter(process.stdout.readline, ''):
            self.signals.output.emit(line.rstrip())
            if "✅" in line or "Success" in line:
                success = True
        
        process.wait()
        self.signals.finished.emit(success)


def main():
    app = QApplication(sys.argv)
    window = BypassGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
