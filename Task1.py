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

    # Create a dictionary to store the title and summary
    # abstracts = {}

    total_page_num = doc_html.cssselect('label.of-total-pages')[0].text_content().split(" ")[-1]

    # Iterate over each article element with class article-overview
    articles = doc_html.cssselect('article.article-overview')
    if len(articles) == 0:
        print('No articles found')
        return -1
    for article in articles:
        # Get the title (i.e. the text content of the <a> tag)
        title_link = article.cssselect('h1.heading-title a')
        if not title_link:
            print('No title found')
            return -1
        if title_link:
            # Take the text of the first a tag and remove the whitespace characters
            article_title = title_link[0].text_content().strip()

            # Check if the article is retracted
            if 'retract' in article_title.lower():
                print(f'{article_title} is retracted, skipping...')
                articles.remove(article)
                continue

            # Check if the article title is in the database
            c.execute("SELECT * FROM article WHERE title = ?", (article_title,))
            if c.fetchone():
                print(f'{article_title} already exists in the database, skipping...')
                articles.remove(article)
                continue

            # Find the div with class abstract-content selected in the same article.
            abstract_div = article.cssselect('div.abstract-content.selected')
            if abstract_div:
                # Check for multiple <p> elements
                paragraphs = abstract_div[0].cssselect('p')
                if paragraphs:
                    # Merge the text of all p elements, and if there are more than one, join them with newlines.
                    cleaned_abstract = (re.sub(r'\s+', ' ', p.text_content().strip()) for p in paragraphs)
                    abstract_text = '\n'.join(p for p in cleaned_abstract)

                    # Insert data. If the database is locked then retry
                    attempt = 0
                    while attempt < 10:
                        try:
                            c.execute("INSERT INTO article (title, abstract, year) VALUES (?, ?, ?)",
                                      (article_title, abstract_text, year))
                            break
                        except sqlite3.OperationalError:
                            print('Database is locked, retrying...')
                            attempt += 1

    # Commit to save the changes
    conn.commit()
    print(f'Data inserted successfully, {len(articles)} articles inserted.')
    # return abstracts
    return total_page_num


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
