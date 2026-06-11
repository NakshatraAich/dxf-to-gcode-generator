import gradio as gr
import os
import socket
import matplotlib.pyplot as plt
from dxf_tool import (
    extract_dxf_segments,
    interpolate_segments,
    rotate_points,
    mirror as apply_mirror,
    shift_to_origin,
    generate_gcode
)

def parse_origin(text):
    try:
        x, y = map(float, text.split(","))
        return (x, y)
    except:
        return (0, 0)

def plot_interpolated_points(points):
    xs, ys = zip(*points)
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot(xs, ys, 'ro', markersize=2, label="Interpolated Points")
    ax.plot(xs[0], ys[0], 'go', markersize=8, label="Start Point")
    ax.set_aspect('equal')
    ax.grid(True)
    ax.set_title("Interpolated DXF Geometry")
    ax.legend()
    return fig

def handle_dxf(file, point_skip, rotate_angle, set_mirror, set_origin, origin_text):
    safe_name = "uploaded.dxf"
    file_path = os.path.join("uploads", safe_name)
    os.makedirs("uploads", exist_ok=True)

    with open(file_path, "wb") as f_out:
        f_out.write(file)

    segments = extract_dxf_segments(file_path)
    interpolated = interpolate_segments(segments, step=0.5)[::int(point_skip)]

    interpolated = rotate_points(interpolated, rotate_angle)
    if set_mirror:
        interpolated = apply_mirror(interpolated)
    if set_origin:
        origin = parse_origin(origin_text)
        interpolated = shift_to_origin(interpolated, origin)
    else:
        origin = (0, 0)

    fig = plot_interpolated_points(interpolated)
    gcode = generate_gcode(interpolated)

    text_info = (
        f"Uploaded: {safe_name}\n"
        f"Segments: {len(segments)}\n"
        f"Interpolated Points: {len(interpolated)}\n"
        f"Rotate: {rotate_angle}°, Mirror: {set_mirror}, "
        f"Origin Shift: {origin if set_origin else 'Not Set'}"
    )

    return text_info, fig, gcode

# ============ Gradio UI Layout ============
with gr.Blocks(title="DXF Upload and Transform") as demo:
    gr.Markdown("## DXF Upload and Transform")

    with gr.Row():
        file = gr.File(file_types=[".dxf"], type="binary", label="Upload DXF File")
        point_skip = gr.Number(label="Point Skip (e.g. 2 = every 2nd point)", value=1)
        rotate_angle = gr.Number(label="Rotate Angle (degrees)", value=0)

    with gr.Row():
        set_mirror = gr.Checkbox(label="Mirror Horizontally", value=False)
        set_origin = gr.Checkbox(label="Set New Origin", value=False)
        origin_text = gr.Textbox(label="New Origin (x, y)", value="0, 0")

    submit_btn = gr.Button("Process DXF")

    info_out = gr.Textbox(label="Processing Info", lines=4)
    plot_out = gr.Plot(label="Interpolated DXF Plot")
    gcode_out = gr.Textbox(label="GCode", lines=10)

    copy_btn = gr.Button("Copy GCode")

    submit_btn.click(
        fn=handle_dxf,
        inputs=[file, point_skip, rotate_angle, set_mirror, set_origin, origin_text],
        outputs=[info_out, plot_out, gcode_out]
    )

    # Re-triggers the textbox so user can easily Ctrl+C
    copy_btn.click(lambda g: g, inputs=gcode_out, outputs=gcode_out)

# ============ LAN Launch ============
try:
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"🌐 Access the app from your browser at: http://{local_ip}:7860")
except:
    print("Could not determine local IP. App will still launch.")

demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
