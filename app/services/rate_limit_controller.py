import time
import threading
from collections import deque
from typing import Optional
import asyncio

class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Consume tokens, return True if successful"""
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
    
    def wait_for_tokens(self, tokens: int = 1, timeout: Optional[float] = None):
        """Wait until tokens are available"""
        start = time.time()
        while not self.consume(tokens):
            if timeout and (time.time() - start) > timeout:
                raise TimeoutError("Rate limit wait timeout")
            time.sleep(0.1)

class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts based on API responses"""
    
    def __init__(self, initial_rate=10, initial_capacity=20):
        self.bucket = TokenBucket(initial_rate, initial_capacity)
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        self.current_rate = initial_rate
        self.current_capacity = initial_capacity
        
    def before_request(self):
        """Call before making API request"""
        self.bucket.wait_for_tokens(1)
    
    def after_request(self, success: bool, retry_after: Optional[float] = None):
        """Call after API request to adjust limits"""
        if success:
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            
            # Gradually increase rate on success
            if self.consecutive_successes > 10:
                self._increase_rate()
                self.consecutive_successes = 0
        else:
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            
            # Reduce rate on failure
            if retry_after:
                self._adjust_to_retry_after(retry_after)
            else:
                self._decrease_rate()
    
    def _increase_rate(self):
        """Increase rate limit gradually"""
        self.current_rate = min(self.current_rate * 1.1, 50)  # Max 50 req/sec
        self.current_capacity = min(self.current_capacity * 1.1, 100)
        self.bucket = TokenBucket(self.current_rate, self.current_capacity)
    
    def _decrease_rate(self):
        """Decrease rate limit aggressively on failure"""
        self.current_rate = max(self.current_rate * 0.5, 1)  # Min 1 req/sec
        self.current_capacity = max(self.current_capacity * 0.5, 5)
        self.bucket = TokenBucket(self.current_rate, self.current_capacity)
    
    def _adjust_to_retry_after(self, retry_after: float):
        """Adjust rate based on API's retry-after header"""
        suggested_rate = 1.0 / max(0.1, retry_after)
        self.current_rate = min(self.current_rate, suggested_rate)
        self.bucket = TokenBucket(self.current_rate, self.current_capacity)
