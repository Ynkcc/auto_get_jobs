# src/utils/rate_limiter.py
import asyncio
import time
import logging

logger = logging.getLogger(__name__)

class AsyncTokenBucket:
    """
    一个异步令牌桶限速器。
    """
    def __init__(self, rate: float, capacity: float):
        self.rate = rate  # 每秒生成的令牌数
        self.capacity = capacity  # 桶的容量
        self._tokens = float(capacity)  # 当前桶中的令牌数
        self._last_refill_time = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self):
        """按需补充令牌"""
        now = time.monotonic()
        time_delta = now - self._last_refill_time
        new_tokens = time_delta * self.rate
        if new_tokens > 0:
            self._tokens = min(self.capacity, self._tokens + new_tokens)
            self._last_refill_time = now

    async def acquire(self, tokens_to_take: int = 1):
        """
        获取指定数量的令牌，如果不够则异步等待。
        """
        if tokens_to_take > self.capacity:
            raise ValueError("请求的令牌数不能超过桶的容量")

        async with self._lock:
            self._refill()
            while self._tokens < tokens_to_take:
                # 计算需要等待的时间
                required_tokens = tokens_to_take - self._tokens
                wait_time = required_tokens / self.rate
                logger.debug(f"令牌不足，需要 {required_tokens:.2f} 个，预计等待 {wait_time:.2f} 秒")
                await asyncio.sleep(wait_time)
                self._refill()
            
            self._tokens -= tokens_to_take
            logger.debug(f"成功获取 {tokens_to_take} 个令牌，剩余 {self._tokens:.2f} 个")