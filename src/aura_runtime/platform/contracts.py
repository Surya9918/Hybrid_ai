"""
AURA Companion - Platform-Neutral Core Interfaces
Defines abstract contracts for OS-specific adapters (Windows, AURA OS, Linux).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class IPlatformAdapter(ABC):
    @abstractmethod
    def launch_application(self, app_name: str, arguments: str = "") -> Tuple[bool, str]:
        pass

    @abstractmethod
    def switch_to_application(self, app_name: str) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def find_installed_applications(self, query: str) -> List[str]:
        pass

    @abstractmethod
    def get_screen_context(self, monitor_index: int = 0) -> Dict[str, Any]:
        pass

    @abstractmethod
    def analyze_region(self, x: int, y: int, width: int, height: int, question: str = "") -> Dict[str, Any]:
        pass

    @abstractmethod
    def read_clipboard_safely(self) -> str:
        pass

    @abstractmethod
    def show_notification(self, title: str, body: str, notification_id: str) -> bool:
        pass
