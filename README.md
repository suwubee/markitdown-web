# MarkItDown Web

这是一个基于Streamlit的Web应用，利用Microsoft的MarkItDown库将各种文件格式转换为Markdown。

## 功能特点

- 支持多种文件格式转换：PDF、Word、PowerPoint、Excel、图片等
- 支持OCR文字识别功能，可以从图片和PDF中提取文本
- 支持使用AI生成图像描述
- 简洁直观的用户界面
- 转换结果可直接下载为Markdown文件

## 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/markitdown-web.git
cd markitdown-web
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行应用
```bash
streamlit run app.py
```

## 使用方法

1. 访问应用（默认地址为 http://localhost:8501）
2. 在侧边栏配置相关选项（OCR、插件等）
3. 上传需要转换的文件
4. 查看转换结果，并下载Markdown文件

## OCR与AI图像描述功能

要使用OCR功能：
- 在侧边栏勾选"使用OCR识别"选项
- 上传图片或PDF文件，系统将自动识别内容

要使用AI生成图像描述：
- 在高级选项中勾选"使用AI生成图像描述"
- 选择LLM模型（OpenAI或Azure OpenAI）
- 输入相应的API密钥和配置
- 上传图片，系统将使用AI生成描述

## 关于MarkItDown

MarkItDown是Microsoft开发的一个Python工具，用于将各种文件和Office文档转换为Markdown。更多信息请访问：[Microsoft MarkItDown](https://github.com/microsoft/markitdown)

## 项目结构

```
markitdown-web/
├── app.py              # 主应用文件
├── requirements.txt    # 项目依赖
├── README.md           # 项目文档
└── images/             # 项目图片资源
```

## 系统要求

- Python 3.10+
- 依赖库：详见requirements.txt
- ffmpeg (用于音频处理和OCR)
  - Debian/Ubuntu安装: `sudo apt update && sudo apt install -y ffmpeg`
  - CentOS/RHEL安装: `sudo dnf install -y ffmpeg`
  - Windows安装: 下载[ffmpeg](https://ffmpeg.org/download.html)并添加到PATH

## 许可证

MIT License
```
