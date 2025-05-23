import streamlit as st
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
import datetime
from pymongo import MongoClient
from wordcloud import WordCloud
import io
import re

# Koneksi ke MongoDB
uri = "mongodb+srv://bellaadha:bellaadha125_@cluster0.sajjj.mongodb.net/crawling?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client['crawling']
collection = db['data_kekerasan']

# Fungsi untuk menghitung jumlah artikel per bulan
def count_articles_per_month():
    month_count = defaultdict(int)
    for article in collection.find():
        published_date = article.get('published', '')
        if published_date:
            try:
                date_obj = datetime.datetime.strptime(published_date, "%a, %d %b %Y %H:%M:%S %Z")
                month_year = date_obj.strftime("%Y-%m")  # Format menjadi "YYYY-MM"
                month_count[month_year] += 1
            except ValueError:
                continue
    return month_count

# Fungsi untuk menghitung frekuensi kata kunci dalam artikel
def count_keywords_in_articles():
    keywords = ['kekerasan', 'sekolah', 'lingkungan', 'siswa', 'guru', 'insiden']
    keyword_count = {keyword: 0 for keyword in keywords}

    for article in collection.find():
        title = article.get('judul', '').lower()
        description = article.get('deskripsi', '').lower()
        for keyword in keywords:
            if keyword in title:
                keyword_count[keyword] += 1
            if keyword in description:
                keyword_count[keyword] += 1
    return keyword_count

# Fungsi untuk menghitung frekuensi kata-kata dari artikel (untuk Word Cloud)
def count_most_common_words():
    words = []

    # Mengambil artikel dari MongoDB
    for article in collection.find():
        title = article.get('judul', '')
        description = article.get('deskripsi', '')

        # Gabungkan judul dan deskripsi
        text = title + ' ' + description

        # Menghapus karakter selain huruf dan angka
        text = re.sub(r'[^a-zA-Z\s]', '', text.lower())  # Mengubah menjadi huruf kecil dan menghapus karakter non-alfabet
        words.extend(text.split())  # Memisahkan kata-kata dan menambahkannya ke dalam list

    # Menghitung frekuensi kata
    word_count = Counter(words)

    # Menampilkan 20 kata paling umum
    most_common_words = word_count.most_common(20)

    return most_common_words

# Fungsi untuk menyimpan visualisasi ke MongoDB
def save_visualization_to_mongo(wordcloud, title):
    # Mengonversi WordCloud ke gambar
    img = wordcloud.to_image()

    # Menyimpan gambar dalam format PNG ke buffer
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)  # Reset pointer ke awal buffer

    # Menyimpan gambar dalam bentuk binary ke MongoDB
    collection.insert_one({
        "image": buf.read(),
        "title": title,
        "date": datetime.datetime.now()
    })


# Fungsi untuk menampilkan Bar Chart Jumlah Artikel per Bulan
def plot_article_count_per_month():
    month_count = count_articles_per_month()

    # Urutkan berdasarkan bulan dan tahun (ascending)
    sorted_month_count = dict(sorted(month_count.items()))

    all_months = list(sorted_month_count.keys())
    all_counts = list(sorted_month_count.values())

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.bar(all_months, all_counts, color='lightblue')
    ax.set_xlabel('Bulan dan Tahun')
    ax.set_ylabel('Jumlah Artikel')
    ax.set_title('Jumlah Artikel per Bulan tentang Kekerasan di Sekolah')

    # Menampilkan grafik menggunakan Streamlit
    st.pyplot(fig)


# Fungsi untuk menampilkan Pie Chart Frekuensi Kata Kunci
def plot_keyword_frequency():
    keyword_count = count_keywords_in_articles()

    keywords = list(keyword_count.keys())
    counts = list(keyword_count.values())

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(counts, labels=keywords, autopct='%1.1f%%', startangle=140, colors=['lightblue', 'lightgreen', 'lightcoral', 'orange', 'yellow', 'pink'])
    ax.set_title('Distribusi Kata Kunci dalam Artikel Kekerasan di Sekolah')

    # Menampilkan grafik menggunakan Streamlit
    st.pyplot(fig)

# Fungsi untuk menampilkan Word Cloud
def plot_wordcloud():
    most_common_words = count_most_common_words()

    # Membuat list dari kata yang sering muncul
    text = ' '.join([item[0] for item in most_common_words])

    # Membuat word cloud
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text)

    # Menampilkan word cloud menggunakan Streamlit
    st.image(wordcloud.to_array(), use_container_width=True)

    # Menyimpan visualisasi ke MongoDB
    save_visualization_to_mongo(wordcloud, 'Word Cloud')

# Aplikasi Streamlit
def app():
    st.title('Visualisasi Artikel Kekerasan di Sekolah')

    st.sidebar.header('Pilih Visualisasi')
    options = ['Jumlah Artikel per Bulan', 'Frekuensi Kata Kunci', 'Word Cloud']  # Hapus opsi '20 Kata Paling Sering Muncul'
    choice = st.sidebar.selectbox('Pilih Tipe Visualisasi', options)

    if choice == 'Jumlah Artikel per Bulan':
        st.subheader('Jumlah Artikel per Bulan')
        plot_article_count_per_month()

    elif choice == 'Frekuensi Kata Kunci':
        st.subheader('Frekuensi Kata Kunci dalam Artikel')
        plot_keyword_frequency()

    elif choice == 'Word Cloud':
        st.subheader('Word Cloud Artikel Kekerasan di Sekolah')
        plot_wordcloud()

# Menjalankan aplikasi Streamlit
if __name__ == '__main__':
    app()
