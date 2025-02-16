import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px
from urllib.parse import urlparse, parse_qs

# Koneksi ke MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["sp_db"]
collection = db["users"]

# Ambil data dari MongoDB
data = list(collection.find({}))

# Buat DataFrame dari data yang diambil
df = pd.DataFrame(data)

# Konversi kolom 'tanggal' menjadi datetime
df["tanggal"] = pd.to_datetime(df["tanggal"])

# Judul aplikasi
st.title("Visualisasi Performa Pengguna")

# Mendapatkan parameter user_id dari URL
if st.query_params["user_id"]:
    selected_user = st.query_params["user_id"]
    user_name = st.query_params["name"]
    st.write(f"Nama: {user_name}")

    # Filter data berdasarkan user yang dipilih
    user_data = df[df["userID"] == selected_user]

    # Bar chart jumlah data berdasarkan nama gerakan
    st.header(f"Jumlah Data Berdasarkan Gerakan")
    bar_data = user_data["namaGerakan"].value_counts().sort_index()
    st.bar_chart(bar_data)

    # Pisahkan data yang benar dan salah
    correct_data = user_data[user_data["keterangan"] == "Sesuai"]
    incorrect_data = user_data[user_data["keterangan"] != "Sesuai"]

    # Buat DataFrame untuk jumlah gerakan benar dan salah
    correct_incorrect_counts = pd.DataFrame(
        {
            "Benar": correct_data["namaGerakan"].value_counts().sort_index(),
            "Salah": incorrect_data["namaGerakan"].value_counts().sort_index(),
        }
    ).fillna(0)

    # Bar chart jumlah gerakan benar dan salah
    st.header(f"Jumlah Gerakan Benar dan Salah")
    st.bar_chart(correct_incorrect_counts)

    # Pie chart jumlah data berdasarkan nama gerakan
    st.header(f"Jumlah Data Berdasarkan Gerakan")
    pie_data = user_data["namaGerakan"].value_counts().reset_index()
    pie_data.columns = ["namaGerakan", "jumlah"]
    fig = px.pie(
        pie_data, values="jumlah", names="namaGerakan", title="Distribusi Nama Gerakan"
    )
    st.plotly_chart(fig)

    # Grupkan data berdasarkan tanggal dan hitung jumlah gerakan sesuai
    correct_data_per_date = (
        correct_data.groupby(correct_data["tanggal"].dt.date)
        .size()
        .reset_index(name="jumlah")
    )

    # Line chart jumlah gerakan sesuai per tanggal
    st.header(f"Jumlah Gerakan Sesuai per Tanggal untuk: {user_name}")
    fig = px.line(
        correct_data_per_date,
        x="tanggal",
        y="jumlah",
        title="Jumlah Gerakan Sesuai per Tanggal",
        labels={"tanggal": "Tanggal", "jumlah": "Jumlah Gerakan Sesuai"},
    )
    st.plotly_chart(fig)

    # Pilihan untuk melihat data mentah
    if st.checkbox("Tampilkan Data Mentah"):
        st.write(correct_data)
else:
    st.write("User ID tidak tersedia di URL")

# Jalankan streamlit dengan perintah:
# streamlit run streamlit.py
