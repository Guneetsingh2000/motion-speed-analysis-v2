import streamlit as st
import requests
import tempfile
import base64
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="Motion Tracker App", layout="wide")
st.title("🎥 Motion Tracker with FastAPI Backend")

video_file = st.file_uploader("Upload .mp4 file", type=["mp4"])
if video_file:
    st.video(video_file)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(video_file.read())
        video_path = tmp.name

    if st.button("Run Motion Analysis"):
        with open(video_path, "rb") as f:
            encoded_video = base64.b64encode(f.read()).decode("utf-8")
        payload = {"video_data": encoded_video}

        with st.spinner("Processing..."):
            res = requests.post("http://localhost:8000/process", json=payload)
            if res.status_code == 200:
                result = res.json()
                st.subheader("Motion Speed Results")
                st.write(f"Max Speed: {result['max_speed']:.2f}")
                st.write(f"Min Speed: {result['min_speed']:.2f}")
                st.write(f"Avg Speed: {result['avg_speed']:.2f}")
                frame = base64.b64decode(result["frame"])
                img = Image.open(BytesIO(frame))
                st.image(img, caption="Overlay Frame", use_column_width=True)
            else:
                st.error("Processing failed.")
