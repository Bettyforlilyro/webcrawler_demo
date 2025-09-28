import asyncio
import os
import random
import re
from datetime import datetime
from enum import Enum
from typing import List, Any, Union

import aiofiles
import aiohttp
from bs4 import BeautifulSoup

from novel_crawler.NovelCrawlerFactory import BaseNovelCrawler, SortStrategy
from novel_crawler.NovelCrawlerFactory import NovelMetadata


class UjNovelCrawler(BaseNovelCrawler):

    base_url = "http://www.ujxsw.org/"
    tags_list = ["wuxia", "dushi", "xuanhuan", "lishi", "youxi", "kehuan", "yanqing"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.1000.0 Safari/537.36",
        "Referer": "http://www.ujxsw.org/",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async def _prepare_resources(self, session=None, semaphore=None):
        """准备session和semaphore资源"""
        should_close_session = False

        if session is None:
            session = aiohttp.ClientSession(headers=self.headers)
            should_close_session = True     # 需要最后手动释放session

        if semaphore is None:
            semaphore = asyncio.Semaphore(10)   # 默认并发数

        return session, semaphore, should_close_session

    # 请确保输入url为小说详情页的url，如《大丰打更人》的详情页url为：http://www.ujxsw.org/book/1022/
    async def get_novel_metadata_async(
            self,
            url: str,
            session: aiohttp.ClientSession = None,
            semaphore: asyncio.Semaphore = None
    ) -> NovelMetadata:
        session, semaphore, should_close_session = await self._prepare_resources(session, semaphore)
        try:
            novel_id = (url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]).replace('.html', '')
            async with semaphore:
                async with session.get(url) as response:
                    text = await response.text()
                    novel_info = BeautifulSoup(text, 'html.parser').find('div', id='maininfo').find('div', id='bookinfo')
                    novel_left = novel_info.find('div', class_='bookleft')
                    novel_right = novel_info.find('div', class_='bookright')
                    novel_cover_url = novel_left.find('img')['src']
                    h1 = novel_right.find('h1')
                    novel_title = h1.contents[0].strip()
                    novel_author = h1.find('em').find('a').get_text()
                    count_div = novel_right.find('div', id='count')
                    spans = count_div.find_all('span', class_='pd_r')
                    novel_tag = spans[0].get_text().strip()
                    clicks = spans[1].get_text().strip()
                    recommends = spans[2].get_text().strip()
                    favorites = spans[3].get_text().strip()
                    novel_word_count = spans[4].get_text().strip()
                    if 'K' in novel_word_count:
                        novel_word_count = novel_word_count.replace('K', '')
                        novel_word_count = int(novel_word_count) * 1000
                    elif 'W' in novel_word_count:
                        novel_word_count = novel_word_count.replace('W', '')
                        novel_word_count = int(novel_word_count) * 10000
                    else:
                        novel_word_count = int(novel_word_count)
                    intro_div = novel_right.find('div', id='bookintro')
                    intro_lines = [line.strip() for line in intro_div.stripped_strings]
                    novel_description = ''.join(intro_lines)
                    latest_div = novel_right.find('div', class_='new')
                    latest_chapter_tag = latest_div.find('span', class_='new_t').find('a')
                    latest_chapter_title = latest_chapter_tag.get_text()
                    latest_chapter_url = latest_chapter_tag['href']
                    update_span = latest_div.find('span', class_='new_p')
                    novel_update_time = update_span.get_text().replace('更新时间：', '').strip()
                    diff_days = datetime.now() - datetime.strptime(novel_update_time, '%Y-%m-%d')
                    novel_status = '完结' if diff_days.days > 30 else '连载'
                    novel_catalog_url = novel_right.find('div', class_='motion').find('a', string='目录列表')['href']
                    detail_info = NovelMetadata(
                        id=novel_id,
                        title=novel_title,
                        author=novel_author,
                        tag=novel_tag,
                        status=novel_status,
                        word_count=novel_word_count,
                        update_time=novel_update_time,
                        description=novel_description,
                        cover_url=novel_cover_url,
                        catalog_url=self.base_url[:-1] + novel_catalog_url
                    )
                    return detail_info
        except Exception as e:
            print(f"获取小说具体信息失败：{e}")
            # 返回默认值
            detail_info = NovelMetadata(
                id="",
                title="",
                author="",
                tag="",
                status="",
                word_count=0,
                update_time="",
                description="",
                cover_url="",
                catalog_url=""
            )
            return detail_info
        finally:
            if should_close_session:
                await session.close()

    # 请确保输入的章节列表url是目录列表的url，比如《大丰打更人》的目录列表url为：http://www.ujxsw.org/read/1022/
    async def get_novel_chapters_list_async(
            self,
            url: str,
            session: aiohttp.ClientSession = None,
            semaphore: asyncio.Semaphore = None
    ) -> list[tuple[str, str]]:
        session, semaphore, should_close_session = await self._prepare_resources(session, semaphore)
        try:
            async with semaphore:
                async with session.get(url) as response:
                    response.encoding = 'utf-8'
                    text = await response.text()
                    soup = BeautifulSoup(text, 'html.parser')
                    chapter_list_ul = soup.find('div', id='readerlist').find('ul')
                    li_list = chapter_list_ul.find_all('li')
                    chapters_list = []
                    for li in li_list:
                        if li.get('class') and 'fj' in li['class']:
                            continue
                        a_tag = li.find('a')
                        if a_tag:
                            chapter_title = a_tag.get_text(strip=True)
                            chapter_url = a_tag['href']
                            chapter_url = self.base_url[:-1] + chapter_url
                            chapters_list.append((chapter_title, chapter_url))
                    return chapters_list
        except Exception as e:
            print(f"获取小说章节列表失败：{e}")
            # 返回默认值
            return []
        finally:
            if should_close_session:
                await session.close()

    # 请确保输入的章节url是章节详情的url，比如《大丰打更人》的某一章节url为：'http://www.ujxsw.org/read/1022/28248683.html'
    async def get_novel_chapter_content_async(
            self,
            chapter_url: str,
            session: aiohttp.ClientSession = None,
            semaphore: asyncio.Semaphore = None
    ) -> str:
        session, semaphore, should_close_session = await self._prepare_resources(session, semaphore)
        try:
            async with semaphore:
                async with session.get(chapter_url) as response:
                    response.encoding = 'utf-8'
                    text = await response.text()
                    soup = BeautifulSoup(text, 'html.parser')
                    content_div = soup.find('div', class_='read-content')
                    text = content_div.get_text(separator='\n', strip=True)
                    lines = text.split('\n')
                    cleaned_content = []
                    ad_keywords = ['最新网址', '免费小说无弹窗', '悠久小説網', '全集TXT电子书免费下载']
                    for i, line in enumerate(lines):
                        if (i <= 3 or i >= (len(lines) - 3)) and any(keyword in line for keyword in ad_keywords):
                            continue
                        cleaned_content.append(line)
                    return '\n'.join(cleaned_content)
        except Exception as e:
            print(f"获取小说章节列表失败：{e}")
            # 返回默认值
            return ""
        finally:
            if should_close_session:
                await session.close()

    async def get_novel_list_by_tag_async(
            self,
            tag: str,
            top_n: int,
            sort_method: SortStrategy = None,
            session: aiohttp.ClientSession = None,
            semaphore: asyncio.Semaphore = None
    ) -> list[tuple[str, str, str]]:    # TODO 按照SortStrategy排序以及返回top_n本小说的逻辑尚未实现
        if tag not in self.tags_list:
            print(f"{tag} 不在标签列表中")
            return []
        session, semaphore, should_close_session = await self._prepare_resources(session, semaphore)
        try:
            tag_url = self.base_url + tag + '/'
            novel_links = []
            # 异步获取所有分页链接
            async with session.get(tag_url) as response:
                # 先获取总页数
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                page_link_div = soup.find('div', id='pagelink')
                match = re.search(r'第\s*\d+\s*/\s*(\d+)\s*页', page_link_div.get_text() if page_link_div else '')
                total_pages = int(match.group(1)) if match else 0

                async def fetch_with_delay(fetch_session, url):
                    async with semaphore:   # 这里使用外层的semaphore控制并发数量
                        async with fetch_session.get(url) as rsp:
                            fetch_content = await rsp.text()
                            await asyncio.sleep(random.uniform(0.01, 0.15))
                            return fetch_content

                # 异步获取所有分页搜索结果页面内容，TODO 此处total_pages可能太多，需要考虑分页？
                tasks = [fetch_with_delay(session, tag_url + str(page) + '/') for page in
                         range(1, total_pages + 1)]
                pages_content = await asyncio.gather(*tasks)
                # 解析所有页面内容，提取小说链接
                for content in pages_content:
                    soup = BeautifulSoup(content, 'html.parser')
                    for dl in soup.select('div#sitembox dl'):
                        a_tag = dl.select_one('dd h3 a')
                        if a_tag:
                            novel_title = a_tag.get_text(strip=True)
                            novel_detail_url = a_tag['href']
                            author_tag = dl.select_one('dd.book_other span a')
                            author = author_tag.get_text(strip=True) if author_tag else '佚名'
                            novel_links.append((novel_title, author, novel_detail_url))
                return novel_links

        except Exception as e:
            print(f"获取标签相关的小说列表失败：{e}")
            return []
        finally:
            if should_close_session:
                await session.close()

    async def get_novel_list_by_author_async(
            self,
            author: str,
            session: aiohttp.ClientSession = None,
            semaphore: asyncio.Semaphore = None
    ) -> list[tuple[str, str, str]]:
        search_url = self.base_url + 'author/' + author
        session, semaphore, should_close_session = await self._prepare_resources(session, semaphore)
        try:
            async with semaphore:
                async with session.get(search_url) as response:
                    text = await response.text()
                    if response.status != 200:
                        raise ValueError('请求失败')
                    if text is None or text == '':
                        print("获取到的内容为空，请换一个作者试试")
                        return []
                    soup = BeautifulSoup(text, 'html.parser')
                    rows = soup.select('table.booklists tbody tr')
                    result = []
                    for row in rows:
                        title_cell = row.find_all('td')[1]
                        title_link = title_cell.find('a')
                        if not title_link:
                            continue
                        title = title_link.get_text(strip=True)
                        url = title_link['href']
                        result.append((title, author, url))
                    return result
        except Exception as e:
            print(f"获取作者相关小说列表失败：{e}")
            return []
        finally:
            if should_close_session:
                await session.close()

    async def get_novel_list_by_keyword_async(
            self,
            keyword: str,
            top_n: int = 5,
            session: aiohttp.ClientSession = None,
            semaphore: asyncio.Semaphore = None
    ) -> list[tuple[str, str, str]]:
        search_url = self.base_url + 'searchbooks.php'
        req_body = {
            'searchkey': keyword
        }
        result = []
        session, semaphore, should_close_session = await self._prepare_resources(session, semaphore)
        try:
            async with semaphore:
                async with session.post(search_url, data=req_body) as response:
                    text = await response.text()
                    soup = BeautifulSoup(text, 'html.parser')
                    novel_items = soup.select('div.shulist ul')
                    if not novel_items:
                        raise ValueError('未找到相关小说')
                    for i, ul in enumerate(novel_items):
                        if i >= top_n:
                            break
                        # 提取书名和详情页链接
                        novel_title_tag = ul.select_one('li.three a')
                        if not novel_title_tag:
                            continue
                        novel_title = novel_title_tag.get_text(strip=True)
                        detail_url = self.base_url[:-1] + novel_title_tag['href']
                        author_tag = ul.select_one('li.four a')
                        author = author_tag.get_text(strip=True) if author_tag else '佚名'
                        result.append((novel_title, author, detail_url))
                    return result
        except Exception as e:
            print(f"获取作者相关小说列表失败：{e}")
            return []
        finally:
            if should_close_session:
                await session.close()

    async def write_novel_content_to_file(
            self,
            url: str,
            file_path: str,
            session: aiohttp.ClientSession = None,
            semaphore: asyncio.Semaphore = None
    ):
        session, semaphore, should_close_session = await self._prepare_resources(session, semaphore)
        try:
            async with semaphore:
                novel_detail = await self.get_novel_metadata_async(url, session, semaphore)
                novel_catalog_url = novel_detail.catalog_url
                novel_chapters_list = await self.get_novel_chapters_list_async(novel_catalog_url, session, semaphore)
                get_chapter_content_tasks = [self.get_novel_chapter_content_async(chapter_url, session, semaphore)
                                             for chapter_title, chapter_url in novel_chapters_list]
                chapters_content_list = await asyncio.gather(*get_chapter_content_tasks)

                async def create_file_if_not_exists(path):
                    from pathlib import Path
                    _file_path = Path(path)
                    if not _file_path.exists():
                        _file_path.parent.mkdir(parents=True, exist_ok=True)
                        async with aiofiles.open(_file_path, 'w', encoding='utf-8') as f:
                            pass
                novel_file_path = file_path + novel_detail.tag + '/' + novel_detail.title + '_' + novel_detail.author + '.txt'
                await create_file_if_not_exists(novel_file_path)
                async with aiofiles.open(novel_file_path, 'a', encoding='utf-8') as f:
                    for (novel_chapter_title, _), chapter_content in zip(novel_chapters_list, chapters_content_list):
                        await f.write(f"{novel_chapter_title}\n{chapter_content}\n\n")
        except Exception as e:
            print(f"写入小说内容到文件失败：{e}")
        finally:
            if should_close_session:
                await session.close()

    # TODO 待完善
    async def get_novel_list_by_rank_async(self, rank_type: Union[str, Enum], top_n: int,
                                           session: aiohttp.ClientSession = None,
                                           semaphore: asyncio.Semaphore = None) -> list[tuple[str, str, str]]:
        return []

