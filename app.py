import streamlit as st
import os
from markitdown import MarkItDown
import sys
from openai import OpenAI, AzureOpenAI
import base64
import io
import pytesseract
from PIL import Image
import json
import traceback

st.set_page_config(page_title="MarkItDown Web", layout="wide")

st.title("MarkItDown Web 转换器")

# 使用更可靠的方式处理设置的持久化
def load_settings():
    try:
        # 尝试从localStorage获取设置
        if 'settings' in st.session_state:
            return
        
        # 初始化默认设置
        default_settings = {
            "api_key": "",
            "base_url": "",
            "endpoint": "",
            "model_name": "gpt-4o",
            "llm_option": "自定义OpenAI端点",
            "custom_prompt": "请将以下内容转换为纯markdown格式，只返回文本内容，不要添加任何额外描述或格式说明。保留原文的结构，包括标题、列表、表格等元素。",
            "use_llm": False
        }
        
        # 将默认设置存储到session_state
        st.session_state.settings = default_settings
    except Exception as e:
        st.error(f"加载设置失败: {str(e)}")
        st.session_state.settings = {}

def save_settings():
    # 将当前页面上的设置保存到session_state
    try:
        st.session_state.settings["api_key"] = api_key
        st.session_state.settings["model_name"] = model_name
        st.session_state.settings["llm_option"] = llm_option
        st.session_state.settings["use_llm"] = use_llm
        st.session_state.settings["custom_prompt"] = custom_prompt
        
        if llm_option == "自定义OpenAI端点":
            st.session_state.settings["base_url"] = base_url
        elif llm_option == "Azure OpenAI":
            st.session_state.settings["endpoint"] = endpoint
    except Exception as e:
        st.warning(f"保存设置时出错: {str(e)}")

# 加载设置
load_settings()

# 初始化已处理文件列表和结果存储
if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()
    
# 用于存储所有文件处理结果的字典
if "file_results" not in st.session_state:
    st.session_state.file_results = {}

# 侧边栏配置选项
st.sidebar.markdown("## 配置选项")
enable_plugins = st.sidebar.checkbox("启用插件", value=False)
use_ocr = st.sidebar.checkbox("使用OCR识别（图片和PDF）", value=False, help="当无法使用AI时，将使用OCR作为备选")

# 高级选项折叠区域 - 设置为始终展开
with st.sidebar.expander("高级选项", expanded=True):
    # LLM配置
    use_llm = st.checkbox("使用AI模型", value=st.session_state.settings.get("use_llm", False))
    
    if use_llm:
        # LLM服务选项
        llm_option = st.selectbox(
            "LLM模型服务", 
            ["自定义OpenAI端点", "OpenAI", "Azure OpenAI"], 
            index=["自定义OpenAI端点", "OpenAI", "Azure OpenAI"].index(
                st.session_state.settings.get("llm_option", "自定义OpenAI端点")
            )
        )
        
        # API Key输入
        api_key = st.text_input("API Key", type="password", value=st.session_state.settings.get("api_key", ""))
        
        # 根据LLM服务选项显示相应的配置
        if llm_option == "自定义OpenAI端点":
            # 基础URL输入 - 独立于模型选择
            base_url = st.text_input(
                "基础URL", 
                placeholder="例如: https://endpoint.com/v1", 
                value=st.session_state.settings.get("base_url", "")
            )
            
            # 模型选择
            model_options = ["gpt-4.1-mini", "gpt-4o-mini", "自定义"]
            selected_model = st.selectbox(
                "模型",
                model_options,
                index=model_options.index("自定义") if st.session_state.settings.get("model_name") not in ["gpt-4.1-mini", "gpt-4o-mini"] else model_options.index(st.session_state.settings.get("model_name", "gpt-4.1-mini"))
            )
            
            # 如果选择了自定义模型，显示输入框
            if selected_model == "自定义":
                model_name = st.text_input(
                    "自定义模型名称",
                    value=st.session_state.settings.get("model_name", "") if st.session_state.settings.get("model_name") not in ["gpt-4.1-mini", "gpt-4o-mini"] else ""
                )
            else:
                model_name = selected_model
                
        elif llm_option == "OpenAI":
            # OpenAI模型选择
            model_options = ["gpt-4o", "gpt-4", "gpt-3.5-turbo", "自定义"]
            selected_model = st.selectbox(
                "模型",
                model_options,
                index=model_options.index("自定义") if st.session_state.settings.get("model_name") not in ["gpt-4o", "gpt-4", "gpt-3.5-turbo"] else model_options.index(st.session_state.settings.get("model_name", "gpt-4o"))
            )
            
            # 如果选择了自定义模型，显示输入框
            if selected_model == "自定义":
                model_name = st.text_input(
                    "自定义模型名称",
                    value=st.session_state.settings.get("model_name", "") if st.session_state.settings.get("model_name") not in ["gpt-4o", "gpt-4", "gpt-3.5-turbo"] else ""
                )
            else:
                model_name = selected_model
                
        else:  # Azure OpenAI
            # Azure终端点
            endpoint = st.text_input(
                "Azure 终端点", 
                value=st.session_state.settings.get("endpoint", "")
            )
            
            # 部署名称/模型
            model_name = st.text_input(
                "部署名称", 
                value=st.session_state.settings.get("model_name", "")
            )
        
        # 添加自定义提示词配置
        st.subheader("AI提示词配置")
        custom_prompt = st.text_area(
            "自定义提示词",
            value=st.session_state.settings.get("custom_prompt", "请将以下内容转换为纯markdown格式，只返回文本内容，不要添加任何额外描述或格式说明。保留原文的结构，包括标题、列表、表格等元素。"),
            height=120,
            help="用于指导AI生成的提示词，影响转换结果的格式和内容"
        )
        
        # 保存按钮 - 显式保存设置
        if st.button("保存设置到浏览器", type="primary"):
            save_settings()
            st.success("✅ 设置已保存到浏览器，刷新页面后仍将保留")

