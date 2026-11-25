import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import sqlite3
import base64
import os
import secrets
import time
from datetime import datetime

# =====================================================================
# KONFIGURASI HALAMAN & KONSTANTA SESI
# =====================================================================
st.set_page_config(page_title="DSS Malnutrisi Bogor", page_icon="👶", layout="wide")
SESSION_TIMEOUT_SECONDS = 600  # 10 menit tidak ada aksi -> otomatis logout

def set_dinkes_theme():
    st.markdown("""
        <style>
        .stApp { background-color: #f4f9f9; background-image: none; }
        [data-testid="stSidebar"] { background-color: #00695C; }
        [data-testid="stSidebar"] * { color: white !important; }
        [data-testid="stSidebar"] input { color: #000000 !important; background-color: #ffffff !important; }
        [data-testid="stSidebar"] [data-testid="stExpander"] { background-color: rgba(255, 255, 255, 0.08); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.2); }
        div.stButton > button:first-child { background-color: #00897B; color: white; border-radius: 8px; border: none; font-weight: bold; }
        div.stButton > button:first-child:hover { background-color: #004D40; color: white; }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #ffffff; border-radius: 4px 4px 0px 0px; padding-left: 20px; padding-right: 20px; font-weight: bold; color: #00695C; }
        </style>
    """, unsafe_allow_html=True)

# =====================================================================
# TABEL RUJUKAN PERMENKES NO. 2 TAHUN 2020 (-1 SD, Median, +1 SD)
# =====================================================================
BBU_L = {
    0:(2.9,3.3,3.9),1:(3.9,4.5,5.1),2:(4.9,5.6,6.3),3:(5.7,6.4,7.2),4:(6.2,7.0,7.8),5:(6.7,7.5,8.4),
    6:(7.1,7.9,8.8),7:(7.4,8.3,9.2),8:(7.7,8.6,9.6),9:(8.0,8.9,9.9),10:(8.2,9.2,10.2),11:(8.4,9.4,10.5),
    12:(8.6,9.6,10.8),13:(8.8,9.9,11.0),14:(9.0,10.1,11.3),15:(9.2,10.3,11.5),16:(9.4,10.5,11.7),17:(9.6,10.7,12.0),
    18:(9.8,10.9,12.2),19:(10.0,11.1,12.5),20:(10.1,11.3,12.7),21:(10.3,11.5,12.9),22:(10.5,11.8,13.2),23:(10.7,12.0,13.4),
    24:(10.8,12.2,13.6),25:(11.0,12.4,13.9),26:(11.2,12.5,14.1),27:(11.3,12.7,14.3),28:(11.5,12.9,14.5),29:(11.7,13.1,14.8),
    30:(11.8,13.3,15.0),31:(12.0,13.5,15.2),32:(12.1,13.7,15.4),33:(12.3,13.8,15.6),34:(12.4,14.0,15.8),35:(12.6,14.2,16.0),
    36:(12.7,14.3,16.2),37:(12.9,14.5,16.4),38:(13.0,14.7,16.6),39:(13.1,14.8,16.8),40:(13.3,15.0,17.0),41:(13.4,15.2,17.2),
    42:(13.6,15.3,17.4),43:(13.7,15.5,17.6),44:(13.8,15.7,17.8),45:(14.0,15.8,18.0),46:(14.1,16.0,18.2),47:(14.3,16.2,18.4),
    48:(14.4,16.3,18.6),49:(14.5,16.5,18.8),50:(14.7,16.7,19.0),51:(14.8,16.8,19.2),52:(15.0,17.0,19.4),53:(15.1,17.2,19.6),
    54:(15.2,17.3,19.8),55:(15.4,17.5,20.0),56:(15.5,17.7,20.2),57:(15.6,17.8,20.4),58:(15.8,18.0,20.6),59:(15.9,18.2,20.8),
    60:(16.0,18.3,21.0)
}

BBU_P = {
    0:(2.8,3.2,3.7),1:(3.6,4.2,4.8),2:(4.5,5.1,5.8),3:(5.2,5.8,6.6),4:(5.7,6.4,7.3),5:(6.1,6.9,7.8),
    6:(6.5,7.3,8.2),7:(6.8,7.6,8.6),8:(7.0,7.9,9.0),9:(7.3,8.2,9.3),10:(7.5,8.5,9.6),11:(7.7,8.7,9.9),
    12:(7.9,8.9,10.1),13:(8.1,9.2,10.4),14:(8.3,9.4,10.6),15:(8.5,9.6,10.9),16:(8.7,9.8,11.1),17:(8.9,10.0,11.4),
    18:(9.1,10.2,11.6),19:(9.2,10.4,11.8),20:(9.4,10.6,12.1),21:(9.6,10.9,12.3),22:(9.8,11.1,12.5),23:(10.0,11.3,12.8),
    24:(10.2,11.5,13.0),25:(10.3,11.7,13.3),26:(10.5,11.9,13.5),27:(10.7,12.1,13.7),28:(10.9,12.3,14.0),29:(11.1,12.5,14.2),
    30:(11.2,12.7,14.4),31:(11.4,12.9,14.7),32:(11.6,13.1,14.9),33:(11.7,13.3,15.1),34:(11.9,13.5,15.4),35:(12.0,13.7,15.6),
    36:(12.2,13.9,15.8),37:(12.4,14.0,16.0),38:(12.5,14.2,16.3),39:(12.7,14.4,16.5),40:(12.8,14.6,16.7),41:(13.0,14.8,16.9),
    42:(13.1,15.0,17.2),43:(13.3,15.2,17.4),44:(13.4,15.3,17.6),45:(13.6,15.5,17.8),46:(13.7,15.7,18.1),47:(13.9,15.9,18.3),
    48:(14.0,16.1,18.5),49:(14.2,16.3,18.8),50:(14.3,16.4,19.0),51:(14.5,16.6,19.2),52:(14.6,16.8,19.4),53:(14.8,17.0,19.7),
    54:(14.9,17.2,19.9),55:(15.1,17.3,20.1),56:(15.2,17.5,20.3),57:(15.3,17.7,20.6),58:(15.5,17.9,20.8),59:(15.6,18.0,21.0),
    60:(15.8,18.2,21.2)
}

TBU_L = {
    0:(48.0,49.9,51.8),1:(52.8,54.7,56.7),2:(56.4,58.4,60.4),3:(59.4,61.4,63.5),4:(61.8,63.9,66.0),5:(63.8,65.9,68.0),
    6:(65.5,67.6,69.8),7:(67.0,69.2,71.3),8:(68.4,70.6,72.8),9:(69.7,72.0,74.2),10:(71.0,73.3,75.6),11:(72.2,74.5,76.9),
    12:(73.4,75.7,78.1),13:(74.5,76.9,79.3),14:(75.6,78.0,80.5),15:(76.6,79.1,81.7),16:(77.6,80.2,82.8),17:(78.6,81.2,83.9),
    18:(79.6,82.3,85.0),19:(80.5,83.2,86.0),20:(81.4,84.2,87.0),21:(82.3,85.1,88.0),22:(83.1,86.0,89.0),23:(83.9,86.9,89.9),
    24:(84.8,87.8,90.9),25:(84.9,88.0,91.1),26:(85.6,88.8,92.0),27:(86.4,89.6,92.9),28:(87.1,90.4,93.7),29:(87.8,91.2,94.5),
    30:(88.5,91.9,95.3),31:(89.2,92.7,96.1),32:(89.9,93.4,96.9),33:(90.5,94.1,97.6),34:(91.1,94.8,98.4),35:(91.8,95.4,99.1),
    36:(92.4,96.1,99.8),37:(93.0,96.7,100.5),38:(93.6,97.4,101.2),39:(94.2,98.0,101.8),40:(94.7,98.6,102.5),41:(95.3,99.2,103.2),
    42:(95.9,99.9,103.8),43:(96.4,100.4,104.5),44:(97.0,101.0,105.1),45:(97.5,101.6,105.7),46:(98.1,102.2,106.3),47:(98.6,102.8,106.9),
    48:(99.1,103.3,107.5),49:(99.7,103.9,108.1),50:(100.2,104.4,108.7),51:(100.7,105.0,109.3),52:(101.2,105.6,109.9),53:(101.7,106.1,110.5),
    54:(102.3,106.7,111.1),55:(102.8,107.2,111.7),56:(103.3,107.8,112.3),57:(103.8,108.3,112.8),58:(104.3,108.9,113.4),59:(104.8,109.4,114.0),
    60:(105.3,110.0,114.6)
}

TBU_P = {
    0:(47.3,49.1,51.0),1:(51.7,53.7,55.6),2:(55.0,57.1,59.1),3:(57.7,59.8,61.9),4:(59.9,62.1,64.3),5:(61.8,64.0,66.2),
    6:(63.5,65.7,68.0),7:(65.0,67.3,69.6),8:(66.4,68.7,71.1),9:(67.7,70.1,72.6),10:(69.0,71.5,73.9),11:(70.3,72.8,75.3),
    12:(71.4,74.0,76.6),13:(72.6,75.2,77.8),14:(73.7,76.4,79.1),15:(74.8,77.5,80.2),16:(75.8,78.6,81.4),17:(76.8,79.7,82.5),
    18:(77.8,80.7,83.6),19:(78.8,81.7,84.7),20:(79.7,82.7,85.7),21:(80.6,83.7,86.7),22:(81.5,84.6,87.7),23:(82.3,85.5,88.7),
    24:(83.2,86.4,89.6),25:(83.3,86.6,89.9),26:(84.1,87.4,90.8),27:(84.9,88.3,91.7),28:(85.7,89.1,92.5),29:(86.4,89.9,93.4),
    30:(87.1,90.7,94.2),31:(87.9,91.4,95.0),32:(88.6,92.2,95.8),33:(89.3,92.9,96.6),34:(89.9,93.6,97.4),35:(90.6,94.4,98.1),
    36:(91.2,95.1,98.9),37:(91.9,95.7,99.6),38:(92.5,96.4,100.3),39:(93.1,97.1,101.0),40:(93.8,97.7,101.7),41:(94.4,98.4,102.4),
    42:(95.0,99.0,103.1),43:(95.6,99.7,103.8),44:(96.2,100.3,104.5),45:(96.7,100.9,105.1),46:(97.3,101.5,105.8),47:(97.9,102.1,106.4),
    48:(98.4,102.7,107.0),49:(99.0,103.3,107.7),50:(99.5,103.9,108.3),51:(100.1,104.5,108.9),52:(100.6,105.0,109.5),53:(101.1,105.6,110.1),
    54:(101.6,106.2,110.7),55:(102.2,106.7,111.3),56:(102.7,107.3,111.9),57:(103.2,107.8,112.5),58:(103.7,108.4,113.0),59:(104.2,108.9,113.6),
    60:(104.7,109.4,114.2)
}

