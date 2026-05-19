"""
ADRION 369 — Micro-Router for http.server
Deklaratywny routing dla BaseHTTPRequestHandler.

Pozwala definiować trasy w oddzielnych modułach i rejestrować je centralnie,
eliminując monolityczny łańcuch elif w do_GET/do_POST.
"""

import re
from typing import Callable, Optional


class Route:
    __slots__ = ("method", "pattern", "handler", "prefix")

    def __init__(self, method: str, pattern: str, handler: Callable):
        self.method = method.upper()
        self.prefix = not bool(re.search(r'[\\(\\[\\{\\*\\+\\?\\$]', pattern))
        self.pattern = pattern if self.prefix else re.compile(pattern)
        self.handler = handler

    def match(self, method: str, path: str) -> bool:
        if method != self.method:
            return False
        if self.prefix:
            return path == self.pattern or path.startswith(self.pattern + "?")
        return bool(self.pattern.match(path))


class Router:
    """
    Centralny rejestr tras.

    Użycie:
        router = Router()
        router.add("GET", "/api/leads", handle_get_leads)
        router.add("POST", "/webhook/harmonia-369", handle_webhook)

        # W WebhookHandler:
        handler_fn = router.resolve("GET", "/api/leads")
        if handler_fn:
            handler_fn(self, data)
    """

    def __init__(self):
        self._routes: list[Route] = []

    def add(self, method: str, pattern: str, handler: Callable):
        """Zarejestruj trasę. Pattern może być exact string lub regex."""
        self._routes.append(Route(method, pattern, handler))

    def get(self, pattern: str, handler: Callable):
        self.add("GET", pattern, handler)

    def post(self, pattern: str, handler: Callable):
        self.add("POST", pattern, handler)

    def resolve(self, method: str, path: str) -> Optional[Callable]:
        """Znajdź handler pasujący do method+path. Zwraca None jeśli brak."""
        clean_path = path.split("?")[0]
        for route in self._routes:
            if route.match(method, clean_path):
                return route.handler
        return None

    def list_routes(self) -> list[dict]:
        """Zwróć listę zarejestrowanych tras (do /health i logów startowych)."""
        return [
            {
                "method": r.method,
                "pattern": r.pattern if isinstance(r.pattern, str) else r.pattern.pattern,
            }
            for r in self._routes
        ]
