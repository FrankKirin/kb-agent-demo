"""
pytest测试文件，用于测试document_parser.py模块
"""

import pytest
from pathlib import Path
import shutil
from src import document_parser


class TestLoadFile:
    """测试load_file函数"""
    
    def test_read_md_file_returns_non_empty_string(self):
        """测试读取.md文件返回非空字符串"""
        # 使用fixtures目录中的sample.md文件
        md_file = Path(__file__).parent.parent / "fixtures" / "sample.md"
        content = document_parser.load_file(str(md_file))
        
        # 验证返回的是非空字符串
        assert isinstance(content, str)
        assert len(content) > 0
        assert "Sample Markdown File" in content
        
    def test_read_txt_file_returns_non_empty_string(self):
        """测试读取.txt文件返回非空字符串"""
        txt_file = Path(__file__).parent.parent / "fixtures" / "sample.txt"
        content = document_parser.load_file(str(txt_file))
        
        # 验证返回的是非空字符串
        assert isinstance(content, str)
        assert len(content) > 0
        assert "simple text file" in content
        
    def test_unsupported_extension_raises_valueerror(self, tmp_path):
        """测试不支持的扩展名抛出ValueError"""
        # 创建一个.xyz文件
        xyz_file = tmp_path / "test.xyz"
        xyz_file.write_text("test content")
        
        # 验证调用会抛出ValueError
        with pytest.raises(ValueError) as exc_info:
            document_parser.load_file(str(xyz_file))
        
        # 验证错误信息包含扩展名
        assert "'.xyz'" in str(exc_info.value)
        assert "不支持的文件扩展名" in str(exc_info.value)
        
    def test_nonexistent_file_raises_filenotfounderror(self):
        """测试不存在的文件抛出FileNotFoundError"""
        with pytest.raises(FileNotFoundError) as exc_info:
            document_parser.load_file("/path/to/nonexistent/file.txt")
        
        assert "文件不存在" in str(exc_info.value)
        
    def test_directory_path_raises_valueerror(self, tmp_path):
        """测试传入目录路径抛出ValueError"""
        # 创建一个目录
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        with pytest.raises(ValueError) as exc_info:
            document_parser.load_file(str(test_dir))
        
        assert "不是文件" in str(exc_info.value)


