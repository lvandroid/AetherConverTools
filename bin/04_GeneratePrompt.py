import base64
import os.path
import subprocess

from io import BytesIO
import requests
from PIL import Image

# 定义本机的SD网址
url = 'http://127.0.0.1:7860'
ex_url = url + "/tagger/v1/interrogate"
headers = {
    'accept': 'application'
}
proxy_server = 'http://127.0.0.1:7890'
proxies = {
    'http': proxy_server,
    'https': proxy_server
}
requests.post(f'{url}/tagger/v1/interrogate', headers=headers)


# 定义WD模型接口
def listwd():
    wd_list = requests.get(f"{url}/tagger/v1/interrogators").json()
    return wd_list


# 定义输入文件夹
folder_path = os.path.dirname(os.getcwd())
frame_path = os.path.join(folder_path, "video_frame_w")


# 定义获取WdTagger模型函数
def get_WDmap():
    WD_model = {}
    num = 0
    data = listwd()['models']
    for i in data:
        WD_model[num] = i
        print(str(num) + ". ", i)
        num += 1
    Choice = int(input("请选择WD模型编号："))
    print("选择的是", WD_model[Choice], "缺少的模型会自动下载")
    return WD_model[Choice]


# 定义wd14的参数
model = get_WDmap()
threshold = 0.5


# 定义图片转base64的函数
def img_str(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


# 轮询目录开始输出
frame_files = [f for f in os.listdir(frame_path) if f.endswith(".png")]

if len(frame_files) == 0:
    print(f"裁切后图片目录中没有任何图片，请检查{frame_path}目录后重试。")
    quit()

for frame in frame_files:
    response = ''
    caption_dict = {}
    sorted_items = []
    frame_file = os.path.join(frame_path, frame)
    img = img_str(Image.open(frame_file))

    with open(frame_file, 'rb') as file:
        image_data = file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
    # 构建请求体的JSON数据
    data = {
        "image": base64_image,
        "model": model,
        "threshold": threshold
    }

    # 请求接口返回内容
    response = requests.post(ex_url, json=data)

    # 检查响应状态码
    if response.status_code == 200:
        # 处理返回的JSON数据
        caption_dict = response.json()['caption']
        sorted_items = sorted([(k, v) for k, v in caption_dict.items() if float(v) > threshold], key=lambda x: x[1])
        txt = ','.join([f'{k}' for k, v in sorted_items])
        # 创建提示词txt文件
        txt_file = os.path.join(frame_path, f'{os.path.splitext(frame_file)[0]}.txt')
        with open(txt_file, 'w', encoding='utf-8') as tags:
            tags.write(txt)
        print(f'{frame}的提示词反推完成， 提取{len(sorted_items)}个tag')
    else:
        print('错误：', response.status_code)
        print('返回内容：', response.text)

# 是否进行下一步
choice = input("\n是否直接开始下一步，进行批量图生图？需要启动API后启动SD，详细配置请打开[05_BatchImg2Img]文件手动调整\n1. 是\n2. 否\n请输入你的选择：")
if choice == "1":
    subprocess.run(['python', '05_BatchImg2Img.py'])
else:
    quit()