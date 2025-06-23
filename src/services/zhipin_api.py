# src/services/zhipin_api.py
import asyncio
import hashlib
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

import aiohttp
from yarl import URL

from ..common.event_manager import event_manager

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
            cls._instance._initialized = False
        return cls._instance

    async def initialize(self):
        """
        初始化并注册事件监听器。
        """
        if self._initialized:
            return
        # 浏览器模块会发布 "cookies_updated" 事件
        event_manager.subscribe("cookies_updated", self.handle_session_update)
        self._initialized = True
        logger.info("ZhipinApi 已初始化并订阅 cookies_updated 事件")

    async def handle_session_update(self, cookies_data: dict, **kwargs):
        """
        事件回调：当收到新的登录凭据时，更新会话的 cookies 和 headers。
        """
        async with self._session_lock:
            cookies = cookies_data.get("cookies", [])
            self._cookies = {c['name']: c['value'] for c in cookies}
            self._headers.update(cookies_data.get("headers", {}))

            if self._session and not self._session.closed:
                await self._session.close()
            self._session = None
            logger.info("ZhipinApi 的会话配置已更新，将在下次请求时重建")
            await self.get_user_info()

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

    async def get_user_info(self) -> Dict:
        """获取当前登录的用户信息并缓存"""
        session = await self._get_session()
        if not self._cookies:
            logger.warning("无法获取用户信息：Session中没有Cookies。")
            return {}
        try:
            url = "https://www.zhipin.com/wapi/zpgeek/user/info"
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                data = await response.json()
                if data.get("code") == 0 and "zpData" in data:
                    self._user_info = data.get("zpData", {})
                    logger.info(f"获取用户信息成功: {self._user_info.get('name')}")
                    return self._user_info
                else:
                    logger.error(f"获取用户信息失败: {data.get('message')}")
                    return {}
        except Exception as e:
            logger.error(f"请求用户信息时出错: {e}", exc_info=True)
            return {}

    def get_user_id(self) -> Optional[int]:
        """从缓存的用户信息中获取UID"""
        return self._user_info.get("uid")

    def get_wt2(self) -> Optional[str]:
        """根据Boss直聘的逻辑生成 wt2 参数"""
        uid = self.get_user_id()
        if not uid:
            logger.error("无法生成wt2: 未获取到用户UID")
            return None
        now = datetime.now(timezone(timedelta(hours=8)))
        formatted_time = now.strftime('%Y%m%d%H')
        text = f"uid={uid}&type=1&source=1&version=1&time={formatted_time}&ps=最终的加盐"
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    async def upload_image(self, file_path: str, security_id: str, file_md5: str) -> Optional[Dict]:
        """
        上传图片简历到Boss直聘, 优先尝试快传.
        """
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
                    if data.get("code") == 0 and data.get("zpData", {}).get("url"):
                        logger.info(f"图片 '{os.path.basename(file_path)}' 快速上传成功")
                        return data.get("zpData")
        except Exception as e:
            logger.warning(f"快速上传失败，将尝试完整上传: {e}")

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
                        return data.get("zpData")
                    else:
                        logger.error(f"完整上传失败: {data.get('message')}")
                        return None
        except Exception as e:
            logger.error(f"完整上传时发生错误: {e}", exc_info=True)
            return None

    async def start_chat(self, security_id: str, job_id: str, lid: str) -> Optional[Dict]:
        """ 与招聘者开始聊天（投递简历）"""
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

zhipin_api = ZhipinApi()