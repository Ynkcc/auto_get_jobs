from pdf2image import convert_from_path

# PDF文件路径
pdf_path = "user_requirements.pdf"

# 将PDF转换为图片
images = convert_from_path(pdf_path)

# 保存每一页为图片
for i, image in enumerate(images):
    image.save(f"page_{i + 1}.png", "PNG")
