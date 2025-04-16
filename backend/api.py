from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import base64
import cv2
import numpy as np

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoData(BaseModel):
    video_data: str
    every_nth: int = 5
    blur_ksize: int = 5
    hist_eq: bool = True
    frame_diff: bool = True
    threshold: int = 20
    learning_rate: float = 0.01
    morph: bool = False
    pyr_scale: float = 0.5
    levels: int = 3
    winsize: int = 15
    iterations: int = 3
    poly_n: int = 5
    poly_sigma: float = 1.2

@app.post("/process")
async def process_video(data: VideoData):
    # Decode video
    nparr = np.frombuffer(base64.b64decode(data.video_data), np.uint8)
    with open("temp_video.mp4", "wb") as f:
        f.write(nparr)

    cap = cv2.VideoCapture("temp_video.mp4")
    fps = cap.get(cv2.CAP_PROP_FPS)
    i = 0
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if i % data.every_nth == 0:
            frames.append(frame)
        i += 1
    cap.release()

    # Preprocessing
    processed, prev_gray = [], None
    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (data.blur_ksize, data.blur_ksize), 0)
        if data.hist_eq:
            gray = cv2.equalizeHist(gray)
        if data.frame_diff and prev_gray is not None:
            gray = cv2.absdiff(prev_gray, gray)
        processed.append(gray)
        prev_gray = gray

    # Background Subtraction
    subtractor = cv2.createBackgroundSubtractorMOG2()
    masks = []
    for frame in processed:
        mask = subtractor.apply(frame, learningRate=data.learning_rate)
        _, mask = cv2.threshold(mask, data.threshold, 255, cv2.THRESH_BINARY)
        if data.morph:
            mask = cv2.erode(mask, None, iterations=1)
            mask = cv2.dilate(mask, None, iterations=2)
        masks.append(mask)

    # Optical Flow Calculation
    speeds = []
    for i in range(1, len(processed)):
        flow = cv2.calcOpticalFlowFarneback(
            processed[i - 1], processed[i], None,
            pyr_scale=data.pyr_scale,
            levels=data.levels,
            winsize=data.winsize,
            iterations=data.iterations,
            poly_n=data.poly_n,
            poly_sigma=data.poly_sigma,
            flags=0
        )
        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        mag_masked = cv2.bitwise_and(mag, mag, mask=masks[i])
        speeds.append(mag_masked)

    # Visualization
    final_index = min(len(frames)-1, len(speeds))
    last_frame = frames[final_index]
    last_mag = speeds[-1] if speeds else np.zeros_like(processed[0])
    heatmap = cv2.applyColorMap(cv2.convertScaleAbs(last_mag, alpha=10), cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(last_frame, 0.6, heatmap, 0.4, 0)

    _, buffer = cv2.imencode(".jpg", overlay)
    img_b64 = base64.b64encode(buffer).decode("utf-8")
    flat = [s[s > 0].flatten() for s in speeds if s is not None]
    all_speed = np.concatenate(flat) if flat else np.array([0])

    return JSONResponse(content={
        "max_speed": float(np.max(all_speed)),
        "min_speed": float(np.min(all_speed)),
        "avg_speed": float(np.mean(all_speed)),
        "frame": img_b64
    })

