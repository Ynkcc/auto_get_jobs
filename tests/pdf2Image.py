from pdf2image import convert_from_path
from PIL import Image

"""
可以将pdf简历转成图片，可用于投递图片简历
"""

# sudo apt-get install poppler-utils
# images = convert_from_path("resume.pdf",poppler_path=r"D:\Desktop\poppler-24.08.0\Library\bin")
# windows可以手动下载二进制文件添加到path 或者手动指定路径

# 转换PDF为图片对象列表
images_1 = convert_from_path("resume.pdf")
images_2 =convert_from_path("面试用.pdf")
images =images_1 + images_2
print(len(images))
# 计算总高度和最大宽度
total_height = sum(img.height for img in images)
max_width = max(img.width for img in images)

# 创建空白画布
combined_img = Image.new('RGB', (max_width, total_height))

# 垂直拼接图片
y_offset = 0
for img in images:
    combined_img.paste(img, (0, y_offset))
    y_offset += img.height  # 更新粘贴位置

# 保存结果
combined_img.save("resume.png")

