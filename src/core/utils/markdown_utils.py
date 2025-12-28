"""
Markdown Utilities

提供 Markdown 解析和处理相关的工具函数。
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SectionType(Enum):
    """章节类型枚举"""
    PARAGRAPH = "paragraph"
    HEADER = "header"
    LIST_ITEM = "list_item"
    CODE_BLOCK = "code_block"
    INLINE_CODE = "inline_code"
    BLOCKQUOTE = "blockquote"
    TABLE = "table"
    LINK = "link"
    IMAGE = "image"
    EMPTY = "empty"
    UNKNOWN = "unknown"


@dataclass
class MarkdownSection:
    """Markdown 章节"""
    content: str
    section_type: SectionType
    line_start: int
    line_end: int
    char_start: int
    char_end: int
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def length(self) -> int:
        """内容长度"""
        return len(self.content)

    @property
    def lines_count(self) -> int:
        """行数"""
        return self.line_end - self.line_start + 1


class MarkdownParser:
    """Markdown 解析器"""

    def __init__(self):
        self.patterns = {
            'code_block': re.compile(r'^```'),
            'header': re.compile(r'^(#{1,6})\s+'),
            'list_item': re.compile(r'^(\s*)([-*+]|\d+\.)\s+'),
            'blockquote': re.compile(r'^>\s*'),
            'table': re.compile(r'^\|.*\|'),
            'empty': re.compile(r'^\s*$'),
            'image': re.compile(r'!\[.*?\]\([^)]+\)'),
            'link': re.compile(r'\[.*?\]\([^)]+\)'),
            'inline_code': re.compile(r'`[^`]+`')
        }

    def parse(self, content: str) -> List[MarkdownSection]:
        """
        解析 Markdown 内容

        Args:
            content: Markdown 内容

        Returns:
            解析后的章节列表
        """
        if not content:
            return []

        lines = content.split('\n')
        sections = []
        current_line = 0
        current_char = 0

        while current_line < len(lines):
            line = lines[current_line]
            line_stripped = line.strip()

            # 检测章节类型并处理
            if self.patterns['code_block'].match(line_stripped):
                section = self._parse_code_block(lines, current_line, current_char)
                sections.append(section)
                current_line = section.line_end + 1
                current_char += len(section.content) + 1  # +1 for newline
            elif self.patterns['header'].match(line_stripped):
                section = self._parse_header(lines, current_line, current_char)
                sections.append(section)
                current_line = section.line_end + 1
                current_char += len(section.content) + 1
            elif self.patterns['list_item'].match(line_stripped) or \
                 (current_line > 0 and self._is_continuation_line(lines, current_line)):
                section = self._parse_list_items(lines, current_line, current_char)
                sections.append(section)
                current_line = section.line_end + 1
                current_char += len(section.content) + 1
            else:
                section = self._parse_paragraph(lines, current_line, current_char)
                sections.append(section)
                current_line = section.line_end + 1
                current_char += len(section.content) + 1

        return sections

    def _parse_code_block(self, lines: List[str], start_line: int, start_char: int) -> MarkdownSection:
        """解析代码块"""
        code_lines = [lines[start_line]]
        line_count = len(lines)

        i = start_line + 1
        while i < line_count:
            line = lines[i]
            code_lines.append(line)
            if self.patterns['code_block'].match(line.strip()):
                break
            i += 1

        content = '\n'.join(code_lines)
        end_char = start_char + len(content)

        return MarkdownSection(
            content=content,
            section_type=SectionType.CODE_BLOCK,
            line_start=start_line,
            line_end=i,
            char_start=start_char,
            char_end=end_char,
            metadata={'language': self._extract_language(code_lines[0])}
        )

    def _parse_header(self, lines: List[str], start_line: int, start_char: int) -> MarkdownSection:
        """解析标题"""
        line = lines[start_line]
        content = line
        end_char = start_char + len(content)

        # 提取标题级别
        match = self.patterns['header'].match(line)
        level = len(match.group(1)) if match else 1

        return MarkdownSection(
            content=content,
            section_type=SectionType.HEADER,
            line_start=start_line,
            line_end=start_line,
            char_start=start_char,
            char_end=end_char,
            metadata={'level': level}
        )

    def _parse_list_items(self, lines: List[str], start_line: int, start_char: int) -> MarkdownSection:
        """解析列表项"""
        list_lines = [lines[start_line]]
        i = start_line + 1
        line_count = len(lines)

        while i < line_count:
            line = lines[i]
            line_stripped = line.strip()

            # 检查是否是列表项或续行
            if (self.patterns['list_item'].match(line_stripped) or
                self._is_continuation_line(lines, i)):
                list_lines.append(line)
                i += 1
            else:
                break

        content = '\n'.join(list_lines)
        end_char = start_char + len(content)

        # 检测列表类型
        list_type = self._detect_list_type(list_lines[0])

        return MarkdownSection(
            content=content,
            section_type=SectionType.LIST_ITEM,
            line_start=start_line,
            line_end=i - 1,
            char_start=start_char,
            char_end=end_char,
            metadata={'list_type': list_type}
        )

    def _parse_paragraph(self, lines: List[str], start_line: int, start_char: int) -> MarkdownSection:
        """解析段落"""
        paragraph_lines = [lines[start_line]]
        i = start_line + 1
        line_count = len(lines)

        while i < line_count:
            line = lines[i]
            line_stripped = line.strip()

            # 检查是否应该继续段落
            if (line_stripped and
                not self._is_structural_line(line_stripped)):
                paragraph_lines.append(line)
                i += 1
            else:
                break

        content = '\n'.join(paragraph_lines)
        end_char = start_char + len(content)

        # 检测段落类型（包含链接、图片等）
        section_type = self._detect_content_type(content)

        return MarkdownSection(
            content=content,
            section_type=section_type,
            line_start=start_line,
            line_end=i - 1,
            char_start=start_char,
            char_end=end_char,
            metadata=self._extract_content_metadata(content)
        )

    def _is_continuation_line(self, lines: List[str], line_index: int) -> bool:
        """检查是否是续行"""
        if line_index == 0:
            return False

        prev_line = lines[line_index - 1].strip()
        current_line = lines[line_index].strip()

        # 如果前一行是列表项，当前行可能是续行
        if self.patterns['list_item'].match(prev_line):
            # 检查当前行是否以空格开头（续行特征）
            return lines[line_index].startswith('  ') or lines[line_index].startswith('\t')

        return False

    def _is_structural_line(self, line: str) -> bool:
        """检查是否是结构性行"""
        return any(pattern.match(line) for pattern in [
            self.patterns['header'],
            self.patterns['code_block'],
            self.patterns['list_item'],
            self.patterns['blockquote'],
            self.patterns['table'],
            self.patterns['empty']
        ])

    def _detect_list_type(self, line: str) -> str:
        """检测列表类型"""
        if re.match(r'^\s*\d+\.', line):
            return "ordered"
        elif re.match(r'^\s*[-*+]', line):
            return "unordered"
        else:
            return "unknown"

    def _detect_content_type(self, content: str) -> SectionType:
        """检测内容类型"""
        if self.patterns['image'].search(content):
            return SectionType.IMAGE
        elif self.patterns['link'].search(content):
            return SectionType.LINK
        elif self.patterns['inline_code'].search(content):
            return SectionType.INLINE_CODE
        elif self.patterns['blockquote'].match(content.split('\n')[0]):
            return SectionType.BLOCKQUOTE
        elif self.patterns['table'].match(content.split('\n')[0]):
            return SectionType.TABLE
        elif content.strip() == "":
            return SectionType.EMPTY
        else:
            return SectionType.PARAGRAPH

    def _extract_content_metadata(self, content: str) -> Dict[str, Any]:
        """提取内容元数据"""
        metadata = {}

        # 统计链接和图片数量
        links = self.patterns['link'].findall(content)
        images = self.patterns['image'].findall(content)
        inline_codes = self.patterns['inline_code'].findall(content)

        metadata['links_count'] = len(links)
        metadata['images_count'] = len(images)
        metadata['inline_codes_count'] = len(inline_codes)

        return metadata

    def _extract_language(self, fence_line: str) -> Optional[str]:
        """从代码块标记中提取语言"""
        match = re.match(r'^```(\w+)', fence_line.strip())
        return match.group(1) if match else None


class MarkdownUtils:
    """Markdown 工具类"""

    @staticmethod
    def extract_links(content: str) -> List[str]:
        """提取所有链接"""
        pattern = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
        return [f"{text}({url})" for text, url in pattern.findall(content)]

    @staticmethod
    def extract_images(content: str) -> List[str]:
        """提取所有图片"""
        pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
        return [f"{text}({url})" for text, url in pattern.findall(content)]

    @staticmethod
    def extract_headers(content: str) -> List[Tuple[int, str]]:
        """提取所有标题"""
        pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        return [(len(match.group(1)), match.group(2).strip()) for match in pattern.finditer(content)]

    @staticmethod
    def extract_code_blocks(content: str) -> List[str]:
        """提取所有代码块"""
        pattern = re.compile(r'```[\w]*\n([\s\S]*?)\n```')
        return pattern.findall(content)

    @staticmethod
    def extract_inline_code(content: str) -> List[str]:
        """提取所有内联代码"""
        pattern = re.compile(r'`([^`]+)`')
        return pattern.findall(content)

    @staticmethod
    def count_words(content: str) -> int:
        """统计字数（排除代码和格式）"""
        # 移除代码块
        content = re.sub(r'```[\s\S]*?```', '', content)
        # 移除内联代码
        content = re.sub(r'`[^`]+`', '', content)
        # 移除链接和图片标记
        content = re.sub(r'\[([^\]]*)\]\([^)]+\)', r'\1', content)
        content = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', content)
        # 移除标题标记
        content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
        # 移除列表标记
        content = re.sub(r'^\s*[-*+]\s+', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*\d+\.\s+', '', content, flags=re.MULTILINE)
        # 移除引用标记
        content = re.sub(r'^>\s+', '', content, flags=re.MULTILINE)

        # 统计中英文单词
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', content))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))

        return english_words + chinese_chars

    @staticmethod
    def sanitize_content(content: str) -> str:
        """清理 Markdown 内容"""
        # 移除潜在的恶意脚本
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        # 移除危险的 HTML 标签
        dangerous_tags = ['iframe', 'object', 'embed', 'form']
        for tag in dangerous_tags:
            content = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', content, flags=re.IGNORECASE | re.DOTALL)

        return content

    @staticmethod
    def validate_structure(content: str) -> List[str]:
        """验证 Markdown 结构"""
        errors = []
        lines = content.split('\n')

        # 检查代码块是否闭合
        code_fence_count = content.count('```')
        if code_fence_count % 2 != 0:
            errors.append("Unclosed code block")

        # 检查链接格式
        links = re.findall(r'\[([^\]]*)\]\(([^)]*)\)', content)
        for text, url in links:
            if not text.strip():
                errors.append(f"Empty link text: [{text}]({url})")
            if not url.strip():
                errors.append(f"Empty link URL: [{text}]({url})")

        # 检查图片格式
        images = re.findall(r'!\[([^\]]*)\]\(([^)]*)\)', content)
        for alt_text, url in images:
            if not url.strip():
                errors.append(f"Empty image URL: ![{alt_text}]({url})")

        return errors