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
        write_file_semaphore = asyncio.Semaphore(5)
        tasks = []
        for keyword in keywords:
            tasks.append(crawler.get_novel_list_by_keyword_async(keyword, semaphore))
        related_novels = await asyncio.gather(*tasks)
        print(related_novels)
        write_file_tasks = []
        for novel_list in related_novels:
            flag = False
            for novel in novel_list:
                for keyword in keywords:
                    if novel[0] == keyword:
                        write_file_tasks.append(
                            crawler.write_novel_content_to_file(novel[2], '/mnt/e/backup/novels/', write_file_semaphore)
                        )
                        flag = True
                        break
                if flag:
                    break
        await asyncio.gather(*write_file_tasks)
        author = "辰东"
        novels_by_author = await crawler.get_novel_list_by_author_async(author, semaphore)
        print(novels_by_author)


if __name__ == '__main__':
    asyncio.run(main())