IMTU_L = {
    0:(12.2,13.4,14.8),1:(13.6,14.9,16.3),2:(15.0,16.3,17.8),3:(15.5,16.9,18.4),4:(15.8,17.2,18.7),5:(15.9,17.3,18.8),
    6:(16.0,17.3,18.8),7:(16.0,17.3,18.8),8:(15.9,17.3,18.7),9:(15.8,17.2,18.6),10:(15.7,17.0,18.5),11:(15.6,16.9,18.4),
    12:(15.5,16.8,18.2),13:(15.4,16.7,18.1),14:(15.3,16.6,18.0),15:(15.2,16.4,17.8),16:(15.1,16.3,17.7),17:(15.0,16.2,17.6),
    18:(14.9,16.1,17.5),19:(14.9,16.1,17.4),20:(14.8,16.0,17.3),21:(14.7,15.9,17.2),22:(14.7,15.8,17.2),23:(14.6,15.8,17.1),
    24:(14.6,15.7,17.0),25:(14.8,16.0,17.3),26:(14.8,15.9,17.3),27:(14.7,15.9,17.2),28:(14.7,15.9,17.2),29:(14.7,15.8,17.1),
    30:(14.6,15.8,17.1),31:(14.6,15.8,17.1),32:(14.6,15.7,17.0),33:(14.5,15.7,17.0),34:(14.5,15.7,17.0),35:(14.5,15.6,16.9),
    36:(14.4,15.6,16.9),37:(14.4,15.6,16.9),38:(14.4,15.5,16.8),39:(14.3,15.5,16.8),40:(14.3,15.5,16.8),41:(14.3,15.5,16.8),
    42:(14.3,15.4,16.8),43:(14.2,15.4,16.7),44:(14.2,15.4,16.7),45:(14.2,15.4,16.7),46:(14.2,15.4,16.7),47:(14.2,15.3,16.7),
    48:(14.1,15.3,16.7),49:(14.1,15.3,16.7),50:(14.1,15.3,16.7),51:(14.1,15.3,16.6),52:(14.1,15.3,16.6),53:(14.1,15.3,16.6),
    54:(14.0,15.3,16.6),55:(14.0,15.2,16.6),56:(14.0,15.2,16.6),57:(14.0,15.2,16.6),58:(14.0,15.2,16.6),59:(14.0,15.2,16.6),
    60:(14.0,15.2,16.6)
}

IMTU_P = {
    0:(12.2,13.3,14.6),1:(13.2,14.6,16.0),2:(14.3,15.8,17.3),3:(14.9,16.4,17.9),4:(15.2,16.7,18.3),5:(15.4,16.8,18.4),
    6:(15.5,16.9,18.5),7:(15.5,16.9,18.5),8:(15.4,16.8,18.4),9:(15.3,16.7,18.3),10:(15.2,16.6,18.2),11:(15.1,16.5,18.0),
    12:(15.0,16.4,17.9),13:(14.9,16.2,17.7),14:(14.8,16.1,17.6),15:(14.7,16.0,17.5),16:(14.6,15.9,17.4),17:(14.5,15.8,17.3),
    18:(14.4,15.7,17.2),19:(14.4,15.7,17.1),20:(14.3,15.6,17.0),21:(14.3,15.5,17.0),22:(14.2,15.5,16.9),23:(14.2,15.4,16.9),
    24:(14.2,15.4,16.8),25:(14.4,15.7,17.1),26:(14.4,15.6,17.0),27:(14.4,15.6,17.0),28:(14.3,15.6,17.0),29:(14.3,15.6,17.0),
    30:(14.3,15.5,16.9),31:(14.3,15.5,16.9),32:(14.3,15.5,16.9),33:(14.2,15.5,16.9),34:(14.2,15.4,16.8),35:(14.2,15.4,16.8),
    36:(14.2,15.4,16.8),37:(14.1,15.4,16.8),38:(14.1,15.4,16.8),39:(14.1,15.3,16.8),40:(14.1,15.3,16.8),41:(14.1,15.3,16.8),
    42:(14.0,15.3,16.8),43:(14.0,15.3,16.8),44:(14.0,15.3,16.8),45:(14.0,15.3,16.8),46:(14.0,15.3,16.8),47:(14.0,15.3,16.8),
    48:(14.0,15.3,16.8),49:(13.9,15.3,16.8),50:(13.9,15.3,16.8),51:(13.9,15.3,16.8),52:(13.9,15.2,16.8),53:(13.9,15.3,16.8),
    54:(13.9,15.3,16.8),55:(13.9,15.3,16.8),56:(13.9,15.3,16.8),57:(13.9,15.3,16.9),58:(13.9,15.3,16.9),59:(13.9,15.3,16.9),
    60:(13.9,15.3,16.9)
}

BBPB_L_TB = [45,50,55,60,65,70,75,80,85,90,95,100,105,110]
BBPB_L_M1 = [2.2,3.0,4.2,5.5,6.7,7.8,8.8,9.6,10.6,11.8,12.8,14.0,15.3,16.8]
BBPB_L_MD = [2.4,3.3,4.5,6.0,7.3,8.4,9.5,10.4,11.5,12.7,13.9,15.2,16.6,18.3]
BBPB_L_P1 = [2.7,3.6,5.0,6.5,7.9,9.2,10.3,11.4,12.5,13.8,15.1,16.5,18.1,20.0]

BBTB_L_TB = [65,70,75,80,85,90,95,100,105,110,115,120]
BBTB_L_M1 = [6.9,7.9,8.9,9.7,10.8,11.9,13.0,14.2,15.5,17.0,18.6,20.4]
BBTB_L_MD = [7.4,8.6,9.6,10.6,11.7,12.9,14.1,15.4,16.8,18.5,20.4,22.4]
BBTB_L_P1 = [8.1,9.3,10.5,11.5,12.7,14.0,15.3,16.7,18.4,20.2,22.4,24.6]

BBPB_P_TB = [45,50,55,60,65,70,75,80,85,90,95,100,105,110]
BBPB_P_M1 = [2.3,3.1,4.2,5.4,6.5,7.5,8.4,9.2,10.3,11.4,12.6,13.7,15.1,16.7]
BBPB_P_MD = [2.5,3.4,4.5,5.9,7.1,8.2,9.1,10.1,11.2,12.5,13.7,15.0,16.5,18.3]
BBPB_P_P1 = [2.7,3.7,5.0,6.4,7.8,9.0,10.0,11.0,12.3,13.7,15.0,16.5,18.2,20.2]

BBTB_P_TB = [65,70,75,80,85,90,95,100,105,110,115,120]
BBTB_P_M1 = [6.6,7.6,8.5,9.4,10.4,11.6,12.7,13.9,15.3,17.0,18.8,20.7]
BBTB_P_MD = [7.2,8.3,9.3,10.2,11.4,12.6,13.9,15.2,16.8,18.6,20.7,22.8]
BBTB_P_P1 = [7.9,9.1,10.2,11.2,12.5,13.8,15.2,16.7,18.4,20.5,22.8,25.2]

def _rumus_zscore(x, m1, med, p1):
    if x < med:
        denom = med - m1
        return round((x - med) / denom, 2) if denom != 0 else 0.0
    else:
        denom = p1 - med
        return round((x - med) / denom, 2) if denom != 0 else 0.0

def hitung_zscore_permenkes(jk_enc, umur, tinggi, berat):
    u_int = int(np.clip(round(float(umur)), 0, 60))
    tb = float(tinggi)
    bb = float(berat)
    imt = bb / ((tb / 100.0) ** 2) if tb > 0 else 0.0

    m1_tb, med_tb, p1_tb = TBU_L[u_int] if jk_enc == 0 else TBU_P[u_int]
    zs_stunting = _rumus_zscore(tb, m1_tb, med_tb, p1_tb)

    if u_int <= 24:
        arr_tb, arr_m1, arr_md, arr_p1 = (BBPB_L_TB, BBPB_L_M1, BBPB_L_MD, BBPB_L_P1) if jk_enc == 0 else (BBPB_P_TB, BBPB_P_M1, BBPB_P_MD, BBPB_P_P1)
    else:
        arr_tb, arr_m1, arr_md, arr_p1 = (BBTB_L_TB, BBTB_L_M1, BBTB_L_MD, BBTB_L_P1) if jk_enc == 0 else (BBTB_P_TB, BBTB_P_M1, BBTB_P_MD, BBTB_P_P1)
    m1_w = float(np.interp(tb, arr_tb, arr_m1))
    med_w = float(np.interp(tb, arr_tb, arr_md))
    p1_w = float(np.interp(tb, arr_tb, arr_p1))
    zs_wasting = _rumus_zscore(bb, m1_w, med_w, p1_w)

    m1_imt, med_imt, p1_imt = IMTU_L[u_int] if jk_enc == 0 else IMTU_P[u_int]
    zs_overweight = _rumus_zscore(imt, m1_imt, med_imt, p1_imt)

    m1_bb, med_bb, p1_bb = BBU_L[u_int] if jk_enc == 0 else BBU_P[u_int]
    zs_underweight = _rumus_zscore(bb, m1_bb, med_bb, p1_bb)

    return zs_stunting, zs_wasting, zs_overweight, zs_underweight

# =====================================================================
# PENGATURAN DATABASE & MIGRASI
# =====================================================================
def get_db_connection():
    return sqlite3.connect('database_malnutrisi.db', check_same_thread=False)

