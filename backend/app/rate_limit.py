from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
from collections import defaultdict
import threading


class RateLimiter:
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
        self.cleanup_interval = 60
        self._start_cleanup()
    
    def _start_cleanup(self):
        def cleanup():
            while True:
                time.sleep(self.cleanup_interval)
                now = time.time()
                with self.lock:
                    for key in list(self.requests.keys()):
                        self.requests[key] = [
                            t for t in self.requests[key]
                            if now - t < 60
                        ]
                        if not self.requests[key]:
                            del self.requests[key]
        
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
    
    def check(self, key: str) -> bool:
        now = time.time()
        with self.lock:
            if key not in self.requests:
                self.requests[key] = []
            
            self.requests[key] = [
                t for t in self.requests[key]
                if now - t < 60
            ]
            
            if len(self.requests[key]) >= self.requests_per_minute:
                return False
            
            self.requests[key].append(now)
            return True


rate_limiter = RateLimiter(requests_per_minute=100)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"
        
        if not rate_limiter.check(key):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too many requests",
                    "message": "Limite de requisições excedido. Tente novamente em 1 minuto.",
                    "code": "RATE_LIMIT_EXCEEDED"
                }
            )
        
        return await call_next(request)