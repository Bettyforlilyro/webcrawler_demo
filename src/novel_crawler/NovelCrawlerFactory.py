import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List

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


class BaseNovelCrawler(ABC):
    """
    小说爬虫的基类。
    """
    @abstractmethod
    async def get_novel_metadata_async(self, session: aiohttp.ClientSession, url: str) -> Any:
        """
        从小说URL获取元数据。

        参数:
            url (str): 小说的URL。

        返回:
            Any: 小说的元数据，包括作者、发布时间、字数等...
        """
        pass

    @abstractmethod
    async def get_novel_chapters_list_async(self, session: aiohttp.ClientSession, url: str) -> list[tuple[str, str]]:
        """
        获取小说的章节列表。

        参数:
            url (str): 小说的URL。

        返回:
            List[(str, str)]: 所有章节URL的列表。(章节标题, 章节URL链接)
        """
        pass

    @abstractmethod
    async def get_novel_chapter_content_async(self, session: aiohttp.ClientSession, chapter_url: str) -> str:
        """
        从小说章节中获取具体内容。

        参数:
            chapter_url (str): 小说章节的URL。

        返回:
            str: 章节的内容。
        """
        pass

    @abstractmethod
    async def get_novel_list_by_tag_async(self, tag: str, sort_method: Any = None) -> List[Any]:
        """
        根据标签获取小说列表（异步）。

        参数:
            tag (str): 小说的标签，例如"xuanhuan"、"dushi"、"yanqing"。
            sort_method (Any): 结果的排序方法，需要是可直接调用的排序器，例如"update_time"、"click"、"subscribe"。

        返回:
            List[Any]: 具有此标签的小说的详细信息。
        """
        pass

    @abstractmethod
    async def get_novel_list_by_author_async(self, author: str, semaphore: asyncio.Semaphore) -> list[tuple[str, str, str]]:
        """
        根据作者获取小说列表。

        参数:
            author (str): 小说的作者。
            semaphore : 控制并发的信号量

        返回:
            list[tuple[str, str, str]]: 具有此关键词的小说的粗略信息，包括书名/作者/详情页URL链接
        """
        pass

    @abstractmethod
    async def get_novel_list_by_keyword_async(self, keyword: str, semaphore: asyncio.Semaphore, top_n: int = 5) -> list[tuple[str, str, str]]:
        """
        根据关键词获取小说列表。

        参数:
            keyword (str): 小说的关键词。
            semaphore : 控制并发的信号量
            top_n (int): 返回相关的结果数量，默认5

        返回:
            list[tuple[str, str, str]]: 具有此关键词的小说的粗略信息，包括书名/作者/详情页URL链接
        """
        pass

    @abstractmethod
    async def write_novel_content_to_file(self, url: str, file_path: str, semaphore: asyncio.Semaphore):
        """
        将具体的某一本小说保存到指定的文件夹路径下

        参数：
            url (str): 小说详情页的URL路径
            file_path (str): 小说需要保存到哪个文件夹下面
            semaphore : 控制并发的信号量

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