def init_tabel_grafik3():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS riwayat_grafik3_kecamatan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tahun INTEGER NOT NULL,
            kecamatan TEXT NOT NULL,
            total_balita INTEGER DEFAULT 0,
            stunting REAL DEFAULT 0.0,
            wasting REAL DEFAULT 0.0,
            underweight REAL DEFAULT 0.0,
            overweight REAL DEFAULT 0.0,
            total_malnutrisi REAL DEFAULT 0.0,
            keterangan TEXT DEFAULT 'Data arsip tahunan',
            UNIQUE(tahun, kecamatan)
        )
    """)
    conn.commit()
    conn.close()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Tabel Balita
    cursor.execute('''CREATE TABLE IF NOT EXISTS data_balita (
        id INTEGER PRIMARY KEY AUTOINCREMENT, Waktu TEXT, Kecamatan TEXT, Kelurahan TEXT,
        Nama_Posyandu TEXT, Alamat_Posyandu TEXT, Nama_Balita TEXT, Nama_Ibu TEXT, NIK_Ibu TEXT,
        JK TEXT, Umur REAL, Tinggi REAL, Berat REAL,
        Stunting INTEGER, Wasting INTEGER, Overweight INTEGER, Underweight INTEGER,
        Status_Stunting TEXT, Status_Wasting TEXT, Status_Overweight TEXT, Status_Underweight TEXT,
        ZS_Stunting REAL, ZS_Wasting REAL, ZS_Overweight REAL, ZS_Underweight REAL,
        Lat REAL, Lon REAL
    )''')
    for col in [
        'Nama_Posyandu', 'Kelurahan', 'Alamat_Posyandu', 'Nama_Ibu', 'NIK_Ibu',
        'Status_Stunting', 'Status_Wasting', 'Status_Overweight', 'Status_Underweight'
    ]:
        try: cursor.execute(f"ALTER TABLE data_balita ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError: pass
    for col in ['ZS_Stunting', 'ZS_Wasting', 'ZS_Overweight', 'ZS_Underweight']:
        try: cursor.execute(f"ALTER TABLE data_balita ADD COLUMN {col} REAL")
        except sqlite3.OperationalError: pass

    # 2. Tabel Users
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT,
        kecamatan TEXT, kelurahan TEXT, nama_posyandu TEXT, alamat_posyandu TEXT, penanggung_jawab TEXT
    )''')
    for col in ['kecamatan', 'kelurahan', 'nama_posyandu', 'alamat_posyandu', 'penanggung_jawab']:
        try: cursor.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError: pass

    # 3. Tabel Sesi Login
    cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY, username TEXT, role TEXT, kecamatan TEXT,
        kelurahan TEXT, nama_posyandu TEXT, alamat_posyandu TEXT, last_active REAL
    )''')
    for col in ['kelurahan', 'alamat_posyandu']:
        try: cursor.execute(f"ALTER TABLE sessions ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError: pass

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO users (username, password, role, kecamatan, kelurahan, nama_posyandu, alamat_posyandu, penanggung_jawab) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ('admin', 'admin123', 'admin', 'Pusat Dinkes Bogor', 'Pabaton', 'Dinas Kesehatan Kota Bogor', 'Jl. Kesehatan No. 3, Kota Bogor', 'Admin Utama')
        )
        cursor.execute(
            "INSERT INTO users (username, password, role, kecamatan, kelurahan, nama_posyandu, alamat_posyandu, penanggung_jawab) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ('kader', 'kader123', 'kader', 'Semua Wilayah', '-', 'Posyandu Default', '-', 'Kader Default')
        )
    else:
        cursor.execute("UPDATE users SET kelurahan='-' WHERE kelurahan IS NULL")
        cursor.execute("UPDATE users SET alamat_posyandu='-' WHERE alamat_posyandu IS NULL")

    # 4. Tabel Edukasi
    cursor.execute('''CREATE TABLE IF NOT EXISTS konten_edukasi (
        id INTEGER PRIMARY KEY AUTOINCREMENT, judul_definisi TEXT, teks_definisi TEXT, judul_protokol TEXT, teks_protokol TEXT
    )''')
    cursor.execute("SELECT COUNT(*) FROM konten_edukasi")
    if cursor.fetchone()[0] == 0:
        def_text = "**1. Stunting (Sangat Pendek / Pendek)**\nKondisi gagal tumbuh pada balita akibat kekurangan gizi kronis (Z-Score TB/U < -2 SD).\n\n**2. Wasting (Gizi Kurang / Buruk)**\nKondisi akut di mana berat badan menurun drastis (Z-Score BB/TB < -2 SD).\n\n**3. Underweight (Berat Badan Kurang)**\nBerat badan anak lebih rendah dari rata-rata seusianya (Z-Score BB/U < -2 SD).\n\n**4. Overweight (Gizi Lebih / Obesitas)**\nAkumulasi lemak abnormal (Z-Score IMT/U atau BB/TB > +2 SD)."
        prot_text = "*   **Rujuk ke Fasilitas Kesehatan:** Segera bawa balita ke dokter anak/puskesmas.\n*   **Berikan MPASI Kaya Protein Hewani:** Intervensi efektif untuk Stunting (telur, ayam, ikan).\n*   **Teruskan ASI Eksklusif:** Pastikan ASI hingga usia 2 tahun.\n*   **Perbaikan Sanitasi (CTPS):** Cuci tangan pakai sabun dan minum air matang."
        cursor.execute("INSERT INTO konten_edukasi (judul_definisi, teks_definisi, judul_protokol, teks_protokol) VALUES (?, ?, ?, ?)", ("📖 Memahami Status Malnutrisi", def_text, "🩺 Protokol Tindakan Penanganan", prot_text))

    # 5. Tabel Tren Indonesia (SSGI)
    cursor.execute('''CREATE TABLE IF NOT EXISTS tren_malnutrisi (
        tahun INTEGER PRIMARY KEY, stunting REAL, wasting REAL, overweight REAL, underweight REAL
    )''')
    cursor.execute("SELECT COUNT(*) FROM tren_malnutrisi")
    if cursor.fetchone()[0] == 0:
        default_indo = [
            (2021, 24.4, 7.1, 3.8, 17.0),
            (2022, 21.6, 7.7, 3.5, 17.1),
            (2023, 21.5, 8.5, 4.2, 15.9),
            (2024, 19.8, 7.4, 3.4, 16.8),
        ]
        cursor.executemany("INSERT INTO tren_malnutrisi (tahun, stunting, wasting, overweight, underweight) VALUES (?, ?, ?, ?, ?)", default_indo)

    # 6. Tabel Tren Kota Bogor (SSGI 2024)
    cursor.execute('''CREATE TABLE IF NOT EXISTS tren_malnutrisi_bogor (
        tahun INTEGER PRIMARY KEY, stunting REAL, wasting REAL, overweight REAL, underweight REAL
    )''')
    cursor.execute("SELECT COUNT(*) FROM tren_malnutrisi_bogor")
    if cursor.fetchone()[0] == 0:
        default_bogor = [
            (2021, 16.9, 5.2, 3.8, 11.4),
            (2022, 18.7, 5.6, 3.4, 11.8),
            (2023, 18.2, 4.9, 3.2, 12.0),
            (2024, 21.1, 4.5, 2.9, 12.1),
        ]
        cursor.executemany("INSERT INTO tren_malnutrisi_bogor (tahun, stunting, wasting, overweight, underweight) VALUES (?, ?, ?, ?, ?)", default_bogor)

    # 7. Tabel Keterangan Kasus per Kecamatan Kota Bogor
    cursor.execute('''CREATE TABLE IF NOT EXISTS kasus_kecamatan_dashboard (
        kecamatan TEXT PRIMARY KEY, stunting INTEGER, wasting INTEGER,
        overweight INTEGER, underweight INTEGER, keterangan TEXT
    )''')
    cursor.execute("SELECT COUNT(*) FROM kasus_kecamatan_dashboard")
    if cursor.fetchone()[0] == 0:
        default_kec_kasus = [
            ("Bogor Barat", 0, 0, 0, 0, "Pemantauan rutin Posyandu"),
            ("Bogor Selatan", 0, 0, 0, 0, "Pemantauan rutin Posyandu"),
            ("Bogor Tengah", 0, 0, 0, 0, "Pemantauan rutin Posyandu"),
            ("Bogor Timur", 0, 0, 0, 0, "Pemantauan rutin Posyandu"),
            ("Bogor Utara", 0, 0, 0, 0, "Pemantauan rutin Posyandu"),
            ("Tanah Sareal", 0, 0, 0, 0, "Pemantauan rutin Posyandu"),
        ]
        cursor.executemany(
            "INSERT INTO kasus_kecamatan_dashboard (kecamatan, stunting, wasting, overweight, underweight, keterangan) VALUES (?, ?, ?, ?, ?, ?)",
            default_kec_kasus
        )

    # 8. Tabel Arsip Upload Massal Grafik 3 (Tahun Sebelumnya)
    cursor.execute('''CREATE TABLE IF NOT EXISTS riwayat_grafik3_kecamatan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tahun INTEGER NOT NULL,
        kecamatan TEXT NOT NULL,
        total_balita INTEGER DEFAULT 0,
        stunting REAL DEFAULT 0.0,
        wasting REAL DEFAULT 0.0,
        underweight REAL DEFAULT 0.0,
        overweight REAL DEFAULT 0.0,
        total_malnutrisi REAL DEFAULT 0.0,
        keterangan TEXT DEFAULT 'Data arsip tahunan',
        UNIQUE(tahun, kecamatan)
    )''')

    conn.commit()
    conn.close()

init_db()

# =====================================================================
# MANAJEMEN SESI PERSISTEN (TAHAN REFRESH & IDLE TIMEOUT 10 MENIT)
# =====================================================================
def create_session(username, role, kecamatan, kelurahan, nama_posyandu, alamat_posyandu):
    token = secrets.token_urlsafe(24)
    now = time.time()
    conn = get_db_connection()
    conn.cursor().execute(
        "INSERT OR REPLACE INTO sessions (token, username, role, kecamatan, kelurahan, nama_posyandu, alamat_posyandu, last_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (token, username, role, kecamatan, kelurahan, nama_posyandu, alamat_posyandu, now)
    )
    conn.commit()
    conn.close()
    st.query_params["session"] = token
    st.session_state.session_token = token
    st.session_state.role = role
    st.session_state.username = username
    st.session_state.kecamatan = kecamatan
    st.session_state.kelurahan = kelurahan or "-"
    st.session_state.nama_posyandu = nama_posyandu
    st.session_state.alamat_posyandu = alamat_posyandu or "-"

def destroy_session(expired=False):
    token = st.query_params.get("session") or st.session_state.get("session_token")
    if token:
        conn = get_db_connection()
        conn.cursor().execute("DELETE FROM sessions WHERE token=?", (token,))
        conn.commit()
        conn.close()
    st.query_params.clear()
    for k in ['role', 'username', 'kecamatan', 'kelurahan', 'nama_posyandu', 'alamat_posyandu', 'session_token']:
        st.session_state[k] = None
    if expired:
        st.session_state.session_expired_msg = True

def check_and_restore_session():
    for k in ['role', 'username', 'kecamatan', 'kelurahan', 'nama_posyandu', 'alamat_posyandu', 'session_token']:
        if k not in st.session_state:
            st.session_state[k] = None

    token = st.query_params.get("session") or st.session_state.get("session_token")
    if not token:
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT username, role, kecamatan, kelurahan, nama_posyandu, alamat_posyandu, last_active FROM sessions WHERE token=?",
        (token,)
    ).fetchone()

    if not row:
        conn.close()
        destroy_session(expired=False)
        return

    username, role, kecamatan, kelurahan, nama_posyandu, alamat_posyandu, last_active = row
    now = time.time()
    if (now - last_active) > SESSION_TIMEOUT_SECONDS:
        conn.close()
        destroy_session(expired=True)
        return

    cursor.execute("UPDATE sessions SET last_active=? WHERE token=?", (now, token))
    conn.commit()
    conn.close()

    st.session_state.session_token = token
    st.session_state.username = username
    st.session_state.role = role
    st.session_state.kecamatan = kecamatan
    st.session_state.kelurahan = kelurahan or "-"
    st.session_state.nama_posyandu = nama_posyandu
    st.session_state.alamat_posyandu = alamat_posyandu or "-"

check_and_restore_session()

def load_data():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM data_balita", conn)
    conn.close()
    if len(df) > 0:
        for col in ['Kelurahan', 'Alamat_Posyandu', 'Nama_Ibu', 'NIK_Ibu', 'Nama_Posyandu']:
            if col in df.columns:
                df[col] = df[col].fillna("-")
        mask_null = df[['ZS_Stunting', 'ZS_Wasting', 'ZS_Overweight', 'ZS_Underweight']].isna().any(axis=1)
        if mask_null.any():
            for idx in df[mask_null].index:
                r = df.loc[idx]
                jk_enc = 0 if str(r['JK']).strip().lower() in ['l', 'laki-laki', 'pria'] else 1
                zs_s, zs_w, zs_o, zs_u = hitung_zscore_permenkes(jk_enc, r['Umur'], r['Tinggi'], r['Berat'])
                df.loc[idx, ['ZS_Stunting', 'ZS_Wasting', 'ZS_Overweight', 'ZS_Underweight']] = [zs_s, zs_w, zs_o, zs_u]
    return df

def hapus_database():
    conn = get_db_connection()
    conn.cursor().execute("DELETE FROM data_balita")
    conn.cursor().execute("DELETE FROM sqlite_sequence WHERE name='data_balita'")
    conn.commit()
    conn.close()

# =====================================================================
# MUAT AI KLASIFIKASI MLRF
# =====================================================================
KOORDINAT_BOGOR = {
    "Bogor Barat": {"lat": -6.5866, "lon": 106.7645},
    "Bogor Selatan": {"lat": -6.6347, "lon": 106.8041},
    "Bogor Tengah": {"lat": -6.5956, "lon": 106.7990},
    "Bogor Timur": {"lat": -6.6111, "lon": 106.8239},
    "Bogor Utara": {"lat": -6.5746, "lon": 106.8118},
    "Tanah Sareal": {"lat": -6.5645, "lon": 106.7963}
}

@st.cache_resource
def load_ml_components():
    if not os.path.exists('mlrf_malnutrisi_model.pkl') or not os.path.exists('scaler_malnutrisi.pkl'):
        st.warning("⚠️ File Model MLRF atau Scaler tidak ditemukan di folder!")
        return None, None
    try:
        clf = joblib.load('mlrf_malnutrisi_model.pkl')
        scl = joblib.load('scaler_malnutrisi.pkl')
        return clf, scl
    except Exception as e:
        st.error(f"Gagal memuat sistem AI: {e}")
        return None, None

model_clf, scaler = load_ml_components()

def prediksi_malnutrisi_detail(jk_enc, umur, tinggi, berat):
    zs_s, zs_w, zs_o, zs_u = hitung_zscore_permenkes(jk_enc, umur, tinggi, berat)

    if model_clf and scaler:
        input_scaled = scaler.transform(np.array([[jk_enc, umur, tinggi, berat]]))
        pred_label = model_clf.predict(input_scaled)[0]
        s, w, o, u = int(pred_label[0]), int(pred_label[1]), int(pred_label[2]), int(pred_label[3])

        stat_s = "Sangat Pendek (Severely Stunted)" if zs_s < -3.0 else ("Pendek (Stunted)" if s == 1 else "Normal")
        stat_w = "Gizi Buruk (Severely Wasted)" if zs_w < -3.0 else ("Gizi Kurang (Wasted)" if w == 1 else "Normal")
        stat_o = "Obesitas (Obese)" if zs_o > 3.0 else ("Gizi Lebih (Overweight)" if o == 1 else "Normal")
        stat_u = "Sangat Kurang (Severely Underweight)" if zs_u < -3.0 else ("Kurang (Underweight)" if u == 1 else "Normal")

        return [s, w, o, u], [stat_s, stat_w, stat_o, stat_u], [zs_s, zs_w, zs_o, zs_u]
    return [0, 0, 0, 0], ["-", "-", "-", "-"], [zs_s, zs_w, zs_o, zs_u]

# =====================================================================
# FUNGSI GANTI PASSWORD MANDIRI (SIDEBAR - ADMIN & KADER + TOGGLE)
# =====================================================================
def render_ganti_password_sidebar():
    with st.sidebar.expander("🔑 Ganti Password"):
        show_pw = st.toggle("👁️ Tampilkan Password", key="toggle_pw_mandiri")
        pw_type = "default" if show_pw else "password"
        with st.form("form_ganti_password_mandiri", clear_on_submit=True):
            old_pass = st.text_input("Password Lama", type=pw_type)
            new_pass = st.text_input("Password Baru", type=pw_type)
            conf_pass = st.text_input("Konfirmasi Password Baru", type=pw_type)
            if st.form_submit_button("Simpan Password"):
                if not old_pass or not new_pass or not conf_pass:
                    st.warning("Semua kolom wajib diisi.")
                elif new_pass != conf_pass:
                    st.error("Konfirmasi password baru tidak cocok!")
                else:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (st.session_state.username, old_pass))
                    if cursor.fetchone():
                        cursor.execute("UPDATE users SET password=? WHERE username=?", (new_pass, st.session_state.username))
                        conn.commit()
                        st.success("Password berhasil diperbarui!")
                    else:
                        st.error("Password lama salah!")
                    conn.close()

# =====================================================================
# FUNGSI PAGINASI
# =====================================================================
def render_pagination(df, page_size=10, key_prefix="pg"):
    if len(df) == 0:
        st.info("Tidak ada data rekam medis untuk ditampilkan.")
        return

    total_pages = max(1, (len(df) - 1) // page_size + 1)

    if key_prefix not in st.session_state:
        st.session_state[key_prefix] = 1
    if st.session_state[key_prefix] > total_pages:
        st.session_state[key_prefix] = total_pages

    start_idx = (st.session_state[key_prefix] - 1) * page_size
    end_idx = start_idx + page_size

    st.dataframe(df.iloc[start_idx:end_idx], use_container_width=True, hide_index=True)

    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        if st.button("⬅️ Sebelumnya", key=f"{key_prefix}_prev", disabled=st.session_state[key_prefix] <= 1, use_container_width=True):
            st.session_state[key_prefix] -= 1
            st.rerun()
    with c2:
        st.markdown(f"<p style='text-align:center; font-weight:bold; color:#00695C;'>Halaman {st.session_state[key_prefix]} dari {total_pages} (Total: {len(df)} Baris Data)</p>", unsafe_allow_html=True)
    with c3:
        if st.button("Selanjutnya ➡️", key=f"{key_prefix}_next", disabled=st.session_state[key_prefix] >= total_pages, use_container_width=True):
            st.session_state[key_prefix] += 1
            st.rerun()

# =====================================================================
# FUNGSI UPLOAD MASSAL DATA TAHUNAN GRAFIK 3 (KHUSUS TAB 5 ADMIN)
# =====================================================================
def render_upload_grafik3_admin():
    st.markdown("##### 3. Upload Massal Data Tahunan Grafik 3 (Per Kecamatan Kota Bogor)")
    st.caption("Unggah file arsip data tahun sebelumnya (misal 2025, 2024, dst.) agar otomatis masuk dan bisa dibandingkan pada Grafik 3 di Dashboard Utama.")

    init_tabel_grafik3()

    daftar_kec_template = list(KOORDINAT_BOGOR.keys())
    df_template_g3 = pd.DataFrame({
        "Tahun": [2025] * len(daftar_kec_template),
        "Kecamatan": daftar_kec_template,
        "Total_Balita": [100, 120, 95, 110, 105, 90][:len(daftar_kec_template)],
        "Stunting": [18.5, 20.0, 15.2, 22.1, 17.0, 19.4][:len(daftar_kec_template)],
        "Wasting": [7.5, 8.0, 6.1, 9.0, 7.2, 6.8][:len(daftar_kec_template)],
        "Underweight": [12.0, 13.5, 10.4, 14.0, 11.8, 12.2][:len(daftar_kec_template)],
        "Overweight": [3.0, 2.5, 4.0, 2.8, 3.5, 3.1][:len(daftar_kec_template)],
        "Total_Malnutrisi": [25.0, 27.5, 21.0, 29.0, 24.0, 26.0][:len(daftar_kec_template)],
        "Keterangan": ["Data arsip SSGI/Posyandu 2025"] * len(daftar_kec_template)
    })

    csv_template = df_template_g3.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Template Upload Massal Grafik 3 (.csv)",
        data=csv_template,
        file_name="template_upload_grafik3_kecamatan.csv",
        mime="text/csv",
        key="btn_dl_template_g3"
    )

    st.info("Catatan Format: Kolom **Stunting, Wasting, Underweight, Overweight, dan Total_Malnutrisi** diisi dalam satuan persen (contoh: `20.5` untuk 20,5%). Anda dapat memasukkan lebih dari satu tahun sekaligus dalam satu file.")

    uploaded_g3 = st.file_uploader(
        "Unggah File Data Grafik 3 (.csv atau .xlsx)",
        type=["csv", "xlsx"],
        key="uploader_grafik3_admin"
    )

    if uploaded_g3 is not None:
        try:
            if uploaded_g3.name.endswith(".csv"):
                df_up = pd.read_csv(uploaded_g3, sep=None, engine="python")
            else:
                df_up = pd.read_excel(uploaded_g3)

            df_up.columns = [str(col).strip() for col in df_up.columns]

            kolom_wajib = [
                "Tahun", "Kecamatan", "Total_Balita", "Stunting",
                "Wasting", "Underweight", "Overweight", "Total_Malnutrisi"
            ]
            kolom_kurang = [k for k in kolom_wajib if k not in df_up.columns]

            if kolom_kurang:
                st.error(f"Format kolom tidak sesuai. Kolom yang belum ada: {', '.join(kolom_kurang)}")
            else:
                if "Keterangan" not in df_up.columns:
                    df_up["Keterangan"] = "Data arsip tahunan"

                def bersihkan_angka(val):
                    if pd.isna(val):
                        return 0.0
                    s = str(val).replace("%", "").replace(",", ".").strip()
                    try:
                        return float(s)
                    except ValueError:
                        return 0.0

                df_up["Tahun"] = pd.to_numeric(df_up["Tahun"], errors="coerce")
                df_up = df_up.dropna(subset=["Tahun", "Kecamatan"]).copy()
                df_up["Tahun"] = df_up["Tahun"].astype(int)
                df_up["Kecamatan"] = df_up["Kecamatan"].astype(str).str.strip()
                df_up["Total_Balita"] = df_up["Total_Balita"].apply(lambda x: int(bersihkan_angka(x)))

                for col_p in ["Stunting", "Wasting", "Underweight", "Overweight", "Total_Malnutrisi"]:
                    df_up[col_p] = df_up[col_p].apply(bersihkan_angka)

                df_up["Keterangan"] = df_up["Keterangan"].fillna("Data arsip tahunan").astype(str)

                st.markdown("**Preview Data yang Akan Diunggah:**")
                st.dataframe(df_up, use_container_width=True, hide_index=True)

                if st.button("💾 Simpan & Masukkan ke Grafik 3", key="btn_simpan_g3"):
                    conn = get_db_connection()
                    c = conn.cursor()
                    jumlah_baris = 0
                    for _, row in df_up.iterrows():
                        c.execute("""
                            INSERT OR REPLACE INTO riwayat_grafik3_kecamatan
                            (tahun, kecamatan, total_balita, stunting, wasting, underweight, overweight, total_malnutrisi, keterangan)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            int(row["Tahun"]),
                            row["Kecamatan"],
                            int(row["Total_Balita"]),
                            float(row["Stunting"]),
                            float(row["Wasting"]),
                            float(row["Underweight"]),
                            float(row["Overweight"]),
                            float(row["Total_Malnutrisi"]),
                            row["Keterangan"]
                        ))
                        jumlah_baris += 1
                    conn.commit()
                    conn.close()
                    st.success(f"Berhasil menyimpan {jumlah_baris} baris data! Tahun tersebut sekarang otomatis muncul di Grafik 3.")
                    st.rerun()
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")

    conn = get_db_connection()
    df_tersimpan_g3 = pd.read_sql_query(
        "SELECT tahun AS Tahun, kecamatan AS Kecamatan, total_balita AS Total_Balita, "
        "stunting AS 'Stunting (%)', wasting AS 'Wasting (%)', underweight AS 'Underweight (%)', "
        "overweight AS 'Overweight (%)', total_malnutrisi AS 'Total Malnutrisi (%)', keterangan AS Keterangan "
        "FROM riwayat_grafik3_kecamatan ORDER BY tahun DESC, kecamatan ASC",
        conn
    )
    conn.close()

    if len(df_tersimpan_g3) > 0:
        with st.expander("📋 Lihat & Kelola Data Arsip Grafik 3 yang Sudah Tersimpan"):
            st.dataframe(df_tersimpan_g3, use_container_width=True, hide_index=True)
            tahun_arsip_list = sorted(df_tersimpan_g3["Tahun"].unique().tolist(), reverse=True)
            col_del1, col_del2 = st.columns([2, 1])
            with col_del1:
                tahun_hapus = st.selectbox("Pilih tahun arsip untuk dihapus:", tahun_arsip_list, key="pilih_hapus_g3")
            with col_del2:
                st.write("")
                st.write("")
                if st.button("🗑️ Hapus Data Tahun Ini", key="btn_hapus_g3"):
                    conn = get_db_connection()
                    conn.execute("DELETE FROM riwayat_grafik3_kecamatan WHERE tahun = ?", (int(tahun_hapus),))
                    conn.commit()
                    conn.close()
                    st.warning(f"Data arsip Grafik 3 tahun {tahun_hapus} telah dihapus.")
                    st.rerun()

