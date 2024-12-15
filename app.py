import streamlit as st
import os
import yt_dlp
from moviepy.editor import VideoFileClip

def download_youtube_video(url, output_path, quality_option):
    """
    Download a YouTube video using yt-dlp with quality selection
    """
    try:
        # Select format based on quality option
        if quality_option == "Highest Resolution":
            format_selector = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'
        elif quality_option == "Lowest Resolution":
            format_selector = 'worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]'
        else:  # Best Available
            format_selector = 'best[ext=mp4]'
        
        ydl_opts = {
            'format': format_selector,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'no_color': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'no_oversized_thumbnails': True,
            'progress_hooks': [download_progress],
            'cookiefile': 'cookies.txt',
        }
        
        class MyLogger:
            def debug(self, msg):
                pass
            def warning(self, msg):
                pass
            def error(self, msg):
                st.error(f"Download error: {msg}")
        
        ydl_opts['logger'] = MyLogger()
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video info
            info_dict = ydl.extract_info(url, download=True)
            
            if not info_dict:
                st.error("Could not extract video information.")
                return None
            
            # Get video title
            video_title = info_dict.get('title', 'downloaded_video')
            
            # Find the downloaded file
            for file in os.listdir(output_path):
                if video_title in file:
                    return os.path.join(output_path, file)
        
        st.error("Video download failed.")
        return None
    
    except Exception as e:
        st.error(f"Unexpected error downloading video: {e}")
        return None

def download_progress(d):
    """
    Progress hook for download
    """
    if d['status'] == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        if total > 0:
            percent = downloaded / total * 100
            st.progress(percent/100)

def trim_video(input_path, start_time, end_time, output_path):
    """
    Trim a video to specified start and end times
    """
    try:
        video = VideoFileClip(input_path)
        
        if start_time < 0 or end_time > video.duration or start_time >= end_time:
            st.error("Invalid trim times. Please check and retry.")
            video.close()
            return None
        
        trimmed_video = video.subclip(start_time, end_time)
        trimmed_video.write_videofile(output_path, logger=None)
        
        video.close()
        trimmed_video.close()
        
        return output_path
    except Exception as e:
        st.error(f"Error trimming video: {e}")
        return None

def read_file_bytes(file_path):
    """
    Read file as bytes for download
    """
    with open(file_path, 'rb') as file:
        return file.read()

def main():
    st.set_page_config(page_title="YouTube Video Downloader", page_icon=":movie_camera:")
    
    os.makedirs('/app/data/downloads', exist_ok=True)
    os.makedirs('/app/data/trimmed_videos', exist_ok=True)
    
    st.title("🎥 ClipCatch")
    
    # Video URL input
    video_url = st.text_input("Enter YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
    
    # Advanced options with quality selection
    with st.expander("Download Options"):
        download_quality = st.selectbox(
            "Video Quality", 
            ["Best Available", "Highest Resolution", "Lowest Resolution"],
            index=0  # Default to Best Available
        )
    
    # Download section
    if st.button("Download Video"):
        if video_url:
            try:
                with st.spinner("Downloading video..."):
                    # Pass the selected quality to the download function
                    downloaded_path = download_youtube_video(
                        video_url, 
                        '/app/data/downloads', 
                        download_quality
                    )
                    
                    if downloaded_path:
                        st.success("Video downloaded successfully!")
                        # st.info(f"Saved at: {downloaded_path}")
                        
                        # Download button for the original video
                        video_bytes = read_file_bytes(downloaded_path)
                        st.download_button(
                            label="Download Original Video",
                            data=video_bytes,
                            file_name=os.path.basename(downloaded_path),
                            mime='video/mp4'
                        )
            except Exception as e:
                st.error(f"Download failed: {e}")
    
    # Trimming section
    st.header("Trimming settings")
    
    # Get list of downloaded videos
    downloaded_videos = os.listdir('/app/data/downloads')
    
    if downloaded_videos:
        selected_video = st.selectbox("Select Video to Trim", downloaded_videos)
        
        if selected_video:
            # Input for start and end times
            col1, col2 = st.columns(2)
            with col1:
                start_time = st.number_input("Start Time (minutes)", min_value=0.0, step=1.0, value=0.0)
            with col2:
                video_path = os.path.join('/app/data/downloads', selected_video)
                video = VideoFileClip(video_path)
                max_duration = video.duration
                video.close()
                
                end_time = st.number_input(
                    "End Time (minutes)", 
                    min_value=0.0, 
                    max_value=max_duration, 
                    value=max_duration, 
                    step=1.0
                )
            
            if st.button("Trim Video"):
                with st.spinner("Trimming video..."):
                    output_filename = f"trimmed_{selected_video}"
                    trimmed_path = trim_video(
                        os.path.join('/app/data/downloads', selected_video), 
                        start_time*60, 
                        end_time*60, 
                        os.path.join('/app/data/trimmed_videos', output_filename)
                    )
                    
                    if trimmed_path:
                        st.success("Video trimmed successfully!")
                        # st.info(f"Saved at: {trimmed_path}")
                        
                        # Download button for the trimmed video
                        trimmed_bytes = read_file_bytes(trimmed_path)
                        st.download_button(
                            label="Download Trimmed Video",
                            data=trimmed_bytes,
                            file_name=os.path.basename(trimmed_path),
                            mime='video/mp4'
                        )
    else:
        st.warning("No videos downloaded yet. Please download a video first.")

if __name__ == "__main__":
    main()