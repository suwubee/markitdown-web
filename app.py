import streamlit as st
import os
from markitdown import MarkItDown

st.set_page_config(page_title="MarkItDown Web", layout="wide")

st.title("MarkItDown Web 转换器")

# Initialize MarkItDown without the enable_plugins parameter
md = MarkItDown()

# 文件上传部分
uploaded_files = st.file_uploader("选择要转换的文件", accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.subheader(f"处理文件: {uploaded_file.name}")
        
        # 保存上传的文件到临时目录
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        try:
            # 转换文件
            result = md.convert(temp_path)
            
            # 显示转换结果
            st.text_area("转换结果", result.text_content, height=300)
            
            # 提供下载按钮
            st.download_button(
                label="下载 Markdown 文件",
                data=result.text_content,
                file_name=f"{os.path.splitext(uploaded_file.name)[0]}.md",
                mime="text/markdown"
            )
            
        except Exception as e:
            st.error(f"转换失败: {str(e)}")
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

st.sidebar.markdown("""
## 使用说明
1. 点击"选择要转换的文件"上传一个或多个文件
2. 系统会自动转换文件为 Markdown 格式
3. 可以预览转换结果
4. 点击"下载 Markdown 文件"保存结果

## 支持的文件格式
- PDF
- Word
- PowerPoint
- Excel
- 图片文件
- 音频文件
- HTML
- CSV, JSON, XML
- ZIP 文件
""")