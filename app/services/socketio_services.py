# run.py

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

from app import db, socketio
from flask_socketio import emit


# ================================
# A. Load Model & Label Encoder
# ================================


class PoseLSTM(nn.Module):
    def __init__(self, input_size=132, hidden_size=128, num_classes=12):
        super(PoseLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        return self.fc(h_n[-1])


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Path model & encoder
MODEL_PATH = "./model_weights/final_lstm_pose_model.pt"
ENCODER_PATH = "./model_weights/final_label_encoder.pkl"

# Load label encoder
with open(ENCODER_PATH, "rb") as f:
    label_encoder = pickle.load(f)

# Load model
num_classes = len(label_encoder.classes_)
model = PoseLSTM(num_classes=num_classes).to(DEVICE)
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model.eval()


# ================================
# B. MediaPipe Setup & Buffer
# ================================

mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
user_buffers = defaultdict(lambda: deque(maxlen=30))  # buffer per user


# ================================
# C. Socket.IO Handlers
# ================================


def handle_connect():
    print("Client connected")


def handle_disconnected():
    print("Client disconnected")


def handle_message(message):
    print("Received message:", message)


def handle_image(data):
    try:
        # Ambil data dari klien
        user_id = data.get("userId")
        selected_pose = data.get("selected_pose")
        image_data = data.get("image_data")

        if not all([user_id, selected_pose, image_data]):
            raise ValueError("Data tidak lengkap dari klien")

        # Decode base64
        image_bytes = base64.b64decode(image_data)
        np_image = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Jalankan MediaPipe
        with mp_holistic.Holistic(
            min_detection_confidence=0.5, min_tracking_confidence=0.5
        ) as holistic:
            results = holistic.process(image_rgb)
            image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

            # Gambar landmark
            mp_drawing.draw_landmarks(
                image_bgr,
                results.pose_landmarks,
                mp_holistic.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(
                    color=(71, 130, 141), thickness=2, circle_radius=4
                ),
                mp_drawing.DrawingSpec(
                    color=(255, 255, 255), thickness=5, circle_radius=2
                ),
            )

            pose_class = "none"
            pose_probabilities = [0.0] * num_classes

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                pose_row = np.array(
                    [[lmk.x, lmk.y, lmk.z, lmk.visibility] for lmk in landmarks]
                ).flatten()
                pose_row = np.clip(pose_row, 0.0, 1.0)

                buffer = user_buffers[user_id]
                buffer.append(pose_row)

                # Hanya jika buffer penuh
                if len(buffer) == 30:
                    input_seq = np.array(buffer)[np.newaxis, ...]  # (1, 30, 132)
                    input_tensor = torch.from_numpy(input_seq).float().to(DEVICE)

                    with torch.no_grad():
                        output = model(input_tensor)
                        probs = torch.nn.functional.softmax(output, dim=1)[0]
                        pred_index = torch.argmax(probs).item()

                        pose_class = label_encoder.inverse_transform([pred_index])[0]
                        pose_probabilities = probs.cpu().numpy().tolist()

            # Simpan ke DB jika sudah ada prediksi
            if pose_class != "none":
                user = db.db.users.find_one({"_id": ObjectId(user_id)})
                gender = user.get("gender", "unknown")
                status = "Sesuai" if pose_class == selected_pose else "Tidak Sesuai"

                db.db.detections.insert_one(
                    {
                        "userID": user_id,
                        "namaGerakan": selected_pose,
                        "keterangan": status,
                        "gender": gender,
                        "tanggal": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

            # Encode ulang gambar untuk dikirim ke frontend
            _, buffer_img = cv2.imencode(".jpg", image_bgr)
            encoded_image = base64.b64encode(buffer_img).decode("utf-8")

            emit(
                "response",
                {
                    "imageData": encoded_image,
                    "pose_class": pose_class,
                    "prob": str(float(np.max(pose_probabilities))),
                },
            )

    except Exception as e:
        print("Error in handle_image:", e)


# ================================
# D. Register Socket Events
# ================================

socketio.on_event("connect", handle_connect)
socketio.on_event("disconnect", handle_disconnected)
socketio.on_event("message", handle_message)
socketio.on_event("image", handle_image)
