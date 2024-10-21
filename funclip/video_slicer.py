import os
from pathlib import Path
import subprocess
import json
from PIL import Image
import logging
import shutil
from tqdm import tqdm
import concurrent.futures

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
        """
        清空输出目录，如果存在则删除并重新创建。
        """
        if self.output_dir.exists():
            try:
                shutil.rmtree(self.output_dir)
                self.logger.debug(f"清空输出目录: {self.output_dir}")
            except Exception as e:
                self.logger.error(f"无法清空输出目录: {self.output_dir}，错误: {e}")
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"重新创建输出目录: {self.output_dir}")
        except Exception as e:
            self.logger.error(f"无法创建输出目录: {self.output_dir}，错误: {e}")

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

    def get_video_resolution(self, video_path):
        """
        使用 ffprobe 获取视频的分辨率。

        :param video_path: 视频文件的路径。
        :return: (width, height) 分辨率元组。
        """
        command = [
            'ffprobe', 
            '-v', 'error', 
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'json', 
            str(video_path)
        ]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            info = json.loads(result.stdout)
            width = info['streams'][0]['width']
            height = info['streams'][0]['height']
            return width, height
        except Exception as e:
            self.logger.error(f"获取视频分辨率失败: {video_path}，错误: {e}")
            return None, None

    def get_video_duration(self, video_path):
        """
        使用 ffprobe 获取视频的时长。

        :param video_path: 视频文件的路径。
        :return: 时长（秒）。
        """
        command = [
            'ffprobe', 
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            duration = float(result.stdout.strip())
            return duration
        except Exception as e:
            self.logger.error(f"获取视频时长失败: {video_path}，错误: {e}")
            return None

    def get_timestamp_str(self, t):
        """
        将秒数转换为 HH_MM_SS 格式的字符串。

        :param t: 时间（秒）
        :return: 格式化的时间字符串
        """
        hours, remainder = divmod(int(t), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}_{minutes:02d}_{seconds:02d}"

    def extract_and_save_frame(self, video_path, timestamp, image_path):
        """
        使用 ffmpeg 提取指定时间点的帧并保存为图像。

        :param video_path: 视频文件的路径。
        :param timestamp: 时间戳（秒）。
        :param image_path: 保存图像的路径。
        """
        command = [
            'ffmpeg',
            '-ss', str(timestamp),
            '-i', str(video_path),
            '-frames:v', '1',
            '-q:v', '2',
            '-y',  # 自动覆盖输出文件
            str(image_path)
        ]
        try:
            # 执行命令
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            self.logger.debug(f"使用 ffmpeg 在 {timestamp}s 保存帧为 '{image_path.name}'")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"使用 ffmpeg 在 {timestamp}s 保存帧失败: {e.stderr}")

    def extract_and_save_frames(self, video_path, folder_path):
        """
        从视频中每隔指定间隔提取一帧，并保存到指定文件夹。

        :param video_path: 视频文件的路径 (Path 对象)。
        :param folder_path: 保存截图的文件夹路径 (Path 对象)。
        """
        width, height = self.get_video_resolution(video_path)
        if width is None or height is None:
            self.logger.error(f"无法获取视频分辨率，跳过视频: {video_path.name}")
            return

        self.logger.info(f"视频分辨率: {width}x{height}")

        duration = self.get_video_duration(video_path)
        if duration is None:
            self.logger.error(f"无法获取视频时长，跳过视频: {video_path.name}")
            return

        self.logger.info(f"处理视频 '{video_path.name}'：时长={duration:.2f}秒")

        # 生成时间点
        timestamps = list(range(0, int(duration) + 1, self.interval))
        if timestamps[-1] != int(duration):
            timestamps.append(int(duration))  # 确保包含视频结尾帧

        for t in timestamps:
            timestamp_str = self.get_timestamp_str(t)
            image_filename = f"{timestamp_str}.png"
            image_path = folder_path / image_filename

            self.extract_and_save_frame(video_path, t, image_path)

    def process_videos(self):
        """
        处理所有视频文件：为每个视频创建文件夹并提取截图，带有进度条和并行处理。
        """
        # 初始化步骤：清空输出目录
        self.clear_output_directory()

        # 使用 ThreadPoolExecutor 进行并行处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
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
                futures.append(executor.submit(self.extract_and_save_frames, video_path, folder_path))

            # 使用 tqdm 显示进度条
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing Videos"):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"并行处理时出错: {e}")

        self.logger.info("所有视频处理完成。")

# 示例调用
if __name__ == "__main__":
    # 示例：视频文件路径列表
    video_paths = [
        "C:/path/to/video1.mp4",
        "C:/path/to/video2.avi",
        "C:/path/to/video3.mov",
        # 添加更多视频文件路径
    ]

    # 基准输出目录
    output_dir = "C:/coffee_cut_temp/frames"

    # 创建 VideoSlicer 实例
    slicer = VideoSlicer(video_paths, output_dir, interval=3)

    # 处理所有视频
    slicer.process_videos()