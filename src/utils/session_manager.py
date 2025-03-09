import threading
import asyncio
import requests
import aiohttp

class SessionManager:
    # 同步资源锁
    _sync_lock = threading.Lock()
    # 异步资源锁
    _async_lock = asyncio.Lock()
    
    # 共享配置存储
    _config = {
        'headers': {'Accept': 'application/json'},
        'cookies': {}
    }
    
    # Session实例
    _sync_session = None
    _async_session = None
    _async_needs_rebuild = False  # 异步session需要重建标记

    def __new__(cls):
        raise NotImplementedError("Cannot instantiate singleton class")

    @classmethod
    def get_sync_session(cls):
        """获取同步session（线程安全）"""
        with cls._sync_lock:
            if cls._sync_session is None:
                cls._sync_session = requests.Session()
                # 应用当前配置
                cls._sync_session.headers.update(cls._config['headers'])
                cls._sync_session.cookies.update(cls._config['cookies'])
            return cls._sync_session

    @classmethod
    async def get_async_session(cls):
        """获取异步session（协程安全）"""
        async with cls._async_lock:
            # 检查重建标记时需要同步锁
            with cls._sync_lock:
                needs_rebuild = cls._async_needs_rebuild
                if needs_rebuild:
                    cls._async_needs_rebuild = False

            # 关闭旧session并重建
            if needs_rebuild and cls._async_session and not cls._async_session.closed:
                await cls._async_session.close()
                cls._async_session = None

            if cls._async_session is None or cls._async_session.closed:
                # 从当前配置创建新session
                with cls._sync_lock:
                    cookies = cls._config['cookies'].copy()
                    headers = cls._config['headers'].copy()

                connector = aiohttp.TCPConnector(ssl=False)
                cls._async_session = aiohttp.ClientSession(
                    connector=connector,
                    headers=headers,
                    cookie_jar=aiohttp.CookieJar(unsafe=True)
                )
            return cls._async_session

    @classmethod
    def update_session(cls, cookies: dict, headers: dict):
        """更新session配置（线程安全）"""
        with cls._sync_lock:
            # 原子更新配置
            cls._config['cookies'].update(cookies)
            cls._config['headers'].update(headers)

            # 更新现有的同步session
            if cls._sync_session:
                cls._sync_session.cookies.update(cookies)
                cls._sync_session.headers.update(headers)

            # 标记异步session需要重建
            cls._async_needs_rebuild = True

    @classmethod
    async def close(cls):
        """关闭所有session（协程安全）"""
        # 关闭同步session
        with cls._sync_lock:
            if cls._sync_session:
                cls._sync_session.close()
                cls._sync_session = None
            cls._async_needs_rebuild = False  # 重置标记

        # 关闭异步session
        async with cls._async_lock:
            if cls._async_session and not cls._async_session.closed:
                await cls._async_session.close()
                cls._async_session = None
