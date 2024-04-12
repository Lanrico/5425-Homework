import whoosh
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser
import urllib.request as urllib2
from lxml import cssselect, html
import sqlite3

response = urllib2.urlopen(
    'https://pubmed.ncbi.nlm.nih.gov/?term=glioma&filter=simsearch1.fha&filter=years.2019-2019&format=abstract')

htmlString = response.read()

# connect to the database
conn = sqlite3.connect('homework.db')
c = conn.cursor()


# def get_abstracts(html_content):
#     doc_html = html.fromstring(html_content)
#     select = cssselect.CSSSelector("div.abstract-content.selected *")
#     # abstracts = [el.get('href') for el in select(doc_html)]
#     abstracts = [el for el in select(doc_html)]
#     return set(abstracts)

def get_abstracts(html_content):
    # 解析HTML内容
    doc_html = html.fromstring(html_content)

    # 创建一个字典来存储标题和摘要
    abstracts = {}

    # 遍历每个class为article-overview的article元素
    articles = doc_html.cssselect('article.article-overview')
    for article in articles:
        # 获取标题（即<a>标签的文本内容）

        title_link = article.cssselect('h1.heading-title a')
        if title_link:
            article_title = title_link[0].text_content().strip()  # 取第一个a标签的文本，并去除空白字符

            # 在同一个article中找到class为abstract-content selected的div
            abstract_div = article.cssselect('div.abstract-content.selected')
            if abstract_div:
                # 检查是否有多个<p>元素
                paragraphs = abstract_div[0].cssselect('p')
                if paragraphs:
                    # 合并所有p元素的文本，如果有多个，用换行符连接它们
                    cleaned_abstract = (re.sub(r'\s+', ' ', p.text_content().strip()) for p in paragraphs)
                    abstract_text = '\n'.join(p for p in cleaned_abstract)
                    # 存储标题和摘要到字典中
                    abstracts[article_title] = abstract_text

                    # ==== Insert data ====
                    c.execute("INSERT INTO article (title, abstract) VALUES (?, ?)", (article_title, abstract_text))

        # ==== Commmit to save the change(s) ====
        conn.commit()
    return abstracts


abstract_dict = get_abstracts(htmlString)
print(abstract_dict)
for key, value in abstract_dict.items():
    print(f"{key}: {value}")
print(len(abstract_dict))

# pageList = []
# count = 0
# for abstract in abstractList:
#     if count > 10:
#         break
#     match = re.search(r'http+', abstract)
#     if match is None:
#         break
#     pageResponse = urllib2.urlopen(abstract)
#     pageHtmlString = pageResponse.read()
#     pageList.append(pageHtmlString)
#
#     count = count + 1
# try:
#     schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)
#
#     #Creating your Index object in a directory, following schema defined above.
#     #Here we save the Index object in a subfolder named 'indexdir' in your working directory
#     ix = create_in(".", schema)
#
#     #Once your Index object is ready, you can add documents to the index using IndexWriter
#     writer = ix.writer()
#     for i in range(len(pageList)):
#         print("adding document " + str(i))
#         writer.add_document(title=u"document " + str(i), path=u".",
#                             content=pageList[i])  #python iterator i starting from 0
#
#     #Calling commit() on the IndexWriter after adding all documents, and it will update the index
#     writer.commit(optimize=True)
#
#     #So far you have defined a schema, created an Index object, and added some documents. Following we will try search
#     #using the index
#
#     #similar to adding document using writer, you need to create a searcher object to search
#     searcher = ix.searcher()
#
#     parser = QueryParser("content", ix.schema)
#     stringquery = parser.parse("Sydney Student")
#     results = searcher.search(stringquery)
#     print("search result:")
#     print(results)
#     for r in results:
#         print(r)
# except:
#     print("Error")
#
# # print(pageList)
#
# emailList = []
#
# for i in pageList:
#     emails = re.findall(r'[\w.-]+@[\w.-]+\.[\w.-]+', i.decode())  ## ['alice@google.com', 'bob@abc.com']
#     if len(emails) > 0:
#         emailList = emailList + emails
#
# print(emailList)
