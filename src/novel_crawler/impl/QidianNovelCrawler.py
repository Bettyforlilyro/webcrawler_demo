from typing import List, Dict, Any

from novel_crawler.NovelCrawlerFactory import BaseNovelCrawler


class UjNovelCrawler(BaseNovelCrawler):
    def get_novel_metadata_async(self, url: str) -> Dict[str, Any]:
        pass

    def get_novel_chapters_list_async(self, url: str) -> List[str]:
        pass

    def get_novel_chapter_content_async(self, chapter_url: str) -> str:
        pass