import streamlit as st
import pyodbc
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns 
import matplotlib.colors as mcolors 


# Thiết lập thông tin kết nối
server = 'DESKTOP-235JCGC\MSSQLSERVER01'
database = 'Booking'
username = 'sa'
password = '12'
driver = '{ODBC Driver 17 for SQL Server}'

# Kết nối đến SQL Server
conn = pyodbc.connect(f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}')
cursor = conn.cursor()

# Lấy dữ liệu từ các bảng Hotel, City và Review
hotel_query = "SELECT * FROM Hotel"
city_query = "SELECT * FROM City"
review_query = "SELECT * FROM Review"

# Đọc dữ liệu vào DataFrame
df_hotel = pd.read_sql(hotel_query, conn)
df_city = pd.read_sql(city_query, conn)
df_review = pd.read_sql(review_query, conn)

# Điều kiện phân loại vùng miền
Conditions = [
    df_city['City'].isin(["Hà Nội", "Thành phố Hải Phòng", "Hạ Long", "Cao Bằng", "Hà Giang", "Ninh Bình"]),
    df_city['City'].isin(["Đà Nẵng", "Huế", "Hội An", "Quảng Ngãi", "Quy Nhơn", "Nha Trang", "Đà Lạt", "Tuy Hoà", "Phan Rang", "Ðồng Hới"]),
    df_city['City'].isin(["TP. Hồ Chí Minh", "Cần Thơ", "Vũng Tàu", "Phú Quốc"])
]

Result = ["Miền Bắc", "Miền Trung", "Miền Nam"]
df_city['Region'] = np.select(Conditions, Result, default="Khác")

# Phân loại giá phòng
def price_segment(price):
    if price <= 1000000:
        return "Giá thấp"
    elif 1000000 < price <= 5000000:
        return "Giá trung bình"
    else:
        return "Giá cao"

df_hotel['PriceSegment'] = df_hotel['Price'].apply(price_segment)

# Tạo từ điển ánh xạ từ CityID trong bảng City
city_mapping = df_city.set_index('CityID').to_dict(orient='index')

# Ánh xạ thông tin từ bảng City vào bảng Hotel thông qua CityID
df_hotel = df_hotel.join(df_hotel['CityID'].map(lambda x: city_mapping.get(x, {})), rsuffix='_City')
df_hotel['Region'] = df_hotel['CityID'].map(lambda x: city_mapping.get(x, {}).get('Region', 'Unknown'))

# Ánh xạ thông tin từ bảng Hotel vào bảng Review thông qua HotelID
hotel_mapping = df_hotel.set_index('HotelID').to_dict(orient='index')
df_review = df_review.join(df_review['HotelID'].map(hotel_mapping).apply(pd.Series), rsuffix='_Hotel')

# Xóa các cột trùng lặp
df_review = df_review.loc[:, ~df_review.columns.duplicated()]

import streamlit as st

# Tiêu đề màu xanh biển đậm, in hoa, chiều rộng hết cỡ và khoảng cách dưới rộng hơn
st.markdown("<h1 style='text-align: center; color: #003366; width: 100%; margin-bottom: 20px;'>HOTEL ANALYSIS</h1>", unsafe_allow_html=True)

### TẠO BIỂU ĐỒ

# 1. Số lượng khách sạn và giá trung bình theo thành phố (Thanh + Đường)
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Trích xuất giá trị 'City' từ mỗi dictionary trong cột 'CityID_City'
df_hotel['City'] = df_hotel['CityID_City'].apply(lambda x: x['City'] if isinstance(x, dict) else None)

# Tính số lượng khách sạn theo thành phố
city_counts = df_hotel['City'].value_counts()

# Tính giá trung bình theo thành phố
city_avg_price = df_hotel.groupby('City')['Price'].mean()

# Đồng bộ hóa thứ tự thành phố giữa city_counts và city_avg_price
city_avg_price = city_avg_price.reindex(city_counts.index)

# Khởi tạo figure và trục chính
fig, ax1 = plt.subplots(figsize=(13, 7))

# Tạo dải màu từ đậm đến nhạt
norm = plt.Normalize(vmin=city_counts.min(), vmax=city_counts.max())  # Chuẩn hóa số lượng khách sạn
cmap = plt.cm.Blues  # Chọn colormap (màu xanh lam)

# Vẽ biểu đồ cột cho số lượng khách sạn với màu sắc từ đậm đến nhạt
bars = ax1.bar(city_counts.index, city_counts.values, color=cmap(norm(city_counts.values)), edgecolor='black', label='Số lượng khách sạn')

# Hiển thị giá trị trên từng cột
for bar in bars:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width() / 2, yval + 5, int(yval), ha='center', va='bottom', fontsize=9)