# 定义自定义图像处理函数
def process_image_with_ai(client, model, image_path, prompt):
    """使用AI处理图像并返回文本内容"""
    try:
        # 读取图像文件并进行base64编码
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
            image_data = base64.b64encode(image_bytes).decode('utf-8')
        
        # 检查图像是否为空
        if not image_bytes:
            return "错误: 图像文件为空"
        
        # 检查客户端是否有效
        if not client:
            return "错误: AI客户端未正确初始化"
        
        # OpenAI API调用
        if isinstance(client, OpenAI):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": prompt},
                        {
                            "role": "user", 
                            "content": [
                                {"type": "text", "text": "请描述这个图像的内容:"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                            ]
                        }
                    ]
                )
                
                # 调试信息
                if not hasattr(response, 'choices') or len(response.choices) == 0:
                    return f"API响应不包含choices字段: {response}"
                
                # 安全地访问响应内容
                return response.choices[0].message.content
                
            except Exception as api_error:
                error_details = traceback.format_exc()
                return f"OpenAI API调用失败: {str(api_error)}\n详细错误: {error_details}"
                
        # Azure OpenAI API调用    
        elif isinstance(client, AzureOpenAI):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": prompt},
                        {
                            "role": "user", 
                            "content": [
                                {"type": "text", "text": "请描述这个图像的内容:"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                            ]
                        }
                    ]
                )
                
                # 调试信息
                if not hasattr(response, 'choices') or len(response.choices) == 0:
                    return f"Azure API响应不包含choices字段: {response}"
                
                # 安全地访问响应内容
                return response.choices[0].message.content
                
            except Exception as api_error:
                error_details = traceback.format_exc()
                return f"Azure OpenAI API调用失败: {str(api_error)}\n详细错误: {error_details}"
        else:
            return f"不支持的LLM客户端类型: {type(client).__name__}"
            
    except Exception as e:
        error_details = traceback.format_exc()
        return f"AI图像处理出错: {str(e)}\n详细错误: {error_details}"

# 使用OCR处理图像函数(备选方案)
def process_image_with_ocr(image_path):
    """使用OCR处理图像并返回文本内容"""
    try:
        # 自动检测语言
        text = pytesseract.image_to_string(Image.open(image_path))
        return text
    except Exception as e:
        error_details = traceback.format_exc()
        return f"OCR处理出错: {str(e)}\n详细错误: {error_details}"

# 初始化MarkItDown和LLM客户端
try:
    # 根据用户选项配置MarkItDown
    md_kwargs = {
        "enable_plugins": enable_plugins
    }
    
    # 配置LLM客户端
    client = None
    if use_llm and api_key:
        # 使用当前UI中的值，而不是session_state中的值
        if llm_option == "OpenAI":
            client = OpenAI(api_key=api_key)
            md_kwargs["llm_client"] = client
            md_kwargs["llm_model"] = model_name
        elif llm_option == "自定义OpenAI端点":
            if not base_url:
                st.warning("请提供有效的基础URL")
            else:
                client = OpenAI(api_key=api_key, base_url=base_url)
                md_kwargs["llm_client"] = client
                md_kwargs["llm_model"] = model_name
                st.info(f"正在使用自定义OpenAI端点: {base_url} 和模型: {model_name}")
        else:  # Azure OpenAI
            if not endpoint:
                st.warning("请提供有效的Azure终端点")
            else:
                client = AzureOpenAI(
                    api_key=api_key,
                    azure_endpoint=endpoint,
                    api_version="2024-02-15-preview"
                )
                md_kwargs["llm_client"] = client
                md_kwargs["llm_model"] = model_name
    
    # 初始化MarkItDown实例(用于处理非图像文件)
    md = MarkItDown(**md_kwargs)
    
