#!/usr/bin/env python3
"""
ADRION 369 - System Tray MVP
Systray icon wrapper for UAP Backend + Frontend management

Usage:
    python uap_systray.py

Features:
    - System tray icon (always visible)
    - Menu: Open UAP, Status, Quit
    - Auto-launch backend (on-demand)
    - Health checks (green/red status)
    - Graceful shutdown
"""

import sys
import os
import subprocess
import time
import logging
import webbrowser
from pathlib import Path
from typing import Optional

# Third party
import pystray
from PIL import Image, ImageDraw
import psutil
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('uap_systray.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('adrion.systray')

# Configuration
BACKEND_HOST = "localhost"
BACKEND_PORT = 8002
FRONTEND_PORT = 8003
HEALTH_CHECK_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}/mapi/v1/health"
FRONTEND_URL = f"http://127.0.0.1:{FRONTEND_PORT}"
LAUNCHER_SCRIPT = "scripts/launch_uap_local_v3.py"

# Status indicators
STATUS_OK = (0, 200, 0)      # Green
STATUS_WARN = (255, 165, 0)  # Orange
STATUS_ERROR = (200, 0, 0)   # Red


class UAP_TrayApp:
    """System tray application for ADRION 369 UAP"""

    def __init__(self):
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.backend_running = False
        self.is_quitting = False
        logger.info("UAP Tray App initialized")

    def generate_icon(self, status_color=STATUS_WARN) -> Image.Image:
        """Generate tray icon dynamically (32x32 with status color)"""
        icon = Image.new('RGB', (32, 32), color='white')
        draw = ImageDraw.Draw(icon)

        # Draw circle with status color
        draw.ellipse([(2, 2), (30, 30)], fill=status_color, outline='black', width=2)

        # Draw "A" for ADRION
        draw.text((10, 8), "A", fill='white', font=None)

        return icon

    def is_port_in_use(self, port: int) -> bool:
        """Check if port is already in use"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                logger.warning(f"Port {port} already in use (PID: {conn.pid})")
                return True
        return False

    def health_check(self) -> bool:
        """Check if backend is responsive"""
        try:
            resp = requests.get(HEALTH_CHECK_URL, timeout=2)
            is_healthy = resp.status_code == 200
            if is_healthy:
                logger.debug(f"Health check OK: {resp.status_code}")
            else:
                logger.warning(f"Health check failed: {resp.status_code}")
            return is_healthy
        except Exception as e:
            logger.warning(f"Health check error: {e}")
            return False

    def start_backend(self) -> bool:
        """Launch backend + frontend services"""
        if self.backend_running:
            logger.info("Backend already running")
            return True

        # Check ports
        if self.is_port_in_use(BACKEND_PORT):
            logger.error(f"Port {BACKEND_PORT} already in use")
            return False

        try:
            logger.info(f"Starting launcher: {LAUNCHER_SCRIPT}")
            # Find the launcher script from workspace root
            launcher_path = Path(__file__).parent.parent.parent.parent / LAUNCHER_SCRIPT
            if not launcher_path.exists():
                logger.error(f"Launcher script not found: {launcher_path}")
                return False

            self.backend_process = subprocess.Popen(
                [sys.executable, str(launcher_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(launcher_path.parent.parent.parent.parent)
            )
            logger.info(f"Launcher PID: {self.backend_process.pid}")

            # Wait for backend to be ready (up to 15 seconds)
            for attempt in range(30):  # 30 * 0.5 = 15s
                if self.health_check():
                    self.backend_running = True
                    logger.info("✓ Backend is healthy")
                    return True
                time.sleep(0.5)

            logger.error("Backend startup timeout (15s)")
            return False

        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            return False

    def stop_backend(self) -> bool:
        """Gracefully shutdown backend"""
        if not self.backend_running:
            logger.info("Backend not running")
            return True

        try:
            if self.backend_process and self.backend_process.poll() is None:
                logger.info(f"Terminating backend (PID: {self.backend_process.pid})")
                self.backend_process.terminate()

                # Wait up to 5 seconds for graceful shutdown
                try:
                    self.backend_process.wait(timeout=5)
                    logger.info("✓ Backend shut down gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning("Backend didn't stop, forcing termination...")
                    self.backend_process.kill()
                    self.backend_process.wait()
                    logger.info("✓ Backend force-killed")

            self.backend_running = False
            return True

        except Exception as e:
            logger.error(f"Error stopping backend: {e}")
            return False

    def on_open_uap(self, icon, item):
        """Menu: Open UAP (start backend if needed)"""
        logger.info("User clicked: Open UAP")

        if not self.backend_running:
            logger.info("Starting backend...")
            if not self.start_backend():
                logger.error("Failed to start backend")
                # Could show error dialog here
                return

        logger.info(f"Opening browser: {FRONTEND_URL}")
        try:
            webbrowser.open(FRONTEND_URL)
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")

    def on_show_status(self, icon, item):
        """Menu: Show status of backend"""
        logger.info("User clicked: Show Status")

        if self.health_check():
            status_text = "✓ Backend is running"
            try:
                resp = requests.get(HEALTH_CHECK_URL, timeout=2)
                status_text = f"✓ Healthy (HTTP {resp.status_code})"
            except:
                pass
        else:
            status_text = "✗ Backend not responding"

        logger.info(f"Status: {status_text}")
        # In a real app, would show tooltip or dialog

    def on_quit(self, icon, item):
        """Menu: Quit application"""
        logger.info("User clicked: Quit")

        self.is_quitting = True
        self.stop_backend()

        logger.info("Stopping tray icon...")
        icon.stop()

        logger.info("UAP Tray App exiting")
        sys.exit(0)

    def create_menu(self, icon):
        """Create tray menu"""
        return pystray.Menu(
            pystray.MenuItem(
                "Open UAP",
                self.on_open_uap
            ),
            pystray.MenuItem(
                "Status",
                self.on_show_status
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Quit",
                self.on_quit
            )
        )

    def run(self):
        """Start the system tray app"""
        logger.info("Creating system tray icon...")

        # Generate icon
        icon_image = self.generate_icon(STATUS_WARN)

        # Create tray icon
        icon = pystray.Icon(
            name="ADRION-UAP",
            icon=icon_image,
            title="ADRION 369 - UAP",
            menu=self.create_menu
        )

        logger.info("Starting tray icon...")
        icon.run()


def main():
    """Main entry point"""
    try:
        app = UAP_TrayApp()
        app.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
