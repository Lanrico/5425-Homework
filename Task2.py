
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud

conn = sqlite3.connect('homework.db')
c = conn.cursor()

# 执行SQL查询，选择abstract和year列
c.execute('SELECT abstract, year FROM article')

# 读取所有结果
results = c.fetchall()

# 用字典来分组数据，键为年份，值为对应年份的abstract列表
grouped_by_year = {}
for abstract, year in results:
    if year in grouped_by_year:
        grouped_by_year[year].append(abstract)
    else:
        grouped_by_year[year] = [abstract]

years = sorted(list(grouped_by_year.keys()))

for year in years:
    grouped_by_year[year] = ' '.join(str(abstracts) for abstracts in grouped_by_year[year])

x, y = np.ogrid[:300, :300]

mask = (x - 150) ** 2 + (y - 150) ** 2 > 130 ** 2
mask = 255 * mask.astype(int)


# 创建一个图形和子图集，每行两个图
fig, axs = plt.subplots(nrows=2, ncols=3, figsize=(15, 10))  # 调整大小适应五个词云
axs = axs.flatten()  # 将二维的子图数组转化为一维，便于迭代访问

# 每个年份的词云一个图
for i, year in enumerate(years):
    wc = WordCloud(background_color="white", repeat=True, mask=mask)
    wc.generate(grouped_by_year[year])

    axs[i].imshow(wc, interpolation="bilinear")
    axs[i].set_title(f"Year {year}")
    axs[i].axis("off")

# 最后一个子图（第六个，我们只需要五个）显示所有年份的词云
wc = WordCloud(background_color="white", repeat=True, mask=mask)
wc.generate(' '.join(grouped_by_year.values()))

axs[-1].imshow(wc, interpolation="bilinear")
axs[-1].set_title(f"All years from 2020 to 2024")
axs[-1].axis("off")


plt.tight_layout()  # 自动调整子图参数，以给定的填充
plt.show()