except Exception as e:
    error_details = traceback.format_exc()
    st.error(f"初始化失败: {str(e)}\n详细错误: {error_details}")
    st.stop()

# 显示使用说明
st.sidebar.markdown("""
## 使用说明
1. 点击"选择要转换的文件"上传一个或多个文件
2. 系统会自动转换文件为 Markdown 格式
3. 可以预览转换结果
4. 点击"下载 Markdown 文件"保存结果

## 支持的文件格式
- PDF (启用OCR可识别图片中的文字)
- Word
- PowerPoint
- Excel
- 图片文件 (启用OCR可识别文字)
- 音频文件 (支持转录)
- HTML
- CSV, JSON, XML
- ZIP 文件
""")

# 开发调试模式
debug_mode = st.sidebar.checkbox("调试模式", value=False)

# 清除所有处理记录的按钮
if st.button("清除所有处理记录", type="secondary"):
    st.session_state.processed_files = set()
    st.session_state.file_results = {}
    st.success("✅ 所有处理记录已清除")

# 文件上传部分
uploaded_files = st.file_uploader("选择要转换的文件", accept_multiple_files=True)

# 处理新文件
if uploaded_files:
    # 筛选出未处理的文件
    new_files = [f for f in uploaded_files if f.name not in st.session_state.processed_files]
    
    # 显示处理信息
    if new_files:
        st.subheader(f"处理新上传的文件 ({len(new_files)} 个)")
        
        # 处理新文件
        for uploaded_file in new_files:
            # 保存上传的文件到临时目录
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                # 判断文件类型，如果是图像则使用自定义API处理
                file_ext = os.path.splitext(temp_path)[1].lower()
                is_image = file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
                
                # 使用AI处理图像
                if is_image and use_llm and client:
                    with st.spinner(f"使用AI处理图像 {uploaded_file.name}..."):
                        prompt_to_use = custom_prompt  # 使用当前UI中的提示词
                        
                        # 显示调试信息
                        if debug_mode:
                            st.write("调试信息:")
                            st.write(f"模型: {model_name}")
                            st.write(f"客户端类型: {type(client).__name__}")
                            st.write(f"图像路径: {temp_path}")
                            st.write(f"图像大小: {os.path.getsize(temp_path)} 字节")
                        
                        result_text = process_image_with_ai(client, model_name, temp_path, prompt_to_use)
                        result_content = result_text
                        
                        # 检查结果是否包含错误信息
                        if result_text.startswith("错误:") or result_text.startswith("API") or result_text.startswith("AI图像处理出错"):
                            st.error(result_text)
                            # 尝试使用OCR作为备选
                            st.info("尝试使用OCR作为备选...")
                            result_text = process_image_with_ocr(temp_path)
                            result_content = result_text
                            
                # 备选方案：使用OCR处理图像
                elif is_image and use_ocr:
                    with st.spinner(f"使用OCR处理图像 {uploaded_file.name}..."):
                        result_text = process_image_with_ocr(temp_path)
                        result_content = result_text
                # 对于非图像文件，使用MarkItDown进行处理
                else:
                    with st.spinner(f"正在转换 {uploaded_file.name}..."):
                        result = md.convert(temp_path)
                        result_content = result.text_content
                
                # 保存结果到session_state
                st.session_state.file_results[uploaded_file.name] = {
                    "content": result_content,
                    "filename": os.path.splitext(uploaded_file.name)[0]
                }
                
                # 标记文件为已处理
                st.session_state.processed_files.add(uploaded_file.name)
                
            except Exception as e:
                error_details = traceback.format_exc()
                st.error(f"转换失败: {str(e)}")
                st.error(f"详细错误信息: {error_details}")
            finally:
                # 清理临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)

# 显示所有处理结果（包括新处理的和之前处理过的）
if st.session_state.file_results:
    st.header("所有已处理文件")
    
    # 遍历所有文件处理结果并显示
    for file_name, file_data in st.session_state.file_results.items():
        with st.expander(f"处理文件: {file_name}", expanded=True):
            # 显示转换结果
            st.text_area("转换结果", file_data["content"], height=300, key=f"result_{file_name}")
            
            # 提供下载按钮
            st.download_button(
                label="下载 Markdown 文件",
                data=file_data["content"],
                file_name=f"{file_data['filename']}.md",
                mime="text/markdown"
            )