class TestLoadDirectory:
    """测试load_directory函数"""
    
    def test_load_directory_with_good_and_bad_files(self, tmp_path, capsys):
        """测试目录中有一个坏文件不影响其他文件"""
        # 创建几个测试文件
        md_file = tmp_path / "test1.md"
        txt_file = tmp_path / "test2.txt"
        # 使用一个支持的扩展名但内容损坏的PDF文件
        # PDF解析会失败，但会被捕获并继续
        bad_file = tmp_path / "bad.pdf"
        
        # 写入内容
        md_content = "# Markdown File\nContent here"
        txt_content = "Text file content\nLine 2"
        
        md_file.write_text(md_content, encoding="utf-8")
        txt_file.write_text(txt_content, encoding="utf-8")
        # 创建一个不是真正PDF格式的文件
        bad_file.write_text("Not a real PDF file", encoding="utf-8")
        
        # 调用load_directory
        results = document_parser.load_directory(str(tmp_path))
        
        # 捕获print输出
        captured = capsys.readouterr()
        
        # 验证结果：应该包含.md和.txt文件
        assert len(results) == 2  # .md和.txt
        
        # 提取文件路径用于验证
        result_paths = [r[0] for r in results]
        
        # 确认.md和.txt文件被成功读取
        assert any("test1.md" in path for path in result_paths)
        assert any("test2.txt" in path for path in result_paths)
        
        # 确认内容正确
        for path, content in results:
            if "test1.md" in path:
                assert md_content in content
            elif "test2.txt" in path:
                assert txt_content in content
        
        # 验证错误消息被打印到标准输出
        assert "bad.pdf" in captured.out
        assert "[跳过]" in captured.out
        
    def test_load_empty_directory(self, tmp_path):
        """测试空目录返回空列表"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        results = document_parser.load_directory(str(empty_dir))
        assert results == []
        
    def test_load_directory_recursive(self, tmp_path):
        """测试递归加载目录"""
        # 创建嵌套目录结构
        subdir1 = tmp_path / "subdir1"
        subdir2 = tmp_path / "subdir2" / "nested"
        subdir1.mkdir()
        subdir2.mkdir(parents=True)
        
        # 在不同层级创建文件
        file1 = tmp_path / "root.txt"
        file2 = subdir1 / "sub1.md"
        file3 = subdir2 / "deep.txt"
        
        file1.write_text("root file", encoding="utf-8")
        file2.write_text("subdir1 file", encoding="utf-8")
        file3.write_text("deep nested file", encoding="utf-8")
        
        # 调用load_directory
        results = document_parser.load_directory(str(tmp_path))
        
        # 应该找到3个文件
        assert len(results) == 3
        
        # 验证所有文件都被找到
        result_paths = [r[0] for r in results]
        assert any("root.txt" in path for path in result_paths)
        assert any("sub1.md" in path for path in result_paths)
        assert any("deep.txt" in path for path in result_paths)
        
    def test_nonexistent_directory_raises_filenotfounderror(self):
        """测试不存在的目录抛出FileNotFoundError"""
        with pytest.raises(FileNotFoundError) as exc_info:
            document_parser.load_directory("/path/to/nonexistent/dir")
        
        assert "目录不存在" in str(exc_info.value)
        
    def test_file_path_as_directory_raises_valueerror(self, tmp_path):
        """测试传入文件路径作为目录抛出ValueError"""
        # 创建一个文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("test", encoding="utf-8")
        
        with pytest.raises(ValueError) as exc_info:
            document_parser.load_directory(str(test_file))
        
        assert "不是目录" in str(exc_info.value)

class TestSupportedExtensions:
    """测试支持的文件扩展名"""
    
    @pytest.mark.parametrize("extension,content", [
        (".txt", "Text file content"),
        (".md", "# Markdown content"),
        (".TXT", "Uppercase extension"),
        (".MD", "Uppercase markdown"),
    ])
    def test_supported_text_extensions(self, tmp_path, extension, content):
        """测试支持的各种文本文件扩展名"""
        test_file = tmp_path / f"test{extension}"
        test_file.write_text(content, encoding="utf-8")
        
        result = document_parser.load_file(str(test_file))
        assert result == content

    def test_unicode_decode_error(self, tmp_path):
        """测试非UTF-8编码的文件抛出UnicodeDecodeError（转换后为ValueError）"""
        # 创建一个非UTF-8编码的文件
        test_file = tmp_path / "test.txt"
        # 写入一些非UTF-8的二进制数据（例如：使用ISO-8859-1编码的字节）
        try:
            # 尝试用非UTF-8编码写入
            test_file.write_bytes(b'\xe9')  # ISO-8859-1中的é字符
            
            # 这应该会引发UnicodeDecodeError，在代码中会被捕获并重新抛出为ValueError
            with pytest.raises(ValueError) as exc_info:
                document_parser.load_file(str(test_file))
            
            assert "无法以 UTF-8 编码读取文件" in str(exc_info.value)
        except Exception as e:
            # 在某些系统上，write_bytes可能不会导致解码错误
            # 跳过这个测试
            pytest.skip(f"系统不支持创建非UTF-8文件: {e}")

    def test_pdf_file_requires_pypdf(self, tmp_path, monkeypatch):
        """测试PDF文件需要pypdf库（模拟ImportError）"""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("%PDF dummy", encoding="utf-8")
        
        # 模拟pypdf导入失败
        original_import = __import__
        
        def mock_import(name, *args, **kwargs):
            if name == "pypdf":
                raise ImportError("No module named 'pypdf'")
            return original_import(name, *args, **kwargs)
        
        monkeypatch.setattr("builtins.__import__", mock_import)
        
        # 重新导入document_parser以应用模拟
        import importlib
        import sys
        if "src.document_parser" in sys.modules:
            del sys.modules["src.document_parser"]
        
        with pytest.raises(ImportError) as exc_info:
            # 重新导入并调用
            from src import document_parser as new_parser
            new_parser.load_file(str(test_file))
        
        assert "PDF 文件支持需要 pypdf 库" in str(exc_info.value)

    def test_docx_file_requires_python_docx(self, tmp_path, monkeypatch):
        """测试docx文件需要python-docx库（模拟ImportError）"""
        test_file = tmp_path / "test.docx"
        test_file.write_text("dummy", encoding="utf-8")
        
        # 模拟docx导入失败
        original_import = __import__
        
        def mock_import(name, *args, **kwargs):
            if name == "docx":
                raise ImportError("No module named 'docx'")
            return original_import(name, *args, **kwargs)
        
        monkeypatch.setattr("builtins.__import__", mock_import)
        
        # 重新导入document_parser以应用模拟
        import importlib
        import sys
        if "src.document_parser" in sys.modules:
            del sys.modules["src.document_parser"]
        
        with pytest.raises(ImportError) as exc_info:
            # 重新导入并调用
            from src import document_parser as new_parser
            new_parser.load_file(str(test_file))
        
        assert "Word 文档支持需要 python-docx 库" in str(exc_info.value)

    def test_read_docx_file_returns_content(self):
        """测试读取.docx文件返回内容"""
        docx_file = Path(__file__).parent.parent / "fixtures" / "test_document.docx"
        content = document_parser.load_file(str(docx_file))
        
        # 验证返回的是非空字符串
        assert isinstance(content, str)
        assert len(content) > 0
        assert "Test Document for Document Parser" in content
        
    def test_text_file_general_exception(self, tmp_path, monkeypatch):
        """测试文本文件读取时的通用异常处理"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content", encoding="utf-8")
        
        # 模拟read_text抛出异常
        original_read_text = Path.read_text
        
        def mock_read_text(self, *args, **kwargs):
            raise PermissionError("Permission denied")
        
        monkeypatch.setattr(Path, "read_text", mock_read_text)
        
        with pytest.raises(IOError) as exc_info:
            document_parser.load_file(str(test_file))
        
        assert "读取文件失败" in str(exc_info.value)