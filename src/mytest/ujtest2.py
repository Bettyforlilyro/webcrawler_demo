import asyncio
import aiohttp

from novel_crawler.NovelCrawlerFactory import NovelCrawlerFactory
from novel_crawler.impl.UjNovelCrawler import UjNovelCrawler


async def main():
    async with aiohttp.ClientSession() as session:
        NovelCrawlerFactory.register_novel_crawler("ujxsw", UjNovelCrawler)
        crawler = NovelCrawlerFactory.create_novel_crawler("ujxsw")
        keywords = ["高武纪元", "这个武圣血条太厚"]
        # 控制搜索请求并发
        semaphore = asyncio.Semaphore(5)
        tasks = []
        for keyword in keywords:
            tasks.append(crawler.get_novel_list_by_keyword_async(keyword, 5, session, semaphore))
        related_novels_list = await asyncio.gather(*tasks)
        write_file_tasks = []
        file_path = "/mnt/e/backup/novels/"
        real_novels_url = []
        for novels in related_novels_list:
            for novel in novels:
                title, _, detail_url = novel
                if title in keywords:
                    real_novels_url.append(detail_url)
        for detail_url in real_novels_url:
            write_file_tasks.append(crawler.write_novel_content_to_file(detail_url, file_path, session, semaphore))
        await asyncio.gather(*write_file_tasks)
        print(novels)



if __name__ == '__main__':
    asyncio.run(main())

