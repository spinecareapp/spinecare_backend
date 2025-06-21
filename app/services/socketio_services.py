from app import db
import cv2
import numpy as np
import pandas as pd
import mediapipe as mp
import pickle
import base64
from bson import ObjectId
from datetime import datetime
from app import socketio  # ✅
from flask_socketio import emit  # ✅ langsung dari modul aslinya


def handle_connect():
    print("Client connected")


def handle_disconnected():
    print("Client disconnected")


def handle_message(message):
    print("Received message:", message)


# Load model
with open("./model_weights/randomforest.pkl", "rb") as f:
    model = pickle.load(f)

# Mediapipe
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils


def handle_image(data):
    try:
        tanggal = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

        image_data = data.get("image_data")
        user_id = data.get("userId")
        selected_pose = data.get("selected_pose")

        body_language_prob = 0.0
        body_language_class = "none"
        image_data_bytes = base64.b64decode(image_data)
        image_array = np.frombuffer(image_data_bytes, dtype=np.uint8)
        decoded_image = cv2.imdecode(image_array, cv2.IMREAD_UNCHANGED)

        with mp_holistic.Holistic(
            min_detection_confidence=0.5, min_tracking_confidence=0.5
        ) as holistic:
            image = cv2.cvtColor(decoded_image, cv2.COLOR_BGR2RGB)
            image = cv2.resize(image, (680, 360), interpolation=cv2.INTER_LINEAR)

            # Make Detections
            results = holistic.process(image)
            print("Detection results obtained")

            # Recolor image back to BGR for rendering
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

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

            try:
                if results.pose_landmarks is not None:
                    # Extract Pose landmarks
                    pose = results.pose_landmarks.landmark
                    pose_row = list(
                        np.array(
                            [
                                [
                                    landmark.x,
                                    landmark.y,
                                    landmark.z,
                                    landmark.visibility,
                                ]
                                for landmark in pose
                            ]
                        ).flatten()
                    )

                    # Concatenate rows
                    row = pose_row

                    # Make Detections
                    X = pd.DataFrame([row])
                    body_language_class = model.predict(X)[0]
                    body_language_prob = model.predict_proba(X)[0]

                    if body_language_class == selected_pose:
                        status = "Sesuai"
                    else:
                        status = "Tidak Sesuai"

                    print(
                        f"ID user: {user_id}, class: {body_language_class}, prob: {body_language_prob}"
                    )

                    user = db.db.users.find_one({"_id": ObjectId(user_id)})
                    gender = user["gender"]

                    userFrame = {
                        "userID": user_id,
                        "namaGerakan": selected_pose,
                        "keterangan": status,
                        "gender": gender,
                        "tanggal": tanggal,
                    }

                    db.db.detections.insert_one(userFrame)
                else:
                    print("No pose landmarks detected")

            except Exception as e:
                print("Error during prediction:", e)

        processed_image_bytes = cv2.imencode(".jpg", image)[1].tobytes()
        processed_image_data = base64.b64encode(processed_image_bytes).decode("utf-8")
        prob_float = float(np.max(body_language_prob))
        prob = str(prob_float)

        emit(
            "response",
            {
                "imageData": processed_image_data,
                "pose_class": body_language_class,
                "prob": prob,
            },
        )

    except Exception as e:
        print("Error processing image:", e)