# Thiết lập trục y1 (số lượng khách sạn)
ax1.set_xlabel('Thành phố', fontsize=15)
ax1.set_ylabel('Số lượng khách sạn', fontsize=12)
ax1.tick_params(axis='y')
ax1.set_xticks(np.arange(len(city_counts.index)))
ax1.set_xticklabels(city_counts.index, rotation=45, ha='right', fontsize=10)

# Tạo trục phụ (y2) - Giá trung bình
ax2 = ax1.twinx()
ax2.plot(city_avg_price.index, city_avg_price.values, color='orange', marker='o', linestyle='-', linewidth=2, label='Giá trung bình')
ax2.set_ylabel('Giá trung bình (VNĐ)', fontsize=12, color='orange')
ax2.tick_params(axis='y', labelcolor='red')

# Hiển thị giá trung bình trên từng điểm trên biểu đồ đường
for i, price in enumerate(city_avg_price):
    ax2.text(i, price, f"{price:,.0f}", color='orange', ha='center', va='bottom', fontsize=10)

# Thêm tiêu đề và lưới
plt.title('Số lượng khách sạn và giá trung bình theo thành phố', fontsize=16)
ax1.grid(axis='y', linestyle='--', alpha=0.7)

# Thêm chú thích
fig.legend(loc='upper right', bbox_to_anchor=(0.9, 0.9), fontsize=10)

# Căn chỉnh đồ họa
plt.tight_layout()

# Hiển thị biểu đồ trên Streamlit
st.pyplot(fig)  # Sử dụng st.pyplot để hiển thị biểu đồ trong Streamlit


##########################
# 2.Top 5 khách sạn có giá cao nhất

import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

# Sắp xếp các khách sạn theo giá từ cao đến thấp
df_sorted = df_hotel[['HotelName', 'Price', 'City']].sort_values(by='Price', ascending=False)

# Chọn top 5 khách sạn
top_n = 5
df_top_n = df_sorted.head(top_n)

# Tạo cột kết hợp tên khách sạn và thành phố để dễ dàng hiển thị
df_top_n['Hotel_with_City'] = df_top_n['HotelName'] + ' (' + df_top_n['City'] + ')'

# Vẽ biểu đồ bằng Seaborn
fig, ax = plt.subplots(figsize=(14, 6))  # Tăng chiều rộng biểu đồ
sns.barplot(
    x='Price', 
    y='Hotel_with_City', 
    data=df_top_n, 
    palette='coolwarm', 
    ax=ax, 
    width=0.8
)

# Thêm giá trị vào mỗi thanh bên ngoài
for index, value in enumerate(df_top_n['Price']):
    ax.text(
        value + 1e6, index, f'{value:,}',  # Hiển thị giá trị với định dạng ngăn cách bằng dấu phẩy
        color='black', ha="left", va="center", fontsize=10
    )

# Thêm tiêu đề và các nhãn
ax.set_title(f'Top {top_n} Khách Sạn có giá cao nhất', fontsize=16)
ax.set_xlabel('Giá', fontsize=12)
ax.set_ylabel('Khách Sạn (Thành Phố)', fontsize=12)
ax.set_xlim(0, 1.3e8)  # Điều chỉnh giới hạn của trục x

# Hiển thị biểu đồ trên ứng dụng Streamlit
st.pyplot(fig)



#3. Top 5 khách sạn có nhiều lượt đánh giá nhất
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

# Trích xuất giá trị 'City' từ mỗi dictionary trong cột 'CityID_City'
df_review['City'] = df_hotel['CityID_City'].apply(lambda x: x['City'] if isinstance(x, dict) else None)

# Sắp xếp các khách sạn theo số lượng đánh giá từ cao đến thấp
df_sorted = df_review[['HotelName', 'ReviewsCount', 'City']].sort_values(by='ReviewsCount', ascending=False)

# Chọn top 5 khách sạn
top_n = 5
df_top_n = df_sorted.head(top_n)

# Tạo cột kết hợp tên khách sạn và thành phố để dễ dàng hiển thị
df_top_n['Hotel_with_City'] = df_top_n['HotelName'] + ' (' + df_top_n['City'] + ')'

# Vẽ biểu đồ bằng Seaborn
fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(
    x='ReviewsCount', 
    y='Hotel_with_City', 
    data=df_top_n, 
    palette='coolwarm', 
    ax=ax
)

# Thêm giá trị vào mỗi thanh
for index, value in enumerate(df_top_n['ReviewsCount']):
    ax.text(
        value, index, f'{value}', 
        color='black', ha="left", va="center", fontsize=10
    )

# Thêm tiêu đề và nhãn
ax.set_title(f'Top {top_n} Khách Sạn có nhiều lượt đánh giá', fontsize=16)
ax.set_xlabel('Số Lượng Đánh Giá', fontsize=12)
ax.set_ylabel('Khách Sạn (Thành Phố)', fontsize=12)

