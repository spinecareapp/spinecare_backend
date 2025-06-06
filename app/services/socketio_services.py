# run.py
from app import db
import cv2
import numpy as np
import mediapipe as mp
import torch
import torch.nn as nn
import pickle
from collections import deque, defaultdict
import base64
from bson import ObjectId
from datetime import datetime
from app import socketio
from flask_socketio import emit


# ================================================
# STEP A: Load PyTorch LSTM Model + Label Encoder
# ================================================
class PoseLSTM(nn.Module):
    def __init__(self, input_size=132, hidden_size=128, num_classes=12):
        super(PoseLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        out = self.fc(h_n[-1])
        return out


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Ganti path berikut sesuai struktur folder Anda
MODEL_WEIGHTS_PATH = "./model_weights/final_lstm_pose_model.pt"
LABEL_ENCODER_PATH = "./model_weights/final_label_encoder.pkl"

# Muat label encoder
with open(LABEL_ENCODER_PATH, "rb") as f:
    label_encoder = pickle.load(f)

# Inisialisasi model dan load bobot
num_classes = len(label_encoder.classes_)
lstm_model = PoseLSTM(input_size=132, hidden_size=128, num_classes=num_classes).to(
    DEVICE
)
lstm_model.load_state_dict(torch.load(MODEL_WEIGHTS_PATH, map_location=DEVICE))
lstm_model.eval()

# =====================================================
# STEP B: Siapkan MediaPipe dan Buffer Per-User (Deque)
# =====================================================
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils

# Kita akan menyimpan satu deque (buffer) untuk setiap user_id.
# Deque berisi baris pose (132-dimensi) sampai mencapai 30 frame
# agar bisa dipakai LSTM.
user_sequences = defaultdict(lambda: deque(maxlen=30))

# =====================================================
# STEP C: Handler Socket.IO
# =====================================================


def handle_connect():
    print("Client connected")


def handle_disconnected():
    print("Client disconnected")


def handle_message(message):
    print("Received message:", message)


# Fungsi utama untuk memproses frame yang masuk
def handle_image(data):
    try:
        tanggal = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        image_data = data.get("image_data")
        user_id = data.get("userId")
        selected_pose = data.get("selected_pose")  # pose yang diharapkan

        # --- Decode base64 image dari klien ---
        image_data_bytes = base64.b64decode(image_data)
        image_array = np.frombuffer(image_data_bytes, dtype=np.uint8)
        decoded_image = cv2.imdecode(image_array, cv2.IMREAD_UNCHANGED)

        # Resize / (opsional) bisa disesuaikan
        # Misal: kita pertahankan resolusi asli, atau sekali resize:
        image = cv2.cvtColor(decoded_image, cv2.COLOR_BGR2RGB)
        # (Jika perlu resize, misalnya jadi 680x360:)
        # image = cv2.resize(image, (680, 360), interpolation=cv2.INTER_LINEAR)

        with mp_holistic.Holistic(
            min_detection_confidence=0.5, min_tracking_confidence=0.5
        ) as holistic:
            # --- Jalankan deteksi pose ---
            results = holistic.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Gambar landmark untuk feedback visual
            mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                mp_holistic.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(
                    color=(71, 130, 141), thickness=2, circle_radius=4
                ),
                mp_drawing.DrawingSpec(
                    color=(255, 255, 255), thickness=5, circle_radius=2
                ),
            )

            body_language_class = "none"
            body_language_prob = [0.0] * num_classes  # default

            if results.pose_landmarks is not None:
                # Ekstraksi 33 landmark × 4 (x,y,z,visibility) → total 132 dimensi
                pose = results.pose_landmarks.landmark
                pose_row = np.array(
                    [[lmk.x, lmk.y, lmk.z, lmk.visibility] for lmk in pose]
                ).flatten()
                # Pastikan semua nilai di‐clip [0,1] (opsional)
                pose_row = np.clip(pose_row, 0.0, 1.0)

                # Masukkan ke deque milik user_id ini
                seq_deque = user_sequences[user_id]
                seq_deque.append(pose_row)

                # Hanya saat deque sudah penuh (30 frame), kita inferensi LSTM
                if len(seq_deque) == 30:
                    # Bentuk tensor: (1, 30, 132)
                    seq_np = np.array(seq_deque)  # shape = (30, 132)
                    input_tensor = (
                        torch.from_numpy(seq_np[np.newaxis, ...]).float().to(DEVICE)
                    )

                    with torch.no_grad():
                        outputs = lstm_model(input_tensor)  # (1, num_classes)
                        probs = torch.nn.functional.softmax(outputs, dim=1)[
                            0
                        ]  # (num_classes,)
                        predicted_idx = torch.argmax(probs).item()
                        body_language_class = label_encoder.inverse_transform(
                            [predicted_idx]
                        )[0]
                        body_language_prob = probs.cpu().numpy().tolist()

                    # Jika Anda ingin sliding window (bukan clear buffer),
                    # deque sudah otomatis slide (maxlen=30). Berikutnya
                    # frame akan memasukkan indeks ke-31, dan frame ke-1
                    # otomatis ter-pop dari kiri. Jadi Anda tidak perlu
                    # mengosongkan deque.

                    # Jika ingin hanya sekali prediksi lalu clear:
                    # seq_deque.clear()

                # Jika results.pose_landmarks ada tapi deque belum sampai 30,
                # body_language_class tetap "none" atau bisa kirimkan status "menunggu buffer".

            # Insert ke database jika ingin:
            # (misalnya hanya simpan ketika sudah prediksi, atau selalu)
            if body_language_class != "none":
                # Ambil data user dari MongoDB
                user = db.db.users.find_one({"_id": ObjectId(user_id)})
                gender = user.get("gender", "unknown")

                status = (
                    "Sesuai" if body_language_class == selected_pose else "Tidak Sesuai"
                )

                userFrame = {
                    "userID": user_id,
                    "namaGerakan": selected_pose,
                    "keterangan": status,
                    "gender": gender,
                    "tanggal": tanggal,
                }
                db.db.detections.insert_one(userFrame)

            # Encode kembali gambar hasil anotasi menjadi base64
            processed_image_bytes = cv2.imencode(".jpg", image)[1].tobytes()
            processed_image_data = base64.b64encode(processed_image_bytes).decode(
                "utf-8"
            )

            # Kirimkan response via SocketIO
            # Ambil probabilitas tertinggi sebagai float
            max_prob = (
                float(np.max(body_language_prob))
                if len(body_language_prob) > 0
                else 0.0
            )
            emit(
                "response",
                {
                    "imageData": processed_image_data,
                    "pose_class": body_language_class,
                    "prob": str(max_prob),
                },
            )

    except Exception as e:
        print("Error processing image:", e)


# =====================================================
# STEP D: Daftarkan Handler ke Socket.IO
# =====================================================
socketio.on_event("connect", handle_connect)
socketio.on_event("disconnect", handle_disconnected)
socketio.on_event("message", handle_message)
socketio.on_event("image", handle_image)
