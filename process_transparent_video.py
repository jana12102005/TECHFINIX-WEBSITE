import os
import sys
import cv2
import torch
import numpy as np
from PIL import Image
from transparent_background import Remover
import imageio_ffmpeg
import subprocess

def process_video():
    input_path = os.path.abspath('app/static/videos/bounty_cinematic.mp4')
    output_path = os.path.abspath('app/static/videos/bounty_transparent.webm')
    
    print(f"Reading input video from: {input_path}")
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print("Error: Could not open input video!")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Video metadata: {width}x{height} @ {fps} FPS, Total Frames: {total_frames}")

    print("Initializing AI Transparent Background Remover (InSPyReNet)...")
    remover = Remover()

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    # FFmpeg command to read raw RGBA frames from stdin and encode to WebM VP9 with alpha transparency (yuva420p)
    ffmpeg_cmd = [
        ffmpeg_exe,
        '-y', # Overwrite output if exists
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{width}x{height}',
        '-pix_fmt', 'rgba',
        '-r', str(fps),
        '-i', '-', # Input from stdin pipe
        '-c:v', 'libvpx-vp9',
        '-pix_fmt', 'yuva420p',
        '-auto-alt-ref', '0', # Required for VP9 alpha in web browsers
        '-b:v', '2M',
        '-crf', '18',
        output_path
    ]

    print("Launching FFmpeg VP9 Alpha Pipe Process...")
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    frame_idx = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            
            # Process AI Alpha Matting
            out_pil = remover.process(pil_img) # Returns RGBA PIL Image
            rgba_bytes = out_pil.tobytes()
            
            # Pipe raw RGBA bytes into FFmpeg
            proc.stdin.write(rgba_bytes)
            
            frame_idx += 1
            if frame_idx % 10 == 0 or frame_idx == total_frames:
                percent = (frame_idx / total_frames) * 100
                print(f"Processed frame {frame_idx}/{total_frames} ({percent:.1f}%)")
                sys.stdout.flush()

    except Exception as e:
        print(f"Error during processing: {e}")
    finally:
        cap.release()
        if proc.stdin:
            proc.stdin.close()
        stderr_output = proc.stderr.read().decode('utf-8', errors='ignore')
        proc.wait()

    print(f"Video processing finished! Saved to: {output_path}")
    print(f"FFmpeg output log snippet:\n{stderr_output[-500:]}")

if __name__ == '__main__':
    process_video()
