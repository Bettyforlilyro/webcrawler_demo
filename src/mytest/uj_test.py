import os

import aiofiles
import aiohttp

from novel_crawler.NovelCrawlerFactory import NovelCrawlerFactory
from novel_crawler.impl.UjNovelCrawler import UjNovelCrawler

NovelCrawlerFactory.register_novel_crawler("ujxsw", UjNovelCrawler)
crawler = NovelCrawlerFactory.create_novel_crawler("ujxsw")


async def fetch_chapters_with_semaphore(semaphore, crawler, session, catalog_url):
    async with semaphore:
        return await crawler.get_novel_chapters_list_async(session, catalog_url)


async def fetch_chapter_content_with_semaphore(semaphore, crawler, session, chapter_url):
    async with semaphore:
        return await crawler.get_novel_chapter_content_async(session, chapter_url)


async def create_file_if_not_exists(file_path, semaphore):
    """异步创建文件（如果不存在）"""
    if not os.path.exists(file_path):
        async with semaphore:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                pass


async def process_novel_chapters(semaphore, crawler, session, novel_chapters_list, file_path):
    """处理单本小说的所有章节"""
    tasks = []
    title_list = []
    for chapter_title, chapter_url in novel_chapters_list:
        title_list.append(chapter_title)
        tasks.append(fetch_chapter_content_with_semaphore(semaphore, crawler, session, chapter_url))
    # 根据章节url异步获取章节内容
    all_chapter_content = await asyncio.gather(*tasks)
    async with semaphore:
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            # 对于单个文件，只能串行写入，否则章节顺序会乱
            for chapter_title, chapter_content in zip(title_list, all_chapter_content):
                await f.write(chapter_title + '\n\n' + chapter_content + '\n\n\n')


async def main():
    crawler = NovelCrawlerFactory.create_novel_crawler("ujxsw")
    tag_list = ["xuanhuan", "dushi", "lishi", "youxi", "kehuan", "yanqing", "wuxia"]
    for tag in tag_list:
        results = await crawler.get_novel_list_by_tag_async(tag)
        async with aiohttp.ClientSession(headers=crawler.__getattribute__("headers")) as session:
            # 控制并发数
            # 获取所有小说章节列表，用信号量控制并发请求数
            get_all_novels_chapters_list_semaphore = asyncio.Semaphore(10)
            # 创建文件也用异步并发信号量控制
            create_file_semaphore = asyncio.Semaphore(20)
            # 将所有小说内容写到文件中去，也用一个异步并发信号量控制
            write_file_semaphore = asyncio.Semaphore(20)
            # 所有任务
            tasks = []
            novels_file_list = []
            base_path = r'/mnt/e/backup/novels'
            for result in results:
                catalog_url = result.catalog_url
                tasks.append(
                    fetch_chapters_with_semaphore(get_all_novels_chapters_list_semaphore, crawler, session, catalog_url)
                )
                file_name = result.title + '_' + result.author + '.txt'
                file_path = os.path.join(base_path, tag, file_name)
                novels_file_list.append(file_path)
            # 并发执行所有任务并收集所有小说的章节列表[(章节标题, 章节内容URL链接)]
            # 这里并没有获取小说章节具体内容
            all_novels_chapters_list = await asyncio.gather(*tasks)
            # 如果文件不存在，创建文件先
            create_file_tasks = [create_file_if_not_exists(file_path, create_file_semaphore) for file_path in novels_file_list]
            await asyncio.gather(*create_file_tasks)
            # 并发将所有小说写入到对应文件中去
            process_novel_tasks = []
            for file_path, novel_chapters_list in zip(novels_file_list, all_novels_chapters_list):
                process_novel_tasks.append(
                    # 这个函数会获取每本小说的所有章节内容，耗时任务
                    process_novel_chapters(write_file_semaphore, crawler, session, novel_chapters_list, file_path)
                )
            # 等待并发写入完成
            await asyncio.gather(*process_novel_tasks)
            print("所有小说写入完成")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())