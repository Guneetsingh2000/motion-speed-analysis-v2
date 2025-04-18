import streamlit as st
import requests
import tempfile
import base64
from PIL import Image
from io import BytesIO
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8080")

st.set_page_config(page_title="Motion Tracker App", layout="wide")
st.title("🎥 Motion Tracker with FastAPI Backend")

video_file = st.file_uploader("Upload .mp4 file", type=["mp4"])
option = st.radio("Tracking Option", [1, 2, 3], format_func=lambda x: {
    1: "User-Selected Tracking", 
    2: "Auto Corner Detection", 
    3: "YOLO Demo (Simulated)"
}[x])

blur = st.slider("Blur", 1, 21, 5, step=2)
hist_eq = st.checkbox("Histogram Equalization", True)
canny = st.checkbox("Canny Edge Detection", False)

if video_file:
    st.video(video_file)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(video_file.read())
        video_path = tmp.name

    if st.button("Run Motion Analysis"):
        with open(video_path, "rb") as f:
            encoded_video = base64.b64encode(f.read()).decode("utf-8")
        payload = {
            "video_data": encoded_video,
            "option": option,
            "blur": blur,
            "hist_eq": hist_eq,
            "canny": canny
        }

        with st.spinner("Processing..."):
            res = requests.post(f"{BACKEND_URL}/process", json=payload)
            if res.status_code == 200:
                result = res.json()
                st.subheader("Motion Speed Results")
                st.write(f"Max Speed: {result['max_speed']:.2f}")
                st.write(f"Min Speed: {result['min_speed']:.2f}")
                st.write(f"Avg Speed: {result['avg_speed']:.2f}")
                frame = base64.b64decode(result["overlay_frame"])
                img = Image.open(BytesIO(frame))
                st.image(img, caption="Overlay Frame", use_container_width=True)
            else:
                st.error("Processing failed.")
