import whoosh
from whoosh.fields import *
import urllib.request as urllib2
from lxml import cssselect, html
import sqlite3
import time
import threading

start_time = time.time()  # 获取当前时间
print('Start time:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time)))


def get_abstracts(url, year, conn):
    c = conn.cursor()

    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        print(f'HTTPError: {e.code}')
        return -1

    html_string = response.read()
    # 解析HTML内容
    doc_html = html.fromstring(html_string)

    # 创建一个字典来存储标题和摘要
    # abstracts = {}

    total_page_num = doc_html.cssselect('label.of-total-pages')[0].text_content().split(" ")[-1]

    # 遍历每个class为article-overview的article元素
    articles = doc_html.cssselect('article.article-overview')
    if len(articles) == 0:
        print('No articles found')
        return -1
    for article in articles:
        # 获取标题（即<a>标签的文本内容）

        title_link = article.cssselect('h1.heading-title a')
        if not title_link:
            print('No title found')
            return -1

        if title_link:
            article_title = title_link[0].text_content().strip()  # 取第一个a标签的文本，并去除空白字符
            # print(article_title)
            # 在同一个article中找到class为abstract-content selected的div
            abstract_div = article.cssselect('div.abstract-content.selected')
            if abstract_div:
                # 检查是否有多个<p>元素
                paragraphs = abstract_div[0].cssselect('p')
                if paragraphs:
                    # 合并所有p元素的文本，如果有多个，用换行符连接它们
                    cleaned_abstract = (re.sub(r'\s+', ' ', p.text_content().strip()) for p in paragraphs)
                    abstract_text = '\n'.join(p for p in cleaned_abstract)
                    # # 存储标题和摘要到字典中
                    # abstracts[article_title] = abstract_text

                    # Insert data 
                    c.execute("INSERT INTO article (title, abstract, year) VALUES (?, ?, ?)", (article_title, abstract_text, year))

    # Commit to save the changes
    conn.commit()
    print(f'Data inserted successfully, {len(articles)} articles inserted.')
    # return abstracts
    return total_page_num


# abstract_dict = get_abstracts(htmlString)
# print(abstract_dict)
# for key, value in abstract_dict.items():
#     print(f"{key}: {value}")
# print(len(abstract_dict))

def fetch_year_data(year):
    # connect to the database
    conn = sqlite3.connect('homework.db')
    attempt = 0
    print(f'Year {year}:')
    print(f'Page 1')
    total_page_num = get_abstracts(
        f'https://pubmed.ncbi.nlm.nih.gov/?term=glioma&filter=simsearch1.fha&filter=years.{year}-{year}&format=abstract&size=200',
        year, conn)
    # 错误处理
    while total_page_num == -1 and attempt < 10:
        print(f'Error, retrying... {attempt + 1}')
        total_page_num = get_abstracts(
            f'https://pubmed.ncbi.nlm.nih.gov/?term=glioma&filter=simsearch1.fha&filter=years.{year}-{year}&format=abstract&size=200',
            year, conn)
        attempt += 1

    for page in range(2, int(total_page_num) + 1):
        attempt = 0
        print(f'Page {page}')
        flag = get_abstracts(
            f'https://pubmed.ncbi.nlm.nih.gov/?term=glioma&filter=simsearch1.fha&filter=years.{year}-{year}&format=abstract&size=200&page={page}',
            year, conn)
        # 错误处理
        while flag == -1 and attempt < 10:
            print(f'Error, retrying... {attempt + 1}')
            flag = get_abstracts(
                f'https://pubmed.ncbi.nlm.nih.gov/?term=glioma&filter=simsearch1.fha&filter=years.{year}-{year}&format=abstract&size=200&page={page}',
                year, conn)
            attempt += 1
    # Close the connection
    conn.close()
    print(f'Year {year} finished.')


threads = []

# 创建线程
for year in range(2020, 2025):
    t = threading.Thread(target=fetch_year_data, args=(year,))
    t.start()
    threads.append(t)

# 等待所有线程完成
for t in threads:
    t.join()

print("All years have been processed.")

end_time = time.time()  # 获取当前时间
elapsed_time = end_time - start_time  # 计算经过的时间
print('End time:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time)))
print(f"Running time: {elapsed_time} seconds")