# Tăng cường hiển thị bằng cách giảm khoảng cách giữa các nhãn
fig.tight_layout()

# Hiển thị biểu đồ trên ứng dụng Streamlit
st.pyplot(fig)



#4. 'Điểm đánh giá trung bình và tổng số lượng đánh giá theo thành phố'
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import streamlit as st

# Tính tổng số lượng đánh giá và điểm đánh giá trung bình theo từng thành phố
city_stats = df_review.groupby('City').agg(
    TotalReviews=('ReviewsCount', 'sum'),  # Tổng số lượng đánh giá
    AvgScore=('Score', 'mean')             # Điểm đánh giá trung bình
).sort_values(by='TotalReviews', ascending=False)

# Sử dụng dải màu từ đậm đến nhạt dựa trên số lượng đánh giá
norm = mcolors.Normalize(vmin=city_stats['TotalReviews'].min(), vmax=city_stats['TotalReviews'].max())  # Chuẩn hóa giá trị
cmap = plt.cm.Blues  # Chọn dải màu Blues

# Vẽ biểu đồ
fig, ax1 = plt.subplots(figsize=(12, 6))

# Biểu đồ cột cho tổng số lượng đánh giá với màu sắc thay đổi
bars = ax1.bar(
    city_stats.index,                  # Trục x: Thành phố
    city_stats['TotalReviews'],        # Trục y: Tổng số lượng đánh giá
    color=cmap(norm(city_stats['TotalReviews'])),  # Màu sắc thay đổi theo số lượng đánh giá
    label='Tổng số lượng đánh giá',
    alpha=0.7
)

# Cài đặt trục Y bên trái
ax1.set_ylabel('Tổng số lượng đánh giá', color='blue', fontsize=12)
ax1.set_title('Điểm đánh giá trung bình và tổng số lượng đánh giá theo thành phố', fontsize=14)
ax1.set_xticks(range(len(city_stats.index)))  # Trục x là chỉ số của thành phố
ax1.set_xticklabels(city_stats.index, rotation=45, fontsize=10)  # Hiển thị tên thành phố

# Hiển thị số lượng trên cột
for bar in bars:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width() / 2, height + 10, f"{int(height)}", ha='center', va='bottom', fontsize=10, color='blue')

# Biểu đồ đường cho điểm đánh giá trung bình
ax2 = ax1.twinx()
ax2.plot(
    city_stats.index,                 # Trục x: Thành phố
    city_stats['AvgScore'],           # Trục y: Điểm đánh giá trung bình
    color='orange',                   # Màu đường
    marker='o',                       # Thêm marker
    linewidth=2,                      # Độ dày đường
    label='Điểm đánh giá trung bình'
)

# Cài đặt trục Y bên phải
ax2.set_ylabel('Điểm đánh giá trung bình', color='orange', fontsize=12)

# Hiển thị giá trị trên biểu đồ đường
for i, score in enumerate(city_stats['AvgScore']):
    ax2.text(i, score + 0.05, f"{score:.2f}", color='orange', ha='center', va='bottom', fontsize=10)

# Tối ưu layout
plt.tight_layout()

# Hiển thị biểu đồ trong ứng dụng Streamlit
st.pyplot(fig)


# 5. Phân khúc giá theo vùng miền 
import matplotlib.pyplot as plt
import streamlit as st

# Tính phân bố khách sạn theo phân khúc giá và vùng
region_price_segment = df_review.groupby(['Region', 'PriceSegment'])['HotelID'].count().unstack().fillna(0)

# Số lượng vùng
num_regions = len(region_price_segment.index)

