# app.py

import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import av
from ultralytics import YOLO
import cv2

class YOLOVideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.model = YOLO('yolov8n.pt')  # Hoặc bạn thay bằng model custom của bạn
        self.conf = 0.3
        self.iou = 0.45

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        results = self.model(img, conf=self.conf, iou=self.iou)
        annotated_img = results[0].plot()
        return annotated_img

st.set_page_config(page_title="YOLO Real-time Detection", layout="wide")
st.title("🚀 YOLO Real-time Webcam Detection with Streamlit WebRTC")

st.sidebar.header("Configuration")
confidence = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.3, 0.01)
iou_threshold = st.sidebar.slider("IoU Threshold", 0.0, 1.0, 0.45, 0.01)

webrtc_streamer(
    key="yolo-realtime",
    video_processor_factory=lambda: YOLOVideoProcessor(),
    media_stream_constraints={
        "video": True,
        "audio": False
    },
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    }
)
