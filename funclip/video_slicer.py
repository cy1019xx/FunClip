import os
from pathlib import Path
from moviepy.editor import VideoFileClip
from PIL import Image
import logging

class VideoSlicer:
    def __init__(self, 
                 video_paths, 
                 output_dir="C:/coffee_cut_temp/frames", 
                 interval=3):
        """
        初始化 VideoSlicer 类。

        :param video_paths: 包含多个视频文件路径的列表。
        :param output_dir: 所有截图文件夹的基准目录。
        :param interval: 截取帧的时间间隔（秒），默认为3秒。
        """
        self.video_paths = [Path(path) for path in video_paths]
        self.output_dir = Path(output_dir)
        self.interval = interval
        self.setup_logging()

    def setup_logging(self):
        """
        配置日志记录。
        """
        self.logger = logging.getLogger('VideoSlicer')
        self.logger.setLevel(logging.DEBUG)

        # 清除已有的处理器
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 创建文件处理器
        file_handler = logging.FileHandler('video_slicer.log')
        file_handler.setLevel(logging.DEBUG)

        # 创建格式器并添加到处理器
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # 添加处理器到日志记录器
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def clear_output_directory(self):
        # 检查输出目录是否存在
        if os.path.exists(self.output_dir):
            # 删除目录下的所有文件
            import shutil  # 添加这一行以导入shutil模块
            shutil.rmtree(self.output_dir)
        # 重新创建输出目录
        os.makedirs(self.output_dir)
        
    def create_folder(self, folder_path):
        """
        创建文件夹，如果文件夹已存在，则不进行任何操作。

        :param folder_path: 要创建的文件夹路径。
        """
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"文件夹已创建或已存在: {folder_path}")
        except Exception as e:
            self.logger.error(f"创建文件夹失败: {folder_path}，错误: {e}")

    def extract_and_save_frames(self, video_path, folder_path):
        """
        从视频中每隔指定间隔提取一帧，并保存到指定文件夹。

        :param video_path: 视频文件的路径 (Path 对象)。
        :param folder_path: 保存截图的文件夹路径 (Path 对象)。
        """
        try:
            with VideoFileClip(str(video_path)) as clip:
                duration = int(clip.duration)
                self.logger.info(f"处理视频 '{video_path.name}'：时长={duration}秒")

                # 生成时间点
                timestamps = list(range(0, duration + 1, self.interval))
                if timestamps[-1] != duration:
                    timestamps.append(duration)  # 确保包含视频结尾帧

                for t in timestamps:
                    frame = clip.get_frame(t)
                    # 生成截图文件名，例如: 00_00_03.png
                    hours, remainder = divmod(t, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    timestamp_str = f"{int(hours):02d}_{int(minutes):02d}_{int(seconds):02d}"
                    image_filename = f"{timestamp_str}.png"
                    image_path = folder_path / image_filename

                    # 保存截图
                    img = Image.fromarray(frame)
                    img.save(image_path)
                    self.logger.debug(f"在 {t}s 保存帧为 '{image_filename}'")

        except Exception as e:
            self.logger.error(f"处理视频 '{video_path.name}' 失败：{e}")

    def process_videos(self):
        """
        处理所有视频文件：为每个视频创建文件夹并提取截图。
        """
        
        # 初始化步骤：清空输出目录
        self.clear_output_directory()

        for video_path in self.video_paths:
            if not video_path.is_file():
                self.logger.warning(f"视频文件不存在: {video_path}")
                continue

            # 获取视频文件名（不包含扩展名）作为文件夹名
            folder_name = video_path.stem
            folder_path = self.output_dir / folder_name
            self.create_folder(folder_path)

            self.logger.info(f"创建文件夹 '{folder_path}' 用于视频 '{video_path.name}'")

            # 提取并保存截图
            self.extract_and_save_frames(video_path, folder_path)

        self.logger.info("所有视频处理完成。")

# 示例调用
if __name__ == "__main__":
    # 示例：视频文件路径列表
    video_paths = [
        "/path/to/video1.mp4",
        "/path/to/video2.avi",
        "/path/to/video3.mov",
        # 添加更多视频文件路径
    ]

    # 基准输出目录
    output_dir = "C:/coffee_cut_temp/frames"

    # 创建 VideoSlicer 实例
    slicer = VideoSlicer(video_paths, output_dir, interval=3)

    # 处理所有视频
    slicer.process_videos()