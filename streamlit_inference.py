# 4. streamlit_inference.py
(Phần này mình copy đúng theo file bạn gửi, chỉ sửa đúng lỗi nhỏ về import os thiếu thôi)

# === streamlit_inference.py ===
import io
import os
from typing import Any

import cv2
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import av

from ultralytics import YOLO
from ultralytics.utils import LOGGER
from ultralytics.utils.checks import check_requirements
from ultralytics.utils.downloads import GITHUB_ASSETS_STEMS

import streamlit as st

PORT = os.getenv('PORT')
if PORT:
    st.set_option('server.port', int(PORT))
    st.set_option('server.address', '0.0.0.0')

class YOLOWebcamProcessor(VideoTransformerBase):
    def __init__(self, model, conf, iou, selected_ind, enable_trk):
        self.model = model
        self.conf = conf
        self.iou = iou
        self.selected_ind = selected_ind
        self.enable_trk = enable_trk

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        if self.enable_trk == "Yes":
            results = self.model.track(img, conf=self.conf, iou=self.iou, classes=self.selected_ind, persist=True)
        else:
            results = self.model(img, conf=self.conf, iou=self.iou, classes=self.selected_ind)
        img = results[0].plot()
        return img


class Inference:
    def __init__(self, **kwargs: Any):
        check_requirements("streamlit>=1.29.0")
        self.st = st
        self.source = None
        self.enable_trk = False
        self.conf = 0.25
        self.iou = 0.45
        self.org_frame = None
        self.ann_frame = None
        self.vid_file_name = None
        self.selected_ind = []
        self.model = None

        self.temp_dict = {"model": None, **kwargs}
        self.model_path = self.temp_dict.get("model")

        LOGGER.info(f"Ultralytics Solutions: ✅ {self.temp_dict}")

    def web_ui(self):
        menu_style_cfg = """<style>MainMenu {visibility: hidden;}</style>"""
        main_title_cfg = """<div><h1 style="color:#FF64DA; text-align:center; font-size:40px; margin-top:-50px;
        font-family: 'Archivo', sans-serif; margin-bottom:20px;">Ultralytics YOLO Streamlit Application</h1></div>"""
        sub_title_cfg = """<div><h4 style="color:#042AFF; text-align:center; font-family: 'Archivo', sans-serif; 
        margin-top:-15px; margin-bottom:50px;">Experience real-time object detection on your webcam with the power 
        of Ultralytics YOLO! 🚀</h4></div>"""

        self.st.set_page_config(page_title="Ultralytics Streamlit App", layout="wide")
        self.st.markdown(menu_style_cfg, unsafe_allow_html=True)
        self.st.markdown(main_title_cfg, unsafe_allow_html=True)
        self.st.markdown(sub_title_cfg, unsafe_allow_html=True)

    def sidebar(self):
        with self.st.sidebar:
            logo = "https://raw.githubusercontent.com/ultralytics/assets/main/logo/Ultralytics_Logotype_Original.svg"
            self.st.image(logo, width=250)

        self.st.sidebar.title("User Configuration")
        self.source = self.st.sidebar.selectbox("Video", ("webcam", "video"))
        self.enable_trk = self.st.sidebar.radio("Enable Tracking", ("Yes", "No"))
        self.conf = float(self.st.sidebar.slider("Confidence Threshold", 0.0, 1.0, self.conf, 0.01))
        self.iou = float(self.st.sidebar.slider("IoU Threshold", 0.0, 1.0, self.iou, 0.01))

        col1, col2 = self.st.columns(2)
        self.org_frame = col1.empty()
        self.ann_frame = col2.empty()

    def source_upload(self):
        self.vid_file_name = ""
        if self.source == "video":
            vid_file = self.st.sidebar.file_uploader("Upload Video File", type=["mp4", "mov", "avi", "mkv"])
            if vid_file is not None:
                g = io.BytesIO(vid_file.read())
                with open("uploaded_video.mp4", "wb") as out:
                    out.write(g.read())
                self.vid_file_name = "uploaded_video.mp4"
        elif self.source == "webcam":
            self.vid_file_name = 0

    def configure(self):
        available_models = [x.replace("yolo", "YOLO") for x in GITHUB_ASSETS_STEMS if x.startswith("yolo11")]
        if self.model_path:
            available_models.insert(0, self.model_path.split(".pt")[0])
        selected_model = self.st.sidebar.selectbox("Model", available_models)

        with self.st.spinner("Model is downloading..."):
            self.model = YOLO(f"{selected_model.lower()}.pt")
            class_names = list(self.model.names.values())
        self.st.success("Model loaded successfully!")

        selected_classes = self.st.sidebar.multiselect("Classes", class_names, default=class_names[:3])
        self.selected_ind = [class_names.index(option) for option in selected_classes]
        if not isinstance(self.selected_ind, list):
            self.selected_ind = list(self.selected_ind)

    def inference(self):
        self.web_ui()
        self.sidebar()
        self.source_upload()
        self.configure()

        if self.st.sidebar.button("Start"):
            stop_button = self.st.button("Stop")

            if self.source == "webcam":
                self.st.info("Using Webcam via Streamlit WebRTC")
                webrtc_streamer(
                    key="realtime",
                    video_processor_factory=lambda: YOLOWebcamProcessor(
                        model=self.model,
                        conf=self.conf,
                        iou=self.iou,
                        selected_ind=self.selected_ind,
                        enable_trk=self.enable_trk
                    ),
                    media_stream_constraints={"video": True, "audio": False},
                    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
                )

            else:
                cap = cv2.VideoCapture(self.vid_file_name)
                if not cap.isOpened():
                    self.st.error("Could not open video source.")
                    return

                while cap.isOpened():
                    success, frame = cap.read()
                    if not success:
                        self.st.warning("Failed to read frame from video.")
                        break

                    if self.enable_trk == "Yes":
                        results = self.model.track(frame, conf=self.conf, iou=self.iou, classes=self.selected_ind, persist=True)
                    else:
                        results = self.model(frame, conf=self.conf, iou=self.iou, classes=self.selected_ind)

                    annotated_frame = results[0].plot()

                    if stop_button:
                        cap.release()
                        self.st.stop()

                    self.org_frame.image(frame, channels="BGR")
                    self.ann_frame.image(annotated_frame, channels="BGR")

                cap.release()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    import sys
    args = len(sys.argv)
    model = sys.argv[1] if args > 1 else None
    Inference(model=model).inference()
