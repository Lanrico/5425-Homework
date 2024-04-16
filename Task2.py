
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud

conn = sqlite3.connect('homework.db')
c = conn.cursor()

# Execute the SQL query, selecting the abstract and year columns
c.execute('SELECT abstract, year FROM article')

# Read all results
results = c.fetchall()

# Use a dictionary to group the data, with the key being the year and the value being the abstract list of the corresponding year
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


# Create a collection of graphs and subgraphs, two graphs per row
fig, axs = plt.subplots(nrows=2, ncols=3, figsize=(15, 10))  # Resize to fit five word clouds
axs = axs.flatten()  # Converts two-dimensional subgraph arrays to one-dimensional for easy iterative access

# One graph for each year's word cloud
for i, year in enumerate(years):
    wc = WordCloud(background_color="white", repeat=True, mask=mask)
    wc.generate(grouped_by_year[year])

    axs[i].imshow(wc, interpolation="bilinear")
    axs[i].set_title(f"Year {year}")
    axs[i].axis("off")

# The last subplot shows word clouds for all years
wc = WordCloud(background_color="white", repeat=True, mask=mask)
wc.generate(' '.join(grouped_by_year.values()))

axs[-1].imshow(wc, interpolation="bilinear")
axs[-1].set_title(f"All years from 2020 to 2024")
axs[-1].axis("off")


plt.tight_layout()  # Automatically adjusts subplot parameters to a given fill
plt.show()