# ==============================================================================
# KONTEN DASHBOARD UTAMA (INDONESIA, KOTA BOGOR SSGI, & TITIK KECAMATAN OTOMATIS)
# ==============================================================================
def render_dashboard_utama():
    init_tabel_grafik3()
    conn = get_db_connection()
    df_trend_indo = pd.read_sql_query("SELECT * FROM tren_malnutrisi ORDER BY tahun", conn)
    df_trend_bogor = pd.read_sql_query("SELECT * FROM tren_malnutrisi_bogor ORDER BY tahun", conn)
    df_kec_note = pd.read_sql_query("SELECT kecamatan, keterangan FROM kasus_kecamatan_dashboard", conn)
    df_arsip_g3 = pd.read_sql_query("SELECT * FROM riwayat_grafik3_kecamatan", conn)
    df_edu = pd.read_sql_query("SELECT * FROM konten_edukasi LIMIT 1", conn)
    conn.close()

    col_g1, col_g2 = st.columns(2)
    color_map = {
        "Stunting (%)": "#d32f2f",
        "Wasting (%)": "#f57c00",
        "Underweight (%)": "#1976d2",
        "Overweight (%)": "#7b1fa2"
    }

    with col_g1:
        st.markdown("### Tren Prevalensi Malnutrisi Indonesia")
        df_i = df_trend_indo.rename(columns={
            'stunting': 'Stunting (%)', 'wasting': 'Wasting (%)',
            'underweight': 'Underweight (%)', 'overweight': 'Overweight (%)'
        })
        fig_indo = px.line(
            df_i, x="tahun",
            y=["Stunting (%)", "Wasting (%)", "Underweight (%)", "Overweight (%)"],
            markers=True, title="Kondisi Nasional (Acuan SSGI 2024)",
            color_discrete_map=color_map
        )
        fig_indo.update_layout(yaxis_title="Prevalensi (%)", xaxis_title="Tahun", hovermode="x unified")
        st.plotly_chart(fig_indo, use_container_width=True)

    with col_g2:
        st.markdown("### Tren Prevalensi Malnutrisi Kota Bogor")
        df_b = df_trend_bogor.rename(columns={
            'stunting': 'Stunting (%)', 'wasting': 'Wasting (%)',
            'underweight': 'Underweight (%)', 'overweight': 'Overweight (%)'
        })
        fig_bogor = px.line(
            df_b, x="tahun",
            y=["Stunting (%)", "Wasting (%)", "Underweight (%)", "Overweight (%)"],
            markers=True,
            title="Kondisi Kota Bogor (SSGI 2024: Stunting 21,1% | Underweight 12,1%)",
            color_discrete_map=color_map
        )
        fig_bogor.update_layout(yaxis_title="Prevalensi (%)", xaxis_title="Tahun", hovermode="x unified")
        st.plotly_chart(fig_bogor, use_container_width=True)

    st.markdown("---")
    st.markdown("### Grafik 3 — Keterangan Titik Kasus per Kecamatan Kota Bogor (%)")
    st.caption("Dihitung otomatis dari inputan kader berdasarkan tahun dalam satuan persen (%), serta mendukung data arsip tahun sebelumnya dari upload Admin.")

    # --- AMBIL DATA OTOMATIS DARI DATABASE BALITA + ARSIP UPLOAD ADMIN ---
    df_balita = load_data()
    tahun_sekarang = datetime.now().year
    daftar_kecamatan = list(KOORDINAT_BOGOR.keys())
    map_keterangan = dict(zip(df_kec_note['kecamatan'], df_kec_note['keterangan'])) if len(df_kec_note) > 0 else {}

    tahun_set = {tahun_sekarang}

    if len(df_balita) > 0 and 'Waktu' in df_balita.columns:
        df_balita['Tahun'] = pd.to_datetime(df_balita['Waktu'], errors='coerce').dt.year
        tahun_set.update(df_balita['Tahun'].dropna().astype(int).tolist())
    else:
        df_balita = pd.DataFrame(columns=['Kecamatan', 'Stunting', 'Wasting', 'Overweight', 'Underweight', 'Tahun'])

    if len(df_arsip_g3) > 0:
        tahun_set.update(df_arsip_g3['tahun'].dropna().astype(int).tolist())

    tahun_tersedia = sorted(list(tahun_set), reverse=True)
    opsi_banding = ["Tahun Sebelumnya (Otomatis)"] + [str(t) for t in tahun_tersedia]

    # --- FILTER TAHUN & INDIKATOR ---
    c_f1, c_f2, c_f3 = st.columns([1, 1, 1.3])
    with c_f1:
        tahun_dipilih = st.selectbox("Pilih Tahun:", tahun_tersedia, index=0, key="g3_tahun_pilih")
    with c_f2:
        pilihan_banding = st.selectbox("Bandingkan dengan:", opsi_banding, index=0, key="g3_tahun_banding")
        tahun_banding = (tahun_dipilih - 1) if pilihan_banding == "Tahun Sebelumnya (Otomatis)" else int(pilihan_banding)
    with c_f3:
        indikator_fokus = st.selectbox(
            "Fokus Indikator pada Grafik:",
            ["Stunting", "Wasting", "Underweight", "Overweight", "Total Malnutrisi"],
            index=0,
            key="g3_indikator"
        )

    # --- FUNGSI HITUNG PERSENTASE (PRIORITAS: INPUT KADER -> FALLBACK: UPLOAD ADMIN) ---
    def hitung_persen_kecamatan(df_src, df_arsip, tahun_target):
        df_yr = df_src[df_src['Tahun'] == tahun_target] if len(df_src) > 0 else df_src
        df_ar = df_arsip[df_arsip['tahun'] == tahun_target] if len(df_arsip) > 0 else df_arsip
        rows = []
        for kec in daftar_kecamatan:
            sub = df_yr[df_yr['Kecamatan'] == kec]
            total = len(sub)

            if total > 0:
                n_s = int(sub['Stunting'].sum())
                n_w = int(sub['Wasting'].sum())
                n_o = int(sub['Overweight'].sum())
                n_u = int(sub['Underweight'].sum())
                n_mal = int(((sub['Stunting'] == 1) | (sub['Wasting'] == 1) |
                             (sub['Overweight'] == 1) | (sub['Underweight'] == 1)).sum())
                p_s = round((n_s / total) * 100, 1)
                p_w = round((n_w / total) * 100, 1)
                p_o = round((n_o / total) * 100, 1)
                p_u = round((n_u / total) * 100, 1)
                p_mal = round((n_mal / total) * 100, 1)
                ket = map_keterangan.get(kec, "Input otomatis Kader Posyandu")
                sumber = "Otomatis (Kader)"
            else:
                sub_a = df_ar[df_ar['kecamatan'].astype(str).str.strip().str.lower() == kec.lower()] if len(df_ar) > 0 else pd.DataFrame()
                if len(sub_a) > 0:
                    r_a = sub_a.iloc[0]
                    total = int(r_a['total_balita'])
                    p_s = round(float(r_a['stunting']), 1)
                    p_w = round(float(r_a['wasting']), 1)
                    p_o = round(float(r_a['overweight']), 1)
                    p_u = round(float(r_a['underweight']), 1)
                    p_mal = round(float(r_a['total_malnutrisi']), 1)
                    ket = str(r_a['keterangan']) if pd.notna(r_a['keterangan']) else "Data Arsip Admin"
                    sumber = "Arsip (Upload Admin)"
                else:
                    total = 0
                    p_s = p_w = p_o = p_u = p_mal = 0.0
                    ket = map_keterangan.get(kec, "Belum ada data")
                    sumber = "Kosong"

            rows.append({
                "Kecamatan": kec,
                "Total_Balita": total,
                "Stunting": p_s,
                "Wasting": p_w,
                "Overweight": p_o,
                "Underweight": p_u,
                "Total Malnutrisi": p_mal,
                "Keterangan": ket,
                "Sumber": sumber
            })
        return pd.DataFrame(rows)

    df_now = hitung_persen_kecamatan(df_balita, df_arsip_g3, tahun_dipilih)
    df_prev = hitung_persen_kecamatan(df_balita, df_arsip_g3, tahun_banding)

    kolom_plot = [
        'Kecamatan', 'Total_Balita', 'Stunting', 'Wasting',
        'Underweight', 'Overweight', 'Total Malnutrisi', 'Keterangan', 'Sumber'
    ]

    df_now_plot = df_now[kolom_plot].copy()
    df_now_plot['Periode'] = f"Tahun {tahun_dipilih}"
    df_now_plot['Label_Titik'] = df_now_plot.apply(
        lambda r: f"{r['Kecamatan']}: {float(r[indikator_fokus]):.1f}% {indikator_fokus}", axis=1
    )

    df_prev_plot = df_prev[kolom_plot].copy()
    df_prev_plot['Periode'] = f"Tahun {tahun_banding}"
    df_prev_plot['Label_Titik'] = df_prev_plot.apply(
        lambda r: f"{float(r[indikator_fokus]):.1f}%", axis=1
    )

    if tahun_banding != tahun_dipilih:
        df_plot = pd.concat([df_prev_plot, df_now_plot], ignore_index=True)
        warna_periode = {
            f"Tahun {tahun_banding}": "#90A4AE",
            f"Tahun {tahun_dipilih}": "#00695C"
        }
    else:
        df_plot = df_now_plot
        warna_periode = {f"Tahun {tahun_dipilih}": "#00695C"}

    fig_kec = px.line(
        df_plot,
        x="Kecamatan",
        y=indikator_fokus,
        color="Periode",
        markers=True,
        text="Label_Titik",
        color_discrete_map=warna_periode,
        hover_data={
            "Kecamatan": True,
            "Periode": True,
            "Sumber": True,
            "Total_Balita": True,
            "Stunting": ":.1f",
            "Wasting": ":.1f",
            "Underweight": ":.1f",
            "Overweight": ":.1f",
            "Total Malnutrisi": ":.1f",
            "Keterangan": True,
            "Label_Titik": False
        },
        labels={
            indikator_fokus: f"{indikator_fokus} (%)",
            "Total_Balita": "Total Balita Diperiksa",
            "Stunting": "Stunting (%)",
            "Wasting": "Wasting (%)",
            "Underweight": "Underweight (%)",
            "Overweight": "Overweight (%)",
            "Total Malnutrisi": "Total Malnutrisi (%)"
        },
        title=f"Perbandingan Persentase {indikator_fokus} per Kecamatan Kota Bogor ({tahun_dipilih} vs {tahun_banding})"
    )
    fig_kec.update_traces(textposition="top center", line=dict(width=3), marker=dict(size=10))
    max_y = float(df_plot[indikator_fokus].max()) if len(df_plot) > 0 else 0.0
    fig_kec.update_layout(
        yaxis_title="Persentase Kasus (%)",
        yaxis=dict(range=[0, max(100, max_y + 15)], ticksuffix="%"),
        xaxis_title="Kecamatan",
        hovermode="x unified"
    )
    st.plotly_chart(fig_kec, use_container_width=True)

    # --- KARTU PERBANDINGAN TREN NAIK / TURUN PER KECAMATAN ---
    st.markdown(f"**Ringkasan Tren {indikator_fokus} ({tahun_dipilih} vs {tahun_banding}):**")
    cols_m = st.columns(3)
    for idx, kec in enumerate(daftar_kecamatan):
        val_now = float(df_now.loc[df_now['Kecamatan'] == kec, indikator_fokus].values[0])
        val_prev = float(df_prev.loc[df_prev['Kecamatan'] == kec, indikator_fokus].values[0])
        sumber_prev = df_prev.loc[df_prev['Kecamatan'] == kec, 'Sumber'].values[0]
        selisih = round(val_now - val_prev, 1)

        with cols_m[idx % 3]:
            if sumber_prev == "Kosong":
                st.metric(
                    label=kec,
                    value=f"{val_now:.1f}%",
                    delta=f"Data {tahun_banding} kosong",
                    delta_color="off"
                )
            else:
                st.metric(
                    label=kec,
                    value=f"{val_now:.1f}%",
                    delta=f"{selisih:+.1f}% vs {tahun_banding}",
                    delta_color="inverse"
                )

    # --- TABEL RINCIAN PERSENTASE & STATUS PENURUNAN ---
    with st.expander(f"Lihat Rincian Tabel Persentase Tahun {tahun_dipilih} & Perbandingan ({tahun_banding})"):
        df_tabel = df_now[['Kecamatan', 'Sumber', 'Total_Balita', 'Stunting', 'Wasting', 'Underweight', 'Overweight', 'Total Malnutrisi']].copy()
        df_tabel[f'{indikator_fokus} {tahun_banding} (%)'] = df_prev[indikator_fokus].values

        def status_tren(row):
            sumber_p = df_prev.loc[df_prev['Kecamatan'] == row['Kecamatan'], 'Sumber'].values[0]
            if sumber_p == "Kosong":
                return f"Belum ada data {tahun_banding}"
            diff = round(float(row[indikator_fokus]) - float(row[f'{indikator_fokus} {tahun_banding} (%)']), 1)
            if diff < 0:
                return f"Menurun {abs(diff):.1f}%"
            elif diff > 0:
                return f"Meningkat +{diff:.1f}%"
            return "Stabil (0.0%)"

        df_tabel['Status Tren'] = df_tabel.apply(status_tren, axis=1)
        df_tabel = df_tabel.rename(columns={
            'Total_Balita': f'Balita Diperiksa ({tahun_dipilih})',
            'Stunting': 'Stunting (%)',
            'Wasting': 'Wasting (%)',
            'Underweight': 'Underweight (%)',
            'Overweight': 'Overweight (%)',
            'Total Malnutrisi': 'Total Malnutrisi (%)'
        })
        st.dataframe(df_tabel, use_container_width=True, hide_index=True)

    st.markdown("---")
    col_edu1, col_edu2 = st.columns(2)
    with col_edu1:
        st.subheader(df_edu['judul_definisi'][0])
        st.info(df_edu['teks_definisi'][0])
    with col_edu2:
        st.subheader(df_edu['judul_protokol'][0])
        st.success(df_edu['teks_protokol'][0])

