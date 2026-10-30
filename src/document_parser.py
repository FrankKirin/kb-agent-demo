"""
模块：document_parser
函数 1：load_file(path: str) -> str
  - 支持 .txt/.md（Path.read_text，utf-8）
  - 支持 .pdf（pypdf 的 PdfReader，按页拼接，页间用 \n 连接）
  - 支持 .docx（python-docx 的 Document，遍历 paragraphs 拼接）
  - 不支持的扩展名抛 ValueError，错误信息包含扩展名
函数 2：load_directory(dir_path: str) -> list[tuple[str, str]]
  - 递归遍历，返回 [(文件路径, 文本内容)]
  - 单个文件读取失败时打印 [跳过] 并继续，不中断整体
验收：
  - fixtures/sample.md 能读出非空字符串
  - 传入 .xyz 文件抛 ValueError
  - 目录里混入一个损坏的 pdf，其他文件仍能读出
"""

from pathlib import Path
from typing import List, Tuple


def load_file(path: str) -> str:
    """加载单个文件并返回其文本内容"""
    file_path = Path(path)
    
    # 检查文件是否存在
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    if not file_path.is_file():
        raise ValueError(f"不是文件: {path}")
    
    ext = file_path.suffix.lower()
    
    # 处理文本文件 (.txt, .md)
    if ext in [".txt", ".md"]:
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"无法以 UTF-8 编码读取文件: {path}")
        except Exception as e:
            raise IOError(f"读取文件失败 {path}: {e}")
    
    # 处理 PDF 文件
    elif ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("PDF 文件支持需要 pypdf 库: pip install pypdf")
        
        try:
            reader = PdfReader(path)
            text_parts = []
            
            for page in reader.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception:
                    # 单页提取失败，继续处理下一页
                    continue
            
            return "\n".join(text_parts)
        except Exception as e:
            raise IOError(f"读取 PDF 文件失败 {path}: {e}")
    
    # 处理 Word 文档
    elif ext == ".docx":
        try:
            from docx import Document
        except ImportError:
            raise ImportError("Word 文档支持需要 python-docx 库: pip install python-docx")
        
        try:
            doc = Document(path)
            text_parts = []
            
            for para in doc.paragraphs:
                if para.text:
                    text_parts.append(para.text)
            
            return "\n".join(text_parts)
        except Exception as e:
            raise IOError(f"读取 Word 文档失败 {path}: {e}")
    
    else:
        # 不支持的扩展名
        raise ValueError(f"不支持的文件扩展名 '{ext}' (文件: {path})")


def load_directory(dir_path: str) -> List[Tuple[str, str]]:
    """递归加载目录中的所有支持文件"""
    dir_path_obj = Path(dir_path)
    
    # 检查目录是否存在
    if not dir_path_obj.exists():
        raise FileNotFoundError(f"目录不存在: {dir_path}")
    if not dir_path_obj.is_dir():
        raise ValueError(f"不是目录: {dir_path}")
    
    results = []
    supported_extensions = {".txt", ".md", ".pdf", ".docx"}
    
    # 递归遍历目录
    for file_path in dir_path_obj.rglob("*"):
        if file_path.is_file():
            ext = file_path.suffix.lower()
            
            # 只处理支持的文件类型
            if ext in supported_extensions:
                try:
                    content = load_file(str(file_path))
                    results.append((str(file_path), content))
                except Exception as e:
                    # 单个文件读取失败，打印错误并继续
                    print(f"[跳过] {file_path}: {e}")
                    continue
    
    return results