# Tạo lưới biểu đồ
fig, axes = plt.subplots(nrows=(num_regions + 2) // 3, ncols=3, figsize=(15, 5 * ((num_regions + 2) // 3)))
axes = axes.flatten()  # Chuyển đổi lưới thành một mảng 1 chiều để tiện thao tác

# Vẽ Donut Chart cho từng vùng
for i, region in enumerate(region_price_segment.index):
    region_data = region_price_segment.loc[region]

    # Vẽ biểu đồ tròn dạng Donut
    wedges, texts, autotexts = axes[i].pie(region_data,
                                           labels=region_data.index,
                                           autopct='%1.1f%%',
                                           colors=['skyblue', 'orange', 'tomato'],
                                           startangle=90,
                                           wedgeprops={'width': 0.6})  # Hiệu ứng donut

    # Thêm tổng số khách sạn vào giữa biểu đồ
    total_hotels = region_data.sum()
    axes[i].text(0, 0, f'{int(total_hotels)}\nKhách sạn', ha='center', va='center', fontsize=12, color='black')

    # Thiết lập tiêu đề cho từng biểu đồ
    axes[i].set_title(f'Phân khúc giá tại {region}', fontsize=14)
    axes[i].set_ylabel('')  # Loại bỏ nhãn trục y

# Loại bỏ các ô thừa
for j in range(i + 1, len(axes)):
    axes[j].axis('off')  # Tắt các ô không sử dụng

# Điều chỉnh bố cục
plt.tight_layout()

# Hiển thị biểu đồ trong ứng dụng Streamlit
st.pyplot(fig)




# 6. Phân bố điểm đánh giá theo số lượng khách sạn
import streamlit as st
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Sử dụng điểm đánh giá từ bảng df_review
data = df_review['Score']  
bins = 7  # Số lượng bins
counts, bin_edges = np.histogram(data, bins=bins)
bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

# Tạo bảng màu cho từng bin
colors = sns.color_palette("coolwarm", len(bin_centers))  # Dải màu coolwarm

# Vẽ biểu đồ histogram với khoảng cách giữa các cột
plt.figure(figsize=(10, 6))
bar_width = (bin_edges[1] - bin_edges[0]) * 0.8  # Giảm chiều rộng cột để tạo khoảng cách
for i in range(len(bin_centers)):
    plt.bar(bin_centers[i], counts[i],
            width=bar_width,  # Điều chỉnh độ rộng
            color=colors[i])
    # Thêm giá trị số lượng khách sạn vào mỗi cột
    plt.text(bin_centers[i], counts[i] + 0.1, str(counts[i]), ha='center', va='bottom', fontsize=10)

# Thêm tiêu đề và nhãn
plt.xlabel('Điểm đánh giá', fontsize=12)
plt.ylabel('Số lượng khách sạn', fontsize=12)
plt.title('Phân bố điểm đánh giá theo số lượng khách sạn', fontsize=14)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.legend()  # Hiển thị chú thích

# Hiển thị biểu đồ trên Streamlit
st.pyplot(plt)  # Streamlit sẽ hiển thị biểu đồ matplotlib



#7. Boxplot Phân bố mức độ đánh giá của khách sạn theo thành phố
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Đảm bảo rằng cột 'AvgReview' có thứ tự cụ thể
review_order = ['Tốt', 'Rất tốt', 'Tuyệt vời', 'Tuyệt hảo', 'Xuất sắc']
df_review['AvgReview'] = pd.Categorical(df_review['AvgReview'], categories=review_order, ordered=True)

# Vẽ boxplot với cột 'AvgReview' đã được sắp xếp
plt.figure(figsize=(14, 8))
sns.boxplot(x='City', y='AvgReview', data=df_review, palette='coolwarm')
plt.title('Phân bố mức độ đánh giá của khách sạn theo thành phố', fontsize=16)
plt.xlabel('Thành phố', fontsize=12)
plt.ylabel('Mức độ đánh giá', fontsize=12)
plt.xticks(rotation=45, ha='right')

# Hiển thị biểu đồ trên Streamlit
st.pyplot(plt)  # Streamlit sẽ hiển thị biểu đồ matplotlib



#8. Boxplot của các điểm đánh giá theo tiêu chí
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Lọc các cột điểm đánh giá từ bảng df_review sau khi đã ánh xạ
score_columns = ['Facilities', 'Comfort', 'Staff', 'FreeWifi', 'ValueforMoney', 'Cleanliness', 'Location']

# Vẽ boxplot
plt.figure(figsize=(10, 6))
sns.boxplot(data=df_review[score_columns])

# Thêm tiêu đề và nhãn
plt.title('Boxplot của các điểm đánh giá theo tiêu chí', fontsize=14)
plt.xlabel('Tiêu chí', fontsize=12)
plt.ylabel('Điểm đánh giá', fontsize=12)

# Hiển thị biểu đồ trên Streamlit
st.pyplot(plt)  # Streamlit sẽ hiển thị biểu đồ matplotlib




#. 9.Mối quan hệ giữa Giá, Số lượng đánh giá và Điểm đánh giá
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Chọn các cột cần thiết từ bảng đã ánh xạ (df_review)
correlation_data = df_review[['Price', 'ReviewsCount', 'Score', 'Facilities', 'Comfort', 'Staff', 'FreeWifi', 'ValueforMoney', 'Cleanliness', 'Location']]

# Tính toán ma trận tương quan
corr_matrix = correlation_data.corr()

# Vẽ heatmap
plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap='Blues', fmt='.2f', linewidths=0.5)

# Thêm tiêu đề
plt.title('Mối quan hệ giữa Giá, Số lượng đánh giá và Điểm đánh giá', fontsize=14)

# Hiển thị biểu đồ trên Streamlit
st.pyplot(plt)  # Streamlit sẽ hiển thị biểu đồ matplotlib