# =====================================================================
# HALAMAN LOGIN
# =====================================================================
def login_page():
    img_path = "image_4f3773.png"
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()
        st.markdown(f"""
        <style>
        .stApp {{ background-image: url("data:image/png;base64,{encoded_string}"); background-size: cover; background-position: center; background-attachment: fixed; }}
        header[data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
        </style>
        """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    [data-testid="stForm"] { background: rgba(20, 25, 30, 0.55) !important; backdrop-filter: blur(12px) !important; -webkit-backdrop-filter: blur(12px) !important; border-radius: 20px !important; border: 1px solid rgba(255, 255, 255, 0.25) !important; padding: 40px !important; box-shadow: 0 15px 40px 0 rgba(0, 0, 0, 0.7) !important; }
    [data-testid="stForm"] p, [data-testid="stForm"] label, [data-testid="stForm"] h4 { color: #ffffff !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.8) !important; font-weight: 600; }
    .stTextInput input { background-color: rgba(255, 255, 255, 0.85) !important; border-radius: 8px !important; color: #000000 !important; }
    [data-testid="stForm"] div.stButton > button { background-color: #00897B !important; color: white !important; width: 100%; border-radius: 8px !important; border: none !important; margin-top: 10px; }
    [data-testid="stForm"] div.stButton > button:hover { background-color: #004D40 !important; }
    .login-title { text-align: center; color: white; text-shadow: 2px 4px 6px rgba(0,0,0,0.95); font-weight: 900; font-size: 3.5rem; margin-bottom: 0px; margin-top: -40px; }
    .login-subtitle { text-align: center; color: #b2dfdb; text-shadow: 2px 3px 5px rgba(0,0,0,0.95); font-weight: 700; font-size: 1.5rem; margin-bottom: 50px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='login-title'>Dinas Kesehatan Kota Bogor</h1>", unsafe_allow_html=True)
    st.markdown("<p class='login-subtitle'>Sistem Cerdas Pendukung Keputusan Malnutrisi Balita</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if st.session_state.get("session_expired_msg"):
            st.warning("⏱️ Sesi Anda telah berakhir karena tidak ada aktivitas selama 10 menit. Silakan login kembali.")
            st.session_state.session_expired_msg = False

        with st.form("login_form"):
            st.markdown("#### Akses Masuk Sistem")
            st.markdown("<br>", unsafe_allow_html=True)
            username = st.text_input("Username Identitas")
            password = st.text_input("Kata Sandi", type="password")
            if st.form_submit_button("Masuk (Login)"):
                conn = get_db_connection()
                user = conn.cursor().execute(
                    "SELECT role, kecamatan, kelurahan, nama_posyandu, alamat_posyandu FROM users WHERE username=? AND password=?",
                    (username, password)
                ).fetchone()
                conn.close()
                if user:
                    create_session(username, user[0], user[1], user[2], user[3], user[4])
                    st.rerun()
                else:
                    st.error("Kredensial tidak valid! Periksa username/password.")

# =====================================================================
# HALAMAN KADER POSYANDU
# =====================================================================
def kader_page():
    set_dinkes_theme()
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Lambang_Kota_Bogor.png/438px-Lambang_Kota_Bogor.png", width=100)
    st.sidebar.title("Kader Posyandu")
    st.sidebar.info(f"Login sebagai: **{st.session_state.username}**")

    user_kec = st.session_state.kecamatan
    user_kel = st.session_state.kelurahan or "-"
    user_pos = st.session_state.nama_posyandu
    user_almt = st.session_state.alamat_posyandu or "-"
    is_locked = user_kec in KOORDINAT_BOGOR

    if is_locked:
        st.sidebar.success(f"📍 Area Tugas:\n\n**{user_pos}**\nKel. {user_kel}, Kec. {user_kec}\n\n🏠 {user_almt}")
    else:
        st.sidebar.warning("📍 Area Tugas:\n\n**Semua Wilayah**")

    render_ganti_password_sidebar()

    if st.sidebar.button("Keluar (Logout)"):
        destroy_session(expired=False)
        st.rerun()

    st.title("Pusat Pengendalian Posyandu")
    tab1, tab2, tab3 = st.tabs(["🏠 Dashboard Utama", "📝 Input Rekam Medis", "🗺️ Peta Pantauan"])

    with tab1:
        render_dashboard_utama()

    with tab2:
        st.subheader("Input Data Individu")
        with st.form("form_individu"):
            c1, c2 = st.columns(2)
            nama = c1.text_input("Nama Lengkap Balita")
            nama_ibu = c1.text_input("Nama Lengkap Ibu")
            nik_ibu = c1.text_input("NIK Ibu (16 Digit)", max_chars=16, placeholder="Contoh: 327101xxxxxxxxxx")
            jk = c1.selectbox("Jenis Kelamin", ["Laki-Laki", "Perempuan"])

            if is_locked:
                c2.text_input("Lokasi Posyandu & Kelurahan", value=f"{user_pos} — Kel. {user_kel}, Kec. {user_kec}", disabled=True)
                c2.text_input("Alamat Posyandu", value=user_almt, disabled=True)
                kecamatan, kelurahan, posyandu, alamat_pos = user_kec, user_kel, user_pos, user_almt
            else:
                kecamatan = c2.selectbox("Lokasi Kecamatan", list(KOORDINAT_BOGOR.keys()))
                kelurahan = c2.text_input("Kelurahan", value="-")
                posyandu = c2.text_input("Nama Posyandu", value="Posyandu Umum")
                alamat_pos = c2.text_input("Alamat Posyandu", value="-")

            umur = c2.number_input("Umur (Bulan)", min_value=0, max_value=60, value=24)
            tinggi = c2.number_input("Tinggi Badan (cm)", min_value=40.0, max_value=120.0, value=80.0)
            berat = c2.number_input("Berat Badan (kg)", min_value=1.0, max_value=30.0, value=10.0)

            if st.form_submit_button("Prediksi MLRF & Simpan Database"):
                if not nama or not nama_ibu or not nik_ibu:
                    st.warning("Harap lengkapi Nama Balita, Nama Ibu, dan NIK Ibu terlebih dahulu.")
                else:
                    jk_enc = 0 if jk == "Laki-Laki" else 1
                    pred_label, pred_status, pred_zs = prediksi_malnutrisi_detail(jk_enc, umur, tinggi, berat)
                    s, w, o, u = pred_label
                    stat_s, stat_w, stat_o, stat_u = pred_status
                    zs_s, zs_w, zs_o, zs_u = pred_zs

                    lat_j = KOORDINAT_BOGOR[kecamatan]['lat'] + np.random.uniform(-0.005, 0.005)
                    lon_j = KOORDINAT_BOGOR[kecamatan]['lon'] + np.random.uniform(-0.005, 0.005)

                    df_baru = pd.DataFrame([{
                        "Waktu": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Kecamatan": kecamatan, "Kelurahan": kelurahan,
                        "Nama_Posyandu": posyandu, "Alamat_Posyandu": alamat_pos,
                        "Nama_Balita": nama, "Nama_Ibu": nama_ibu, "NIK_Ibu": nik_ibu,
                        "JK": jk, "Umur": umur, "Tinggi": tinggi, "Berat": berat,
                        "Stunting": s, "Wasting": w, "Overweight": o, "Underweight": u,
                        "Status_Stunting": stat_s, "Status_Wasting": stat_w, "Status_Overweight": stat_o, "Status_Underweight": stat_u,
                        "ZS_Stunting": zs_s, "ZS_Wasting": zs_w, "ZS_Overweight": zs_o, "ZS_Underweight": zs_u,
                        "Lat": lat_j, "Lon": lon_j
                    }])
                    conn = get_db_connection()
                    df_baru.to_sql('data_balita', conn, if_exists='append', index=False)
                    conn.close()
                    st.success(f"Rekam medis **{nama}** (Ibu: {nama_ibu}) tersimpan. Status AI: {stat_s} | {stat_w} | {stat_o} | {stat_u} — Z-Score Permenkes: TB/U({zs_s}), BB/TB({zs_w}), IMT/U({zs_o}), BB/U({zs_u})")

        st.markdown("---")
        st.subheader("Upload Massal (Data Kolektif Posyandu)")
        csv_template = "Nama,Nama_Ibu,NIK_Ibu,JK,Umur,Tinggi,Berat\nBudi,Siti Aminah,3271010101900001,Laki-Laki,24,80.5,10.2\nAyu,Dewi Lestari,3271010202920002,Perempuan,36,90.0,12.5"
        st.download_button(label="📥 Download Template CSV", data=csv_template, file_name="Template_Upload_Posyandu.csv", mime="text/csv")

        if is_locked:
            st.info(f"Sistem akan menetapkan seluruh data CSV ini ke **{user_pos}** — Kel. {user_kel}, Kec. {user_kec} ({user_almt}).")

        file_csv = st.file_uploader("Unggah file CSV (Sesuai Template)", type=['csv'])
        if file_csv and st.button("Proses Seluruh Data via Model AI"):
            df_upload = pd.read_csv(file_csv, dtype={'NIK_Ibu': str})
            hasil_list = []
            for _, row in df_upload.iterrows():
                jk_enc = 0 if str(row['JK']).strip().lower() in ['l', 'laki-laki', 'pria'] else 1
                pred_label, pred_status, pred_zs = prediksi_malnutrisi_detail(jk_enc, row['Umur'], row['Tinggi'], row['Berat'])
                s, w, o, u = pred_label
                stat_s, stat_w, stat_o, stat_u = pred_status
                zs_s, zs_w, zs_o, zs_u = pred_zs

                kec = user_kec if is_locked else row.get('Kecamatan', list(KOORDINAT_BOGOR.keys())[0])
                kel = user_kel if is_locked else row.get('Kelurahan', '-')
                pos = user_pos if is_locked else row.get('Nama_Posyandu', 'Posyandu Umum')
                almt = user_almt if is_locked else row.get('Alamat_Posyandu', '-')
                lat_b = KOORDINAT_BOGOR.get(kec, KOORDINAT_BOGOR["Bogor Tengah"])['lat']
                lon_b = KOORDINAT_BOGOR.get(kec, KOORDINAT_BOGOR["Bogor Tengah"])['lon']

                hasil_list.append({
                    "Waktu": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Kecamatan": kec, "Kelurahan": kel, "Nama_Posyandu": pos, "Alamat_Posyandu": almt,
                    "Nama_Balita": row['Nama'],
                    "Nama_Ibu": row.get('Nama_Ibu', '-'),
                    "NIK_Ibu": str(row.get('NIK_Ibu', '-')),
                    "JK": row['JK'], "Umur": row['Umur'], "Tinggi": row['Tinggi'], "Berat": row['Berat'],
                    "Stunting": s, "Wasting": w, "Overweight": o, "Underweight": u,
                    "Status_Stunting": stat_s, "Status_Wasting": stat_w, "Status_Overweight": stat_o, "Status_Underweight": stat_u,
                    "ZS_Stunting": zs_s, "ZS_Wasting": zs_w, "ZS_Overweight": zs_o, "ZS_Underweight": zs_u,
                    "Lat": lat_b + np.random.uniform(-0.005, 0.005), "Lon": lon_b + np.random.uniform(-0.005, 0.005)
                })
            conn = get_db_connection()
            pd.DataFrame(hasil_list).to_sql('data_balita', conn, if_exists='append', index=False)
            conn.close()
            st.success(f"{len(df_upload)} balita berhasil diklasifikasikan oleh AI dan disimpan di database!")

    with tab3:
        st.subheader("📊 Statistik Wilayah & Rekam Medis (Kader Posyandu)")
        df_db = load_data()
        if len(df_db) > 0:
            c_rekap1, c_rekap2 = st.columns([1, 1.4])
            with c_rekap1:
                st.markdown("**Rekapitulasi per Kecamatan:**")
                rekap_kec = df_db.groupby('Kecamatan').agg(
                    Balita=('Nama_Balita', 'count'), Stunting=('Stunting', 'sum'),
                    Wasting=('Wasting', 'sum'), Overweight=('Overweight', 'sum'), Underweight=('Underweight', 'sum')
                ).reset_index()
                st.dataframe(rekap_kec, use_container_width=True, hide_index=True)

            with c_rekap2:
                st.markdown("**Rekapitulasi per Posyandu (Otomatis Kecamatan, Kelurahan & Alamat):**")
                rekap_pos = df_db.groupby(['Kecamatan', 'Kelurahan', 'Nama_Posyandu', 'Alamat_Posyandu']).agg(
                    Balita=('Nama_Balita', 'count'), Stunting=('Stunting', 'sum'),
                    Wasting=('Wasting', 'sum'), Overweight=('Overweight', 'sum'), Underweight=('Underweight', 'sum')
                ).reset_index()
                st.dataframe(rekap_pos, use_container_width=True, hide_index=True)

            st.markdown("---")

            pilih_pos = st.selectbox("Pilih Posyandu untuk detail rekam medis anak:", df_db['Nama_Posyandu'].unique())
            df_detail = df_db[df_db['Nama_Posyandu'] == pilih_pos][[
                'Nama_Balita', 'Nama_Ibu', 'NIK_Ibu', 'JK', 'Umur', 'Tinggi', 'Berat',
                'ZS_Stunting', 'ZS_Wasting', 'ZS_Overweight', 'ZS_Underweight',
                'Status_Stunting', 'Status_Wasting', 'Status_Overweight', 'Status_Underweight'
            ]].copy()
            df_detail.rename(columns={
                'Nama_Ibu': 'Nama Ibu', 'NIK_Ibu': 'NIK Ibu',
                'ZS_Stunting': 'Z-Score Stunting', 'ZS_Wasting': 'Z-Score Wasting',
                'ZS_Overweight': 'Z-Score Overweight', 'ZS_Underweight': 'Z-Score Underweight',
                'Status_Stunting': 'Indikator TB/U', 'Status_Wasting': 'Indikator BB/TB',
                'Status_Overweight': 'Risiko Lebih', 'Status_Underweight': 'Indikator BB/U'
            }, inplace=True)

            render_pagination(df_detail, page_size=10, key_prefix=f"kader_pg_{pilih_pos}")

            st.markdown("---")
            st.subheader("🗺️ Visualisasi Geografis (Peta Sebaran)")
            df_map = df_db.copy()
            df_map['Total_Risiko'] = df_map[['Stunting', 'Wasting', 'Overweight', 'Underweight']].sum(axis=1)
            df_map['Ukuran_Titik'] = (df_map['Total_Risiko'] * 4) + 6

            fig = px.scatter_map(
                df_map, lat="Lat", lon="Lon", color="Total_Risiko", size="Ukuran_Titik",
                hover_name="Nama_Balita",
                hover_data=["Kecamatan", "Kelurahan", "Nama_Posyandu", "Alamat_Posyandu", "ZS_Stunting", "ZS_Wasting", "ZS_Overweight", "ZS_Underweight"],
                color_continuous_scale=["#1B5E20", "#Fbc02D", "#E65100", "#B71C1C"],
                range_color=[0, 4],
                size_max=18, zoom=11.5, map_style="open-street-map"
            )
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Peta dan Statistik akan muncul setelah data diinput.")

# =====================================================================
# HALAMAN ADMIN
# =====================================================================
def admin_page():
    set_dinkes_theme()
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Lambang_Kota_Bogor.png/438px-Lambang_Kota_Bogor.png", width=100)
    st.sidebar.title("Admin Dinkes")
    st.sidebar.info(f"Login sebagai: **{st.session_state.username}**")

    render_ganti_password_sidebar()

    if st.sidebar.button("Keluar (Logout)"):
        destroy_session(expired=False)
        st.rerun()

    st.title("Panel Eksekutif Dinas Kesehatan")
    df_db = load_data()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Dashboard Utama", "📊 Database Terpusat", "🗺️ Laporan Spasial",
        "👥 Manajemen Akun Kader", "⚙️ Pengaturan Konten"
    ])

    with tab1:
        render_dashboard_utama()

    with tab2:
        st.subheader("Rekam Medis Terpusat Seluruh Posyandu Kota Bogor")
        if len(df_db) > 0:
            df_admin = df_db[[
                'Waktu', 'Kecamatan', 'Kelurahan', 'Nama_Posyandu', 'Alamat_Posyandu',
                'Nama_Balita', 'Nama_Ibu', 'NIK_Ibu', 'JK', 'Umur', 'Tinggi', 'Berat',
                'ZS_Stunting', 'ZS_Wasting', 'ZS_Overweight', 'ZS_Underweight',
                'Status_Stunting', 'Status_Wasting', 'Status_Overweight', 'Status_Underweight'
            ]].copy()
            df_admin.rename(columns={
                'Alamat_Posyandu': 'Alamat Posyandu',
                'Nama_Ibu': 'Nama Ibu', 'NIK_Ibu': 'NIK Ibu',
                'ZS_Stunting': 'Z-Score Stunting', 'ZS_Wasting': 'Z-Score Wasting',
                'ZS_Overweight': 'Z-Score Overweight', 'ZS_Underweight': 'Z-Score Underweight'
            }, inplace=True)
            render_pagination(df_admin, page_size=10, key_prefix="admin_pg_utama")

            c_dl, c_del = st.columns([2, 1])
            with c_dl:
                st.download_button("📥 Download Database Lengkap (CSV)", df_db.to_csv(index=False).encode('utf-8'), "Database_Dinkes.csv", "text/csv")
            with c_del:
                st.warning("⚠️ Peringatan: Tindakan ini akan menghapus seluruh data balita secara permanen.")
                konfirmasi = st.checkbox("Saya menyadari dan yakin ingin mengosongkan database")
                if st.button("🚨 Hapus Seluruh Database (Balita)", disabled=not konfirmasi):
                    hapus_database()
                    st.success("Database berhasil dikosongkan.")
                    st.rerun()
        else:
            st.info("Database masih kosong.")

    with tab3:
        st.subheader("Laporan Geospasial Malnutrisi Kota Bogor")
        if len(df_db) > 0:
            c_rekap1, c_rekap2 = st.columns([1, 1.4])
            with c_rekap1:
                st.markdown("**Rekapitulasi per Kecamatan:**")
                rekap_kec = df_db.groupby('Kecamatan').agg(
                    Balita=('Nama_Balita', 'count'), Stunting=('Stunting', 'sum'),
                    Wasting=('Wasting', 'sum'), Overweight=('Overweight', 'sum'), Underweight=('Underweight', 'sum')
                ).reset_index()
                st.dataframe(rekap_kec, use_container_width=True, hide_index=True)
            with c_rekap2:
                st.markdown("**Rekapitulasi Terpusat per Posyandu:**")
                rekap_pos = df_db.groupby(['Kecamatan', 'Kelurahan', 'Nama_Posyandu', 'Alamat_Posyandu']).agg(
                    Balita=('Nama_Balita', 'count'), Stunting=('Stunting', 'sum'),
                    Wasting=('Wasting', 'sum'), Overweight=('Overweight', 'sum'), Underweight=('Underweight', 'sum')
                ).reset_index()
                st.dataframe(rekap_pos, use_container_width=True, hide_index=True)
                st.download_button("📥 Download Laporan Wilayah", rekap_pos.to_csv(index=False).encode('utf-8'), "Laporan_Wilayah.csv", "text/csv")

            st.markdown("---")
            st.subheader("🗺️ Peta Analisis Lokasi Balita (Scatter Map)")
            df_map = df_db.copy()
            df_map['Total_Risiko'] = df_map[['Stunting', 'Wasting', 'Overweight', 'Underweight']].sum(axis=1)
            df_map['Ukuran_Titik'] = (df_map['Total_Risiko'] * 4) + 6
            fig = px.scatter_map(
                df_map, lat="Lat", lon="Lon", color="Total_Risiko", size="Ukuran_Titik",
                hover_name="Nama_Balita",
                hover_data=["Kecamatan", "Kelurahan", "Nama_Posyandu", "Alamat_Posyandu", "ZS_Stunting", "ZS_Wasting", "ZS_Overweight", "ZS_Underweight"],
                color_continuous_scale=["#1B5E20", "#Fbc02D", "#E65100", "#B71C1C"],
                range_color=[0, 4],
                size_max=18, zoom=11.5, map_style="open-street-map"
            )
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Peta belum dapat ditampilkan. Database masih kosong.")

    with tab4:
        st.subheader("Manajemen Akun Sistem")
        c_form, c_list = st.columns([1, 1.5])

        conn = get_db_connection()
        list_kader = pd.read_sql_query("SELECT username FROM users WHERE role='kader'", conn)['username'].tolist()
        df_users_kader = pd.read_sql_query(
            "SELECT username, kecamatan, kelurahan, nama_posyandu, alamat_posyandu, penanggung_jawab FROM users WHERE role='kader'",
            conn
        )
        conn.close()

        with c_form:
            with st.expander("➕ Buat Akun Kader Baru", expanded=True):
                show_new_pw = st.toggle("👁️ Tampilkan Password", key="toggle_pw_baru")
                with st.form("form_tambah_akun", clear_on_submit=True):
                    new_user = st.text_input("Username Baru")
                    new_pass = st.text_input("Password", type="default" if show_new_pw else "password")
                    new_kec = st.selectbox("Area Penugasan (Kecamatan)", list(KOORDINAT_BOGOR.keys()))
                    new_kel = st.text_input("Kelurahan (Contoh: Cilendek Barat)")
                    new_pos = st.text_input("Nama Posyandu (Contoh: Posyandu Melati 1)")
                    new_almt = st.text_area("Alamat Lengkap Posyandu", height=80, placeholder="Contoh: Jl. Merdeka RW 05 No. 12")
                    new_pj = st.text_input("Nama Penanggung Jawab")
                    if st.form_submit_button("Buat Akun"):
                        if new_user and new_pass and new_kel and new_pos and new_almt and new_pj:
                            try:
                                conn = get_db_connection()
                                conn.cursor().execute(
                                    "INSERT INTO users (username, password, role, kecamatan, kelurahan, nama_posyandu, alamat_posyandu, penanggung_jawab) VALUES (?, ?, 'kader', ?, ?, ?, ?, ?)",
                                    (new_user, new_pass, new_kec, new_kel, new_pos, new_almt, new_pj)
                                )
                                conn.commit()
                                conn.close()
                                st.success(f"Akun kader '{new_user}' untuk {new_pos} (Kel. {new_kel}) berhasil dibuat!")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("Username tersebut sudah terdaftar!")
                        else:
                            st.warning("Lengkapi semua isian form termasuk Kelurahan dan Alamat Posyandu.")

            with st.expander("🔄 Reset Password Kader", expanded=False):
                show_reset_pw = st.toggle("👁️ Tampilkan Password", key="toggle_pw_reset")
                with st.form("form_reset_password", clear_on_submit=True):
                    reset_user = st.selectbox("Pilih Akun Kader", list_kader if list_kader else ["Tidak ada akun"])
                    reset_pass = st.text_input("Password Baru", type="default" if show_reset_pw else "password")
                    if st.form_submit_button("Reset Password") and list_kader:
                        if reset_pass:
                            conn = get_db_connection()
                            conn.cursor().execute("UPDATE users SET password=? WHERE username=?", (reset_pass, reset_user))
                            conn.commit()
                            conn.close()
                            st.success(f"Password untuk akun '{reset_user}' berhasil direset!")
                        else:
                            st.warning("Masukkan password baru terlebih dahulu.")

            with st.expander("🗑️ Hapus Akun Kader", expanded=False):
                with st.form("form_hapus_akun"):
                    hapus_user = st.selectbox("Pilih Akun yang Dihapus", list_kader if list_kader else ["Tidak ada akun"])
                    if st.form_submit_button("Hapus Akun Permanen") and list_kader:
                        conn = get_db_connection()
                        conn.cursor().execute("DELETE FROM users WHERE username=?", (hapus_user,))
                        conn.commit()
                        conn.close()
                        st.success(f"Akun '{hapus_user}' telah dihapus!")
                        st.rerun()

        with c_list:
            st.markdown("##### 📋 Daftar Akun Kader Terdaftar")
            st.dataframe(df_users_kader, use_container_width=True, hide_index=True)

    with tab5:
        st.subheader("CMS: Pengaturan Konten Dashboard Utama")
        conn = get_db_connection()
        df_tren_indo_db = pd.read_sql_query("SELECT * FROM tren_malnutrisi ORDER BY tahun", conn)
        df_tren_bogor_db = pd.read_sql_query("SELECT * FROM tren_malnutrisi_bogor ORDER BY tahun", conn)
        df_edu_db = pd.read_sql_query("SELECT * FROM konten_edukasi LIMIT 1", conn)
        conn.close()

        c_edit1, c_edit2 = st.columns(2)
        with c_edit1:
            st.markdown("##### 1. Edit Grafik Tren Indonesia (SSGI)")
            edited_indo = st.data_editor(df_tren_indo_db, num_rows="dynamic", use_container_width=True, hide_index=True, key="editor_indo")
            if st.button("💾 Simpan Tren Indonesia"):
                conn = get_db_connection()
                conn.cursor().execute("DELETE FROM tren_malnutrisi")
                edited_indo.to_sql('tren_malnutrisi', conn, if_exists='append', index=False)
                conn.commit()
                conn.close()
                st.success("Data grafik tren Indonesia diperbarui!")
                st.rerun()

        with c_edit2:
            st.markdown("##### 2. Edit Grafik Tren Kota Bogor (SSGI)")
            edited_bogor = st.data_editor(df_tren_bogor_db, num_rows="dynamic", use_container_width=True, hide_index=True, key="editor_bogor")
            if st.button("💾 Simpan Tren Kota Bogor"):
                conn = get_db_connection()
                conn.cursor().execute("DELETE FROM tren_malnutrisi_bogor")
                edited_bogor.to_sql('tren_malnutrisi_bogor', conn, if_exists='append', index=False)
                conn.commit()
                conn.close()
                st.success("Data grafik tren Kota Bogor diperbarui!")
                st.rerun()

        st.markdown("---")
        render_upload_grafik3_admin()

        st.markdown("---")
        st.markdown("##### 4. Edit Edukasi & Protokol Medis")
        with st.form("form_edit_edukasi"):
            j_def = st.text_input("Judul Definisi Malnutrisi", value=df_edu_db['judul_definisi'][0])
            t_def = st.text_area("Isi Penjelasan Definisi (Mendukung Markdown)", value=df_edu_db['teks_definisi'][0], height=250)
            j_prot = st.text_input("Judul Protokol Penanganan", value=df_edu_db['judul_protokol'][0])
            t_prot = st.text_area("Isi Protokol Medis (Mendukung Markdown)", value=df_edu_db['teks_protokol'][0], height=250)
            if st.form_submit_button("💾 Simpan Perubahan Teks Edukasi"):
                conn = get_db_connection()
                conn.cursor().execute(
                    "UPDATE konten_edukasi SET judul_definisi=?, teks_definisi=?, judul_protokol=?, teks_protokol=? WHERE id=1",
                    (j_def, t_def, j_prot, t_prot)
                )
                conn.commit()
                conn.close()
                st.success("Teks Edukasi berhasil diperbarui!")
                st.rerun()

# =====================================================================
# KONTROL NAVIGASI
# =====================================================================
if st.session_state.role is None:
    login_page()
elif st.session_state.role == "kader":
    kader_page()
elif st.session_state.role == "admin":
    admin_page()
