"""
PDF解析模块
从PDF文件中提取文本内容
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import PyPDF2
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from tqdm import tqdm

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils.config import config


class PDFParser:
    """PDF解析器类"""
    
    def __init__(self, output_dir: str = None):
        """
        初始化PDF解析器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir or str(config.RAW_DATA_DIR / "literature")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def extract_with_pypdf2(self, pdf_path: str) -> str:
        """
        使用PyPDF2提取PDF文本
        
        Args:
            pdf_path: PDF文件路径
        
        Returns:
            提取的文本
        """
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"PyPDF2提取失败: {e}")
        
        return text
    
    def extract_with_pdfminer(self, pdf_path: str) -> str:
        """
        使用pdfminer提取PDF文本（更准确）
        
        Args:
            pdf_path: PDF文件路径
        
        Returns:
            提取的文本
        """
        try:
            text = extract_text(
                pdf_path,
                laparams=LAParams(
                    line_margin=0.5,
                    word_margin=0.1,
                    char_margin=2.0,
                    boxes_flow=0.5
                )
            )
            return text
        except Exception as e:
            print(f"pdfminer提取失败: {e}")
            return ""
    
    def parse_pdf(
        self,
        pdf_path: str,
        save_txt: bool = True,
        save_metadata: bool = True
    ) -> Dict[str, str]:
        """
        解析单个PDF文件
        
        Args:
            pdf_path: PDF文件路径
            save_txt: 是否保存为txt文件
            save_metadata: 是否保存元数据
        
        Returns:
            包含文本内容的字典
        """
        if not os.path.exists(pdf_path):
            print(f"PDF文件不存在: {pdf_path}")
            return {}
        
        print(f"正在解析: {pdf_path}")
        
        # 优先使用pdfminer
        text = self.extract_with_pdfminer(pdf_path)
        
        # 如果pdfminer提取内容过少，尝试PyPDF2
        if not text or len(text.strip()) < 100:
            print("  pdfminer提取内容较少，尝试PyPDF2...")
            text = self.extract_with_pypdf2(pdf_path)
        
        # 检查提取结果
        if not text or len(text.strip()) < 100:
            print("  警告：提取的文本内容过少，可能需要OCR")
            return {}
        
        file_name = Path(pdf_path).stem
        
        # 保存为txt文件
        if save_txt:
            txt_path = os.path.join(self.output_dir, f"{file_name}.txt")
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"  文本已保存: {txt_path}")
        
        # 保存元数据
        if save_metadata:
            metadata = {
                "source_file": pdf_path,
                "file_name": file_name,
                "text_length": len(text),
                "char_count": len(text),
                "line_count": len(text.split('\n')),
                "preview": text[:500] + "..." if len(text) > 500 else text
            }
            
            json_path = os.path.join(self.output_dir, f"{file_name}_metadata.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            print(f"  元数据已保存: {json_path}")
        
        return {file_name: text}
    
    def parse_directory(
        self,
        directory: str,
        pattern: str = "*.pdf",
        recursive: bool = False
    ) -> List[Dict[str, str]]:
        """
        解析目录下的所有PDF文件
        
        Args:
            directory: PDF文件目录
            pattern: 文件匹配模式
            recursive: 是否递归搜索
        
        Returns:
            所有PDF文件的文本内容列表
        """
        dir_path = Path(directory)
        
        if not dir_path.exists():
            print(f"目录不存在: {directory}")
            return []
        
        # 查找PDF文件
        if recursive:
            pdf_files = list(dir_path.rglob(pattern))
        else:
            pdf_files = list(dir_path.glob(pattern))
        
        if not pdf_files:
            print(f"在目录 {directory} 中未找到PDF文件")
            return []
        
        print(f"找到 {len(pdf_files)} 个PDF文件")
        
        results = []
        for pdf_file in tqdm(pdf_files, desc="解析PDF文件"):
            result = self.parse_pdf(str(pdf_file))
            if result:
                results.append(result)
        
        # 保存汇总信息
        summary = {
            "total_files": len(pdf_files),
            "successful_extractions": len(results),
            "failed_extractions": len(pdf_files) - len(results),
            "files": [list(r.keys())[0] for r in results]
        }
        
        summary_path = os.path.join(self.output_dir, "extraction_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n解析完成:")
        print(f"  成功: {summary['successful_extractions']}")
        print(f"  失败: {summary['failed_extractions']}")
        print(f"  汇总信息: {summary_path}")
        
        return results
    
    def split_text_by_sections(
        self,
        text: str,
        section_markers: List[str] = None
    ) -> Dict[str, str]:
        """
        按章节分割文本
        
        Args:
            text: 文本内容
            section_markers: 章节标记列表
        
        Returns:
            章节字典
        """
        if section_markers is None:
            section_markers = [
                "摘要", "关键词", "引言", "方法", "结果", "讨论", "结论", "参考文献"
            ]
        
        sections = {}
        current_section = "前言"
        current_text = []
        
        for line in text.split('\n'):
            line = line.strip()
            
            # 检查是否是章节标题
            is_section = False
            for marker in section_markers:
                if marker in line and len(line) < 50:
                    # 保存当前章节
                    if current_text:
                        sections[current_section] = '\n'.join(current_text)
                    
                    # 开始新章节
                    current_section = marker
                    current_text = []
                    is_section = True
                    break
            
            if not is_section and line:
                current_text.append(line)
        
        # 保存最后一个章节
        if current_text:
            sections[current_section] = '\n'.join(current_text)
        
        return sections


if __name__ == "__main__":
    # 测试PDF解析
    parser = PDFParser()
    
    # 解析项目根目录下的PDF文件
    project_root = config.PROJECT_ROOT
    results = parser.parse_directory(str(project_root), pattern="*.pdf")
    
    print(f"\n共解析 {len(results)} 个PDF文件")
