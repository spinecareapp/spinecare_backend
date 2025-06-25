import base64
import cv2
import numpy as np
import mediapipe as mp
import torch
import torch.nn as nn
import pickle
from collections import deque, defaultdict
from datetime import datetime
from bson import ObjectId
import time
from flask import request

from app import db, socketio
from flask_socketio import emit

# ================================
# A. Load Model & Label Encoder
# ================================

print("[INFO] Memuat model LSTM dan label encoder...")

class PoseLSTM(nn.Module):
    def __init__(self, input_size=132, hidden_size=128, num_classes=12):
        super(PoseLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        return self.fc(h_n[-1])

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = "./model_weights/final_lstm_pose_model.pt"
ENCODER_PATH = "./model_weights/final_label_encoder.pkl"

with open(ENCODER_PATH, "rb") as f:
    label_encoder = pickle.load(f)
    print(f"[DEBUG] Label encoder berisi kelas: {label_encoder.classes_}")

num_classes = len(label_encoder.classes_)
model = PoseLSTM(num_classes=num_classes).to(DEVICE)
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model.eval()
print(f"[INFO] Model berhasil dimuat. Perangkat: {DEVICE}")

# ================================
# B. MediaPipe Setup & Buffer
# ================================

print("[INFO] Inisialisasi MediaPipe dan buffer pengguna...")

mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils

holistic_model = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)

user_buffers = defaultdict(lambda: deque(maxlen=30))
sid_to_user = {} # <-- TAMBAHKAN BUKU TAMU INI

# ================================
# C. Socket.IO Handlers
# ================================

def handle_connect():
    print("[INFO] Client terhubung")

def handle_disconnected():
    sid = request.sid # Dapatkan SID dari koneksi yang baru saja putus
    print(f"[INFO] Client dengan SID {sid} terputus.")
    
    # Periksa buku tamu untuk melihat siapa pemilik SID ini
    if sid in sid_to_user:
        user_id = sid_to_user[sid]
        print(f"[CLEANUP] Membersihkan sesi dan buffer untuk user {user_id}...")
        
        # 1. Hapus buffer data landmark pengguna tersebut
        if user_id in user_buffers:
            del user_buffers[user_id]
            print(f"          -> Buffer untuk {user_id} dihapus.")
            
        # 2. Hapus entri dari buku tamu
        del sid_to_user[sid]
        print(f"          -> Entri SID {sid} dihapus.")
        
    else:
        print(f"[WARN] SID {sid} terputus tanpa pernah terdaftar di buku tamu.")

# Jangan lupa untuk meregister handle_disconnected di bawah
# socketio.on_event("disconnect", handle_disconnected)

def handle_message(message):
    print("[DEBUG] Pesan diterima:", message)

def handle_image(data):
    sid = request.sid
    start_time = time.time()
    
    try:
        user_id = data.get("userId")
        selected_pose = data.get("selected_pose")
        image_data = data.get("image_data")

        if not all([user_id, selected_pose, image_data]):
            raise ValueError("Data tidak lengkap dari klien")

        # Daftarkan pengguna di "buku tamu" jika ini interaksi pertama
        if sid not in sid_to_user:
            sid_to_user[sid] = user_id
            print(f"[INFO] SID {sid} terdaftar untuk user {user_id}")

        # 1. Decode gambar
        image_bytes = base64.b64decode(image_data)
        np_image = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 2. Proses dengan model MediaPipe yang sudah diinisialisasi (tanpa 'with')
        results = holistic_model.process(image_rgb)

        if not results.pose_landmarks:
            emit("response", {"status": "no_pose", "message": "Pose tidak terdeteksi"})
            return

        # 3. Ekstraksi dan simpan landmark ke buffer
        landmarks = results.pose_landmarks.landmark
        pose_row = np.array([[lmk.x, lmk.y, lmk.z, lmk.visibility] for lmk in landmarks]).flatten()
        pose_row = np.clip(pose_row, 0.0, 1.0)
        
        buffer = user_buffers[user_id]
        buffer.append(pose_row)

        # 4. Cek status buffering
        if len(buffer) < 30:
            emit("response", {"status": "buffering", "progress": len(buffer)})
            return

        # 5. Lakukan prediksi dengan model LSTM jika buffer sudah penuh
        input_seq = np.array(buffer)[np.newaxis, ...]
        input_tensor = torch.from_numpy(input_seq).float().to(DEVICE)

        with torch.no_grad():
            output = model(input_tensor)
            probs = torch.nn.functional.softmax(output, dim=1)[0]
            pred_index = torch.argmax(probs).item()
            pose_class = label_encoder.inverse_transform([pred_index])[0]
            confidence = probs[pred_index].item()

        # 6. (Opsional) Simpan ke database
        user = db.db.users.find_one({"_id": ObjectId(user_id)})
        gender = user.get("gender", "unknown") if user else "unknown"
        status = "Sesuai" if pose_class == selected_pose else "Tidak Sesuai"
        db.db.detections.insert_one({
            "userID": user_id,
            "namaGerakan": selected_pose,
            "keterangan": status,
            "gender": gender,
            "tanggal": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
        })
        
        # 7. Siapkan dan kirim respons kembali ke klien
        image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        mp_drawing.draw_landmarks(
            image_bgr,
            results.pose_landmarks,
            mp_holistic.POSE_CONNECTIONS, # Gunakan koneksi dari holistic
            mp_drawing.DrawingSpec(color=(71, 130, 141), thickness=2, circle_radius=4),
            mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=5, circle_radius=2),
        )
        _, buffer_img = cv2.imencode(".jpg", image_bgr)
        encoded_image = base64.b64encode(buffer_img).decode("utf-8")

        emit("response", {
            "status": "ok",
            "pose_class": pose_class,
            "prob": str(confidence),
            "imageData": encoded_image,
        })

    except Exception as e:
        print(f"[ERROR] Terjadi kesalahan di handle_image: {e}")
        emit("response", {"status": "error", "message": str(e)})
    finally:
        # Selalu cetak waktu proses untuk debugging performa
        processing_time = (time.time() - start_time) * 1000 # dalam milidetik
        print(f"[PERF] Waktu proses untuk frame ini: {processing_time:.2f} ms")

        
def handle_reset_buffer(data):
    user_id = data.get("userId")
    if user_id in user_buffers:
        user_buffers[user_id].clear()
        print(f"[INFO] Buffer untuk user {user_id} telah direset.")
    emit("response", {"status": "buffer_reset", "message": "Buffer berhasil direset."})        

# ================================
# D. Register Socket Events
# ================================

print("[INFO] Mendaftarkan event Socket.IO...")

socketio.on_event("connect", handle_connect)
socketio.on_event("disconnect", handle_disconnected)
socketio.on_event("message", handle_message)
socketio.on_event("image", handle_image)
socketio.on_event("reset_buffer", handle_reset_buffer)
