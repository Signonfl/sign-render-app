{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import cv2\
import numpy as np\
from PIL import Image\
import io\
import tempfile\
import base64\
import json\
\
def load_image(image_file):\
    image = Image.open(image_file)\
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)\
\
def scale_sign(sign_img, real_sign_height_in, real_ref_height_in, ref_pixel_height):\
    scale_ratio = real_ref_height_in / ref_pixel_height  # inches per pixel\
    sign_height_px = int(real_sign_height_in / scale_ratio)\
    h, w = sign_img.shape[:2]\
    sign_width_px = int(sign_height_px * (w / h))\
    return cv2.resize(sign_img, (sign_width_px, sign_height_px))\
\
def overlay_sign(building_img, sign_img, x_offset, y_offset, alpha=1.0):\
    y1, y2 = y_offset, y_offset + sign_img.shape[0]\
    x1, x2 = x_offset, x_offset + sign_img.shape[1]\
    if y2 > building_img.shape[0] or x2 > building_img.shape[1]:\
        raise ValueError("Sign exceeds image bounds. Adjust position or size.")\
\
    overlay = building_img.copy()\
    roi = overlay[y1:y2, x1:x2]\
    blended = cv2.addWeighted(sign_img, alpha, roi, 1 - alpha, 0)\
    overlay[y1:y2, x1:x2] = blended\
    return overlay\
\
def convert_image_to_downloadable(image_array):\
    _, buffer = cv2.imencode('.png', image_array)\
    b64 = base64.b64encode(buffer).decode()\
    href = f'<a href="data:image/png;base64,\{b64\}" download="rendered_sign.png">Download Rendered Image</a>'\
    return href\
\
def detect_signable_area(building_img):\
    gray = cv2.cvtColor(building_img, cv2.COLOR_BGR2GRAY)\
    edges = cv2.Canny(gray, 50, 150)\
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)\
    if not contours:\
        return 0, 0\
    x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))\
    return x + w // 2, y + h // 2  # Center of the largest contour\
\
def main():\
    st.title("Scaled Signage Renderer")\
\
    building_file = st.file_uploader("Upload photo of building", type=["jpg", "jpeg", "png"])\
    sign_file = st.file_uploader("Upload a sign artwork (PNG with transparency preferred)", type=["png", "jpg", "jpeg"])\
\
    real_ref_height = st.number_input("Known real-world height of reference object (in inches)", min_value=1.0)\
    ref_pixel_height = st.number_input("Measured height of reference object in image (in pixels)", min_value=1)\
    sign_height = st.number_input("Desired real-world sign height (in inches)", min_value=1.0)\
\
    auto_detect_area = st.checkbox("Auto-detect and center on largest signable area")\
    snap_to_grid = st.checkbox("Snap to 10px grid")\
    alpha = st.slider("Sign opacity (0.0 = transparent, 1.0 = solid)", 0.0, 1.0, 1.0, 0.01)\
\
    preset_data = st.session_state.get("preset_data", None)\
    load_preset = st.button("Load Preset")\
    save_preset = st.button("Save Preset")\
\
    if "clicked_coords" not in st.session_state:\
        st.session_state.clicked_coords = (0, 0)\
\
    if building_file and sign_file:\
        building_img = load_image(building_file)\
        sign_img = load_image(sign_file)\
\
        scaled_sign = scale_sign(sign_img, sign_height, real_ref_height, ref_pixel_height)\
\
        if auto_detect_area:\
            cx, cy = detect_signable_area(building_img)\
            x_offset = cx - scaled_sign.shape[1] // 2\
            y_offset = cy - scaled_sign.shape[0] // 2\
        else:\
            click = st.image(building_img, caption="Click to place sign", use_column_width=True)\
            click_input = st.image(building_img, channels="RGB")\
            coord = st.experimental_get_query_params().get("click", [None])[0]\
            if coord:\
                cx, cy = map(int, coord.split(","))\
                st.session_state.clicked_coords = (cx, cy)\
            x_offset, y_offset = st.session_state.clicked_coords\
            if snap_to_grid:\
                x_offset -= x_offset % 10\
                y_offset -= y_offset % 10\
\
        if load_preset and preset_data:\
            x_offset, y_offset = preset_data["x"], preset_data["y"]\
\
        if save_preset:\
            st.session_state["preset_data"] = \{"x": x_offset, "y": y_offset\}\
\
        try:\
            result_img = overlay_sign(building_img, scaled_sign, x_offset, y_offset, alpha=alpha)\
            st.image(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB), caption="Rendered Sign Mockup", use_column_width=True)\
            st.markdown(convert_image_to_downloadable(result_img), unsafe_allow_html=True)\
            st.write(f"Placement: (\{x_offset\}, \{y_offset\}) | Sign size: \{scaled_sign.shape[1]\} x \{scaled_sign.shape[0]\} pixels")\
        except Exception as e:\
            st.error(f"Error: \{e\}")\
\
if __name__ == "__main__":\
    main()\
}