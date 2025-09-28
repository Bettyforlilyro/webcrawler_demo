import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Union
import aiohttp


@dataclass
class NovelMetadata:
    id: str             # 小说ID，根据这个id可以进入这本小说的详情网站
    title: str          # 小说名
    author: str         # 作者
    tag: str            # "玄幻"/"都市"/"历史"/"游戏"/"科幻"/"悬疑"/"言情"
    status: str         # "完结", "连载"
    word_count: int     # 字数
    update_time: str    # 最近更新时间
    description: str    # 简介
    cover_url: str      # 封面图片URL
    catalog_url: str    # 小说目录URL


class SortStrategy(ABC):
    @abstractmethod
    async def sort(self, novels: list[NovelMetadata]) -> list[NovelMetadata]:
        pass


class BaseNovelCrawler(ABC):
    """
    小说爬虫的基类。
    """
    @abstractmethod
    async def get_novel_metadata_async(
            self,
            url: str,
            session: aiohttp.ClientSession = None,
            semaphore: asyncio.Semaphore = None
    ) -> NovelMetadata:
        """
        从小说URL获取元数据。

        参数:
            url (str): 小说详情页URL
            session : 异步HTTP会话对象，用于管理共享连接池和Cookie等
            semaphore : 信号量semaphore控制并发
        返回:
            NovelMetadata: 小说的详情，包括作者、发布时间、字数等...
        """
        pass

    @abstractmethod
    async def get_novel_chapters_list_async(
            self,
            url: str,
            session: aiohttp.ClientSession = None,
            semaphore: asyncio.Semaphore = None
    ) -> list[tuple[str, str]]:
        """
        获取小说的章节列表。

        参数:
            url (str): 小说章节列表（目录列表）的URL
            session : 异步HTTP会话对象，用于管理共享连接池和Cookie等
            semaphore : 信号量semaphore控制并发

        返回:
            list[tuple[str, str]]: 所有章节URL的列表。(章节标题, 章节内容URL链接)
        """
        pass

    @abstractmethod
    async def get_novel_chapter_content_async(
            self,
            chapter_url: str,
            session: aiohttp.ClientSession = None,
            semaphore: asyncio.Semaphore = None
    ) -> str:
        """
        从小说章节中获取具体内容。

        参数:
            chapter_url (str): 小说某一章节具体内容的URL。
            session : 异步HTTP会话对象，用于管理共享连接池和Cookie等
            semaphore : 信号量semaphore控制并发

        返回:
            str: 章节的内容。
        """
        pass

    @abstractmethod
    async def get_novel_list_by_tag_async(
            self,
            tag: str,
            top_n: int,
            sort_method: SortStrategy = None,
            session: aiohttp.ClientSession = None,
            semaphore: asyncio.Semaphore = None
    ) -> list[tuple[str, str, str]]:
        """
        根据标签获取小说列表（异步）。

        参数:
            tag (str): 小说的分类，例如"xuanhuan"、"dushi"、"yanqing"。
            top_n (int): 返回多少本小说
            sort_method (SortStrategy): 结果的排序方法，需要是可直接调用的排序器，例如"update_time"、"click"、"subscribe"。
            session : 异步HTTP会话对象，用于管理共享连接池和Cookie等
            semaphore : 信号量semaphore控制并发

        返回:
            list[tuple[str, str, str]]: 具有此标签的一些小说信息。包括书名/作者/详情页URL链接
        """
        pass

    @abstractmethod
    async def get_novel_list_by_author_async(
            self,
            author: str,
            session: aiohttp.ClientSession = None,
            semaphore: asyncio.Semaphore = None
    ) -> list[tuple[str, str, str]]:
        """
        根据作者获取小说列表。

        参数:
            author (str): 小说的作者。
            session : 异步HTTP会话对象，用于管理共享连接池和Cookie等
            semaphore : 信号量semaphore控制并发

        返回:
            list[tuple[str, str, str]]: 该作者所写的小说的粗略信息，包括书名/作者/详情页URL链接
        """
        pass

    @abstractmethod
    async def get_novel_list_by_keyword_async(
            self,
            keyword: str,
            top_n: int = 5,
            session: aiohttp.ClientSession = None,
            semaphore: asyncio.Semaphore = None
    ) -> list[tuple[str, str, str]]:
        """
        根据关键词获取小说列表。

        参数:
            keyword (str): 小说的关键词。
            top_n (int): 返回相关的结果数量，默认5
            session : 异步HTTP会话对象，用于管理共享连接池和Cookie等
            semaphore : 信号量semaphore控制并发

        返回:
            list[tuple[str, str, str]]: 具有此关键词的小说的粗略信息，包括书名/作者/详情页URL链接
        """
        pass

    @abstractmethod
    async def get_novel_list_by_rank_async(
            self,
            rank_type: Union[str, Enum],
            top_n: int,
            session: aiohttp.ClientSession = None,
            semaphore: asyncio.Semaphore = None
    ) -> list[tuple[str, str, str]]:
        """
        根据不同的榜单（诸如订阅榜、推荐榜、月票榜等）返回排行前几的小说列表.

        参数:
            rank_type : 枚举类型或者字符串类型，不同的小说网站可能有各种不同的榜单类型
            top_n (int): 返回相关的结果数量
            session : 异步HTTP会话对象，用于管理共享连接池和Cookie等
            semaphore : 异信号量semaphore控制并发

        返回:
            list[tuple[str, str, str]]: 具有此关键词的小说的粗略信息，包括书名/作者/详情页URL链接
        """
        pass

    @abstractmethod
    async def write_novel_content_to_file(
            self,
            url: str,
            file_path: str,
            session: aiohttp.ClientSession = None,
            semaphore: asyncio.Semaphore = None
    ):
        """
        将具体的某一本小说保存到指定的文件夹路径下

        参数：
            url (str): 小说详情页的URL路径
            file_path (str): 小说需要保存到哪个文件夹下面
            session : 异步HTTP会话对象，用于管理共享连接池和Cookie等
            semaphore : 信号量semaphore控制并发

        """


class NovelCrawlerFactory:
    """
    小说爬虫的工厂类。
    """
    _all_sites = {}

    @classmethod
    def register_novel_crawler(cls, site_name: str, crawler: Any) -> None:
        """
        为站点注册小说爬虫。

        参数:
            site_name (str): 站点的名称。
            crawler (Any): 小说爬虫类。
        """
        cls._all_sites[site_name] = crawler

    @classmethod
    def create_novel_crawler(cls, site_name: str) -> BaseNovelCrawler:
        """
        为给定站点名称创建小说爬虫。

        参数:
            site_name (str): 站点的名称。

        返回:
            BaseNovelCrawler: 给定站点的小说爬虫。
        """
        crawler = cls._all_sites.get(site_name)
        if crawler is None:
            raise ValueError(f"未找到站点 '{site_name}' 的爬虫")
        return crawler()
