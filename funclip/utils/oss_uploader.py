import os
import uuid
from io import BytesIO
from typing import BinaryIO

import oss2
from PIL import Image
from dotenv import load_dotenv

load_dotenv()


class OSSUploader:
    def __init__(self, access_key_id=os.getenv('OSS2_ACCESS_KEY_ID'),
                 access_key_secret=os.getenv('OSS2_ACCESS_KEY_SECRET'),
                 endpoint='https://oss-cn-chengdu.aliyuncs.com',
                 bucket_name=os.getenv('OSS2_BUCKET_NAME')):
        """
        初始化OSSUploader类。

        :param access_key_id: OSS访问密钥ID，默认值为 'DEFAULT_ACCESS_KEY_ID'
        :param access_key_secret: OSS访问密钥Secret，默认值为 'DEFAULT_ACCESS_KEY_SECRET'
        :param endpoint: OSS服务端点，默认值为 'DEFAULT_OSS_ENDPOINT'
        :param bucket_name: OSS存储桶名称，默认值为 'DEFAULT_BUCKET_NAME'
        """
        auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(auth, endpoint, bucket_name)

    def upload_jpg(self, img_obj: BinaryIO, object_name=None):
        """
        上传本地文件到OSS，并返回文件的签名URL。

        :param img_obj:

        :param object_name: OSS上的对象名称
        :return: 文件的签名URL
        """
        if not object_name:
            object_name = f"{uuid.uuid4()}.jpeg"
        try:
            # 上传文件到OSS
            self.bucket.put_object(object_name, img_obj)
            # 生成签名URL
            url = self.bucket.sign_url('GET', object_name, 3600, slash_safe=True)
            return url
        except Exception as e:
            print(f"上传失败: {e}")
            return None


# 示例使用
if __name__ == '__main__':
    current_working_directory = os.getcwd()


    # 在本地构造一个全是红色的jpg图片
    image = Image.new('RGB', (1000, 1000), (0, 255, 0))
    image.save('local_file.jpg')
    # 上传文件
    with open('local_file.jpg', 'rb') as img_obj:
        # 创建OSSUploader实例，使用默认参数
        uploader = OSSUploader()
        url = uploader.upload_jpg(img_obj)

        print(' URL的地址为：', url) 
