# src/services/zhipin_api.py

import asyncio
import hashlib
import logging
import os
from datetime import datetime
from typing import Dict, Optional

import aiohttp
from yarl import URL
from aiolimiter import AsyncLimiter

from ..common.event_manager import event_manager
from ..common.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class ZhipinApi:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._session = None
            cls._instance._headers = {}
            cls._instance._cookies = {}
            cls._instance._user_info = {}
            cls._instance._session_lock = asyncio.Lock()
            # 设置一个安全的默认限速器，防止在配置加载前调用时出错
            cls._instance._limiter = AsyncLimiter(1, 1)
            # API就绪状态事件
            cls._instance._api_ready = asyncio.Event()
            logger.info("ZhipinApi已创建，使用默认限速器 (1 req/s)")
        return cls._instance

    async def wait_for_ready(self):
        """
        等待API客户端进入就绪状态。
        """
        await self._api_ready.wait()

    async def handle_session_update(self, cookies_data: dict, **kwargs):
        """
        事件回调：当收到新的登录凭据时，更新会话的 cookies 和 headers。
        """
        async with self._session_lock:
            # 清除旧的就绪状态
            self._api_ready.clear()
            
            cookies = cookies_data.get("cookies", [])
            self._cookies = {c['name']: c['value'] for c in cookies}
            self._headers.update(cookies_data.get("headers", {}))

            if self._session and not self._session.closed:
                await self._session.close()
            self._session = None
            logger.info("ZhipinApi 的会话配置已更新，将在下次请求时重建")

        # 尝试获取用户信息以验证新会话并设置就绪状态
        user_info = await self.get_user_info(wait_for_ready=False)
        if user_info:
            self._api_ready.set()
            logger.info("ZhipinApi 已就绪，凭据验证成功。")
        else:
            logger.warning("ZhipinApi 在会话更新后未能进入就绪状态。")

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        获取或创建 aiohttp.ClientSession。
        """
        async with self._session_lock:
            if self._session is None or self._session.closed:
                if not self._cookies:
                    logger.warning("无法创建ZhipinAPI会话：Cookies为空。请等待浏览器登录并同步。")
                
                connector = aiohttp.TCPConnector(limit=100, limit_per_host=20, ssl=False)
                cookie_jar = aiohttp.CookieJar(unsafe=True)
                if self._cookies:
                    cookie_jar.update_cookies(self._cookies, URL("https://www.zhipin.com"))

                self._session = aiohttp.ClientSession(
                    connector=connector,
                    headers=self._headers,
                    cookie_jar=cookie_jar
                )
                logger.info("新的 ZhipinApi aiohttp.ClientSession 已创建")
            return self._session
    
    async def get_job_detail(self, security_id: str, lid: str) -> Optional[Dict]:
        """
        获取职位详细信息
        """
        await self._api_ready.wait()
        async with self._limiter:
            session = await self._get_session()
            url = "https://www.zhipin.com/wapi/zpgeek/job/detail.json"
            params = {
                "securityId": security_id,
                "lid": lid,
                "_": int(datetime.now().timestamp() * 1000)
            }
            try:
                async with session.get(url, params=params, timeout=15) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if data.get("code") == 0 and "zpData" in data:
                        logger.debug(f"成功获取职位详情: {data['zpData'].get('jobInfo',{}).get('jobName')}")
                        return data.get("zpData")
                    else:
                        logger.error(f"获取职位详情失败: {data.get('message')}")
                        return None
            except Exception as e:
                logger.error(f"请求职位详情时出错 (securityId: {security_id}): {e}", exc_info=True)
                return None

    async def get_user_info(self, wait_for_ready: bool = True) -> Dict:
        """获取当前登录的用户信息并缓存"""
        if wait_for_ready:
            await self._api_ready.wait()
            # 如果是等待后调用，直接返回缓存的信息
            return self._user_info

        # ---- 以下逻辑仅在初始化时(wait_for_ready=False)执行 ----
        session = await self._get_session()
        if not self._cookies:
            logger.warning("无法获取用户信息：Session中没有Cookies。")
            return {}
        try:
            url = "https://www.zhipin.com/wapi/zpuser/wap/getUserInfo.json"
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                data = await response.json()
                if data.get("code") == 0 and "zpData" in data:
                    self._user_info = data.get("zpData", {})
                    logger.info(f"获取用户信息成功: {self._user_info.get('name')}")
                    return self._user_info
                else:
                    logger.error(f"获取用户信息失败: {data.get('message')}")
                    self._user_info = {} # 获取失败时清空
                    return {}
        except Exception as e:
            logger.error(f"请求用户信息时出错: {e}", exc_info=True)
            self._user_info = {} # 出现异常时清空
            return {}

    def get_user_token(self) -> Optional[int]:
        """
        从缓存的用户信息中获取用于mqtt连接的用户名。
        """
        return self._user_info.get("token")

    def get_user_id(self) -> Optional[int]:
        """
        从缓存的用户信息中获取用于mqtt连接的用户名。
        """
        return self._user_info.get("userId")

    async def get_wt2(self) -> Optional[str]:
        """通过网络请求获取wt2验证参数"""
        await self._api_ready.wait()
        async with self._limiter:
            session = await self._get_session()
            if not self._cookies:
                logger.warning("无法获取wt2：Session中没有Cookies。")
                return None
            try:
                url = "https://www.zhipin.com/wapi/zppassport/get/wt"
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if data.get("code") == 0:
                        wt2 = data['zpData'].get('wt2')
                        logger.info("获取wt2成功")
                        return wt2
                    else:
                        logger.error(f"获取wt2失败: {data.get('message')}")
                        return None
            except Exception as e:
                logger.error(f"请求wt2时出错: {e}", exc_info=True)
                return None

    async def upload_image(self, file_path: str, security_id: str, file_md5: str) -> Optional[Dict]:
            """
            上传图片简历到Boss直聘, 优先尝试快传, 并返回符合Protobuf结构的字典。
            """
            await self._api_ready.wait()

            # 辅助函数，用于从API响应构建Protobuf兼容的字典
            def _build_image_dict(zp_data: dict) -> Optional[Dict]:
                if not zp_data or 'url' not in zp_data:
                    return None
                try:
                    # 从元数据获取尺寸，如果不存在则提供默认值
                    metadata = zp_data.get("metadata", {})
                    origin_width = metadata.get("width",None)
                    origin_height = metadata.get("height", None)
                    if origin_width is None or origin_height is None:
                        # 如果没有提供尺寸，引发异常
                        raise ValueError("图片元数据中缺少宽度或高度信息")

                    # 计算缩略图尺寸
                    tiny_width = 200
                    tiny_height = int(tiny_width * origin_height / origin_width) if origin_width > 0 else 200

                    return {
                        "tinyImage": {
                            "url": zp_data.get('tinyUrl', zp_data['url']), # 如果没有tinyUrl，使用原始url
                            "width": tiny_width,
                            "height": tiny_height
                        },
                        "originImage": {
                            "url": zp_data['url'],
                            "width": origin_width,
                            "height": origin_height
                        }
                    }
                except Exception as e:
                    logger.error(f"从zpData构建图片字典时出错: {e}")
                    return None

            # 1. 尝试快速上传
            async with self._limiter:
                session = await self._get_session()
                quick_upload_url = "https://www.zhipin.com/wapi/zpupload/quicklyUpload"
                quick_data = {
                    "fileMd5": file_md5,
                    "fileSize": os.path.getsize(file_path),
                    "source": "chat_file",
                    "securityId": security_id
                }
                try:
                    async with session.post(quick_upload_url, data=quick_data, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("code") == 0:
                                zp_data = data.get("zpData")
                                if zp_data and zp_data.get("url"):
                                    logger.info(f"图片 '{os.path.basename(file_path)}' 快速上传成功")
                                    return _build_image_dict(zp_data)
                except Exception as e:
                    logger.warning(f"快速上传失败，将尝试完整上传: {e}")
            
            # 2. 如果快传失败，则进行完整上传
            async with self._limiter:
                session = await self._get_session()
                full_upload_url = "https://www.zhipin.com/wapi/zpupload/image/uploadSingle"
                try:
                    with open(file_path, "rb") as f:
                        form_data = aiohttp.FormData()
                        form_data.add_field('file', f, filename=os.path.basename(file_path), content_type='application/octet-stream')
                        form_data.add_field('securityId', security_id)
                        form_data.add_field('source', 'chat_file')
                        
                        async with session.post(full_upload_url, data=form_data, timeout=30) as response:
                            response.raise_for_status()
                            data = await response.json()
                            if data.get("code") == 0:
                                logger.info(f"图片 '{os.path.basename(file_path)}' 完整上传成功")
                                return _build_image_dict(data.get("zpData"))
                            else:
                                logger.error(f"完整上传失败: {data.get('message')}")
                                return None
                except Exception as e:
                    logger.error(f"完整上传时发生错误: {e}", exc_info=True)
                    return None

    async def start_chat(self, security_id: str, job_id: str, lid: str) -> Optional[Dict]:
        """ 与招聘者开始聊天（投递简历）"""
        await self._api_ready.wait()
        async with self._limiter:
            url = "https://www.zhipin.com/wapi/zpgeek/friend/add.json"
            params = {"securityId": security_id, "jobId": job_id, "lid": lid}
            session = await self._get_session()
            try:
                async with session.get(url, params=params, timeout=15) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                logger.error(f"发起聊天时出错: {e}", exc_info=True)
                return None

    async def close(self, **kwargs):
        """ 关闭 aiohttp.ClientSession """
        async with self._session_lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None
                logger.info("ZhipinApi 的 aiohttp.ClientSession 已关闭")

    def reinitialize_config(self):
        """根据加载的配置重新初始化速率限制器。"""
        try:
            config = ConfigManager.get_config()
            rate_limit_config = config.crawler.rate_limit

            self._limiter = AsyncLimiter(rate_limit_config.rate, 60)
            logger.info(f"ZhipinApi 限速器已根据配置更新: 速率 {rate_limit_config.rate} req/min")
        except RuntimeError as e:
            logger.warning(f"重新初始化ZhipinApi配置失败，将继续使用默认限速器: {e}")

zhipin_api = ZhipinApi()