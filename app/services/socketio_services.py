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
from flask_socketio import emit

# Pastikan 'app' dan 'socketio' diimpor dengan benar dari struktur proyek Anda
from app import db, socketio 

# ===================================================================
# FUNGSI NORMALISASI
# ===================================================================
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24

def normalize_landmarks(landmarks_row):
    landmarks = landmarks_row.reshape(33, 4)
    try:
        left_shoulder = landmarks[LEFT_SHOULDER][:2]
        right_shoulder = landmarks[RIGHT_SHOULDER][:2]
        left_hip = landmarks[LEFT_HIP][:2]
        right_hip = landmarks[RIGHT_HIP][:2]
    except IndexError:
        return landmarks_row.flatten()
    torso_center_x = (left_shoulder[0] + right_shoulder[0] + left_hip[0] + right_hip[0]) / 4
    torso_center_y = (left_shoulder[1] + right_shoulder[1] + left_hip[1] + right_hip[1]) / 4
    anchor = np.array([torso_center_x, torso_center_y])
    torso_size = np.linalg.norm(left_shoulder - right_shoulder) + 1e-6
    normalized_landmarks = landmarks.copy()
    for i in range(len(landmarks)):
        normalized_landmarks[i][0] = (landmarks[i][0] - anchor[0]) / torso_size
        normalized_landmarks[i][1] = (landmarks[i][1] - anchor[1]) / torso_size
        normalized_landmarks[i][2] = landmarks[i][2] / torso_size
    return normalized_landmarks.flatten()

# ================================
# A. LOAD MODEL & LABEL ENCODER
# ================================
print("[INFO] Memuat model LSTM dan label encoder...")

class PoseLSTM(nn.Module):
    def __init__(self, input_size=132, hidden_size=128, num_classes=12):
        super(PoseLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.dropout = nn.Dropout(p=0.3)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        out = h_n[-1]
        out = self.dropout(out)
        out = self.fc(out)
        return out

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = "./model_weights/best_lstm_pose_model.pt"
ENCODER_PATH = "./model_weights/final_label_encoder.pkl"

with open(ENCODER_PATH, "rb") as f:
    label_encoder = pickle.load(f)
num_classes = len(label_encoder.classes_)
model = PoseLSTM(num_classes=num_classes).to(DEVICE)
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model.eval()
print(f"[INFO] Model berhasil dimuat. Perangkat: {DEVICE}")

# ================================
# B. MEDIAPIPE SETUP & BUFFER
# ================================
print("[INFO] Inisialisasi MediaPipe dan buffer pengguna...")
mp_holistic = mp.solutions.holistic
holistic_model = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)
user_buffers = defaultdict(lambda: deque(maxlen=30))
sid_to_user = {}

# ================================
# C. SOCKET.IO HANDLERS
# ================================
def handle_connect():
    print(f"[INFO] Client terhubung: {request.sid}")

def handle_disconnected():
    sid = request.sid
    print(f"[INFO] Client dengan SID {sid} terputus.")
    if sid in sid_to_user:
        user_id = sid_to_user.pop(sid)
        if user_id in user_buffers:
            del user_buffers[user_id]
            print(f"[CLEANUP] Buffer dan sesi untuk user {user_id} telah dibersihkan.")

def handle_message(message):
    print(f"[DEBUG] Pesan umum diterima dari {request.sid}: {message}")

def handle_image(data):
    sid = request.sid
    try:
        user_id = data.get("userId")
        selected_pose = data.get("selected_pose")
        image_data = data.get("image_data")

        if not all([user_id, selected_pose, image_data]):
            return emit("response", {"status": "error", "message": "Data dari klien tidak lengkap"})

        if sid not in sid_to_user:
            sid_to_user[sid] = user_id

        image_bytes = base64.b64decode(image_data)
        np_image = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        results = holistic_model.process(image_rgb)

        if not results.pose_landmarks:
            return emit("response", {"status": "no_pose", "message": "Pose tidak terdeteksi"})

        landmarks = results.pose_landmarks.landmark
        pose_row = np.array([[lmk.x, lmk.y, lmk.z, lmk.visibility] for lmk in landmarks]).flatten()
        
        normalized_pose_row = normalize_landmarks(pose_row)
        
        buffer = user_buffers[user_id]
        buffer.append(normalized_pose_row)

        if len(buffer) < 30:
            return emit("response", {"status": "buffering", "progress": len(buffer)})

        input_seq = np.array(buffer)[np.newaxis, ...]
        input_tensor = torch.from_numpy(input_seq).float().to(DEVICE)

        with torch.no_grad():
            output = model(input_tensor)
            probs = torch.nn.functional.softmax(output, dim=1)[0]
            pred_index = torch.argmax(probs).item()
            predicted_class = label_encoder.inverse_transform([pred_index])[0]
            confidence = probs[pred_index].item()
        
        # ==========================================================
        # <<< JURUS TERAKHIR: LOGIKA PERBANDINGAN PINTAR >>>
        # ==========================================================
        # 1. Bersihkan kedua string dengan mengubahnya ke huruf kecil,
        #    mengganti tanda hubung dengan spasi, dan menghapus spasi ekstra.
        clean_predicted = predicted_class.lower().replace('-', ' ').strip()
        clean_selected = selected_pose.lower().replace('-', ' ').strip()
        
        # 2. Lakukan perbandingan menggunakan versi yang sudah bersih.
        is_match = clean_predicted == clean_selected

        # 3. Tentukan status berdasarkan hasil perbandingan yang sudah "pintar".
        status = "Sesuai" if is_match else "Tidak Sesuai"

        # (Opsional) Tambahkan print untuk melihat hasil pembersihan
        print("--- DEBUGGING PERBANDINGAN ---")
        print(f"Target dari Flutter (selected_pose): '{selected_pose}' -> Dibersihkan: '{clean_selected}'")
        print(f"Prediksi dari Model (predicted_class): '{predicted_class}' -> Dibersihkan: '{clean_predicted}'")
        print(f"Hasil Cocok? -> {is_match}")
        print("---------------------------------")
        # ==========================================================

        # Kirim respons yang dibutuhkan oleh Flutter
        emit("response", {
            "status": status,
            "pose_class": predicted_class, # Kirim nama asli dari model
            "prob": str(confidence),
        })

    except Exception as e:
        print(f"[ERROR] Terjadi kesalahan di handle_image: {e}")
        emit("response", {"status": "error", "message": str(e)})

def handle_reset_buffer(data):
    user_id = data.get("userId")
    if user_id in user_buffers:
        user_buffers[user_id].clear()
        print(f"[INFO] Buffer untuk user {user_id} telah direset.")
    emit("response", {"status": "buffer_reset", "message": "Buffer berhasil direset."})

# ================================
# D. REGISTER SOCKET EVENTS
# ================================
def register_socket_handlers(socketio_instance):
    print("[INFO] Mendaftarkan event Socket.IO...")
    socketio_instance.on_event("connect", handle_connect)
    socketio_instance.on_event("disconnect", handle_disconnected)
    socketio_instance.on_event("message", handle_message)
    socketio_instance.on_event("image", handle_image)
    socketio_instance.on_event("reset_buffer", handle_reset_buffer)

# Di file utama Anda (app.py atau __init__.py), Anda akan memanggil:
# from .services import socketio_services
# socketio_services.register_socket_handlers(socketio)