# server.py (Versi Modifikasi - Tanpa Ketergantungan API Key)
import os
import time
import yt_dlp
from flask import Flask, jsonify, request
from flask_cors import CORS

# --- KONFIGURASI ---
# TIDAK ADA LAGI API KEY YANG DIPERLUKAN
PORT = 3001
COOKIE_FILE = "cookies.txt"

app = Flask(__name__)
CORS(app)

# State disimpan di memori
state = {"nowPlaying": None, "queue": []}

# --- FUNGSI BANTUAN (MODIFIKASI) ---

# [MODIFIKASI 1] Fungsi AI Intro diganti dengan template teks sederhana
def get_ai_intro(song_title, artist):
    """
    Menghasilkan intro generik tanpa memanggil AI.
    """
    # Kita bisa buat beberapa template agar tidak monoton
    templates = [
        f"Selanjutnya, kita putarkan lagu spesial: {song_title}!",
        f"Ini dia request berikutnya, {song_title} dari {artist}!",
        f"Ayo kita dengarkan bersama {song_title}!"
    ]
    # Pilih salah satu secara acak (atau berurutan)
    # Untuk simpelnya, kita pakai yang pertama saja.
    return templates[0]

# [MODIFIKASI 2] Fungsi Pencarian diganti total untuk menggunakan pencarian internal yt-dlp
def search_youtube_and_get_stream(query):
    """
    Mencari video di YouTube menggunakan fitur pencarian yt-dlp, bukan API.
    Hanya akan mengambil hasil pertama.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1', # Otomatis mencari dan ambil 1 hasil pertama
    }
    # Gunakan cookie jika file ada, ini sangat penting
    if os.path.exists(COOKIE_FILE):
        ydl_opts['cookiefile'] = COOKIE_FILE

    try:
        # Langsung berikan query ke yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            
            # Karena kita pakai 'ytsearch1', hasilnya ada di dalam 'entries'
            if 'entries' in info and info['entries']:
                video_info = info['entries'][0]
                song_object = {
                    'id': video_info.get('id'),
                    'title': video_info.get('title', 'Judul Tidak Diketahui'),
                    'artist': video_info.get('uploader') or video_info.get('channel', 'Artis Tidak Diketahui'),
                    'stream_url': video_info.get('url'),
                    'duration': video_info.get('duration')
                }
                return song_object, None
            else:
                return None, "Lagu tidak ditemukan setelah diekstrak."

    except Exception as e:
        print(f"Error saat mencari dengan yt-dlp: {e}")
        return None, "Gagal mencari atau memproses lagu dari YouTube."

# --- API ENDPOINTS (Tidak ada yang berubah di sini) ---
@app.route('/api/status')
def get_status():
    return jsonify(state)

@app.route('/api/request', methods=['POST'])
def request_song():
    data = request.get_json()
    query, requester_name = data.get('query'), data.get('name', 'Anonymous')
    if not query: return jsonify({'error': 'Query tidak boleh kosong'}), 400

    song_object, error_message = search_youtube_and_get_stream(query)
    if error_message: return jsonify({'error': error_message}), 500
    
    song_object['requester'] = requester_name
    if not state["nowPlaying"]:
        song_object['intro'] = get_ai_intro(song_object['title'], song_object['artist'])
        song_object['start_time_utc'] = time.time()
        state["nowPlaying"] = song_object
        message = f"Langsung memutar: '{song_object['title']}'"
    else:
        state["queue"].append(song_object)
        message = f"'{song_object['title']}' telah ditambahkan!"
    return jsonify({'message': message})

@app.route('/api/skip', methods=['POST'])
def skip_song():
    if state["queue"]:
        next_song = state["queue"].pop(0)
        next_song['intro'] = get_ai_intro(next_song['title'], next_song['artist'])
        next_song['start_time_utc'] = time.time()
        state["nowPlaying"] = next_song
    else:
        state["nowPlaying"] = None
    return jsonify(state)

@app.route('/api/remove', methods=['POST'])
def remove_song():
    global state
    data = request.get_json()
    index_to_remove = data.get('index')
    if index_to_remove is None or not isinstance(index_to_remove, int):
        return jsonify({"error": "Indeks tidak valid"}), 400
    try:
        if 0 <= index_to_remove < len(state['queue']):
            removed_song = state['queue'].pop(index_to_remove)
            return jsonify({"success": True, "message": f"Lagu '{removed_song['title']}' dihapus."})
        else:
            return jsonify({"error": "Indeks di luar jangkauan"}), 404
    except Exception as e:
        return jsonify({"error": "Kesalahan server"}), 500

if __name__ == '__main__':
    print(f"Server Helper Lokal (Mode Tanpa API) berjalan di http://localhost:{PORT}")
    print("Pastikan file 'cookies.txt' ada di folder yang sama.")
    app.run(host='127.0.0.1', port=PORT, debug=False)
