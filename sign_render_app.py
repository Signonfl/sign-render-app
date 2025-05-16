
import streamlit as st
import numpy as np
from PIL import Image
import io
import base64
import json

def load_image(image_file):
    return Image.open(image_file).convert("RGBA")

def scale_sign(sign_img, real_sign_height_in, real_ref_height_in, ref_pixel_height):
    scale_ratio = real_ref_height_in / ref_pixel_height  # inches per pixel
    sign_height_px = int(real_sign_height_in / scale_ratio)
    w, h = sign_img.size
    sign_width_px = int(sign_height_px * (w / h))
    return sign_img.resize((sign_width_px, sign_height_px))

def overlay_sign(building_img, sign_img, x_offset, y_offset, alpha=1.0):
    building_img = building_img.convert("RGBA")
    sign_img = sign_img.convert("RGBA")

    if alpha < 1.0:
        alpha_mask = sign_img.split()[3].point(lambda p: int(p * alpha))
        sign_img.putalpha(alpha_mask)

    result = Image.new("RGBA", building_img.size)
    result.paste(building_img, (0, 0))
    result.paste(sign_img, (x_offset, y_offset), sign_img)
    return result.convert("RGB")

def convert_image_to_downloadable(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    b64 = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="rendered_sign.png">Download Rendered Image</a>'
    return href

def main():
    st.title("Scaled Signage Renderer")

    building_file = st.file_uploader("Upload photo of building", type=["jpg", "jpeg", "png"])
    sign_file = st.file_uploader("Upload a sign artwork (PNG with transparency preferred)", type=["png", "jpg", "jpeg"])

    real_ref_height = st.number_input("Known real-world height of reference object (in inches)", min_value=1.0)
    ref_pixel_height = st.number_input("Measured height of reference object in image (in pixels)", min_value=1)
    sign_height = st.number_input("Desired real-world sign height (in inches)", min_value=1.0)

    alpha = st.slider("Sign opacity (0.0 = transparent, 1.0 = solid)", 0.0, 1.0, 1.0, 0.01)

    if building_file and sign_file:
        building_img = load_image(building_file)
        sign_img = load_image(sign_file)

        try:
            scaled_sign = scale_sign(sign_img, sign_height, real_ref_height, ref_pixel_height)

            max_x = max(0, building_img.size[0] - scaled_sign.size[0])
            max_y = max(0, building_img.size[1] - scaled_sign.size[1])

            x_offset = st.slider("X offset", 0, max_x, 0)
            y_offset = st.slider("Y offset", 0, max_y, 0)

            result_img = overlay_sign(building_img, scaled_sign, x_offset, y_offset, alpha=alpha)
            st.image(result_img, caption="Rendered Sign Mockup", use_column_width=True)
            st.markdown(convert_image_to_downloadable(result_img), unsafe_allow_html=True)
            st.write(f"Placement: ({x_offset}, {y_offset}) | Sign size: {scaled_sign.size[0]} x {scaled_sign.size[1]} pixels")
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
