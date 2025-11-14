"""
中文文本分块器

专门优化用于中文文本的分块器，支持按句子边界分割，避免在词语中间切分。
"""

import logging
import re
from typing import List
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class ChineseTextSplitter:
    """
    中文文本分块器

    专门优化用于中文文本的分块器。
    - 支持按句子边界分割，避免破坏语义完整性
    - 避免在词语中间切分
    - 支持配置分块大小和重叠大小

    Args:
        chunk_size: 分块大小（字符数）
        chunk_overlap: 重叠大小（字符数）
        respect_sentence_boundary: 是否尊重句子边界

    示例:
        >>> splitter = ChineseTextSplitter(chunk_size=500, chunk_overlap=50)
        >>> chunks = splitter.split_text("这是一段中文文本。包含多个句子。")
        >>> print(f"分割成 {len(chunks)} 个块")
    """

    # 中文句子分隔符
    SENTENCE_SEPARATORS = ['。', '！', '？', '；', '\n', '…']
    
    # 次要分隔符（用于长句子的进一步分割）
    SECONDARY_SEPARATORS = ['，', '、', '：', '"', '"', ''', ''']

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        respect_sentence_boundary: bool = True
    ):
        """
        初始化中文分块器

        Args:
            chunk_size: 分块大小（字符数）
            chunk_overlap: 重叠大小（字符数）
            respect_sentence_boundary: 是否尊重句子边界
        """
        if chunk_size <= 0:
            raise ValueError(f"chunk_size必须大于0，当前值: {chunk_size}")

        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap不能为负数，当前值: {chunk_overlap}")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) 必须小于 chunk_size ({chunk_size})"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.respect_sentence_boundary = respect_sentence_boundary

        logger.debug(
            f"初始化ChineseTextSplitter: chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}, respect_sentence_boundary={respect_sentence_boundary}"
        )

    def split_text(self, text: str) -> List[str]:
        """
        分割中文文本

        根据配置选择合适的分割策略：
        - 如果respect_sentence_boundary=True，按句子边界分割
        - 否则按字符数分割（但仍避免在词语中间切分）

        Args:
            text: 要分割的文本

        Returns:
            分割后的文本块列表

        Raises:
            ValueError: 如果text为空或无效
        """
        if not text:
            raise ValueError("文本不能为空")

        if not isinstance(text, str):
            raise ValueError("text必须是字符串类型")

        logger.debug(f"开始分割文本，长度: {len(text)} 字符")

        if self.respect_sentence_boundary:
            chunks = self._split_by_sentences(text)
        else:
            chunks = self._split_by_chars(text)

        logger.debug(f"分割完成，生成 {len(chunks)} 个块")
        return chunks

    def _split_by_sentences(self, text: str) -> List[str]:
        """
        按句子边界分割文本

        优先在句子分隔符处切分，确保语义完整性。
        如果单个句子超过chunk_size，则进一步使用次要分隔符切分。

        Args:
            text: 要分割的文本

        Returns:
            分割后的文本块列表
        """
        # 首先按主要分隔符分割成句子
        sentences = self._split_into_sentences(text)
        
        if not sentences:
            return []

        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # 如果单个句子就超过chunk_size，需要进一步切分
            if len(sentence) > self.chunk_size:
                # 先保存当前块（如果有内容）
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # 对长句子进行切分
                sub_chunks = self._split_long_sentence(sentence)
                chunks.extend(sub_chunks)
                continue
            
            # 检查添加这个句子是否会超过chunk_size
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence
            else:
                # 保存当前块
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # 开始新块，考虑重叠
                if self.chunk_overlap > 0 and chunks:
                    # 从上一个块的末尾取overlap部分
                    overlap_text = self._get_overlap_text(chunks[-1], self.chunk_overlap)
                    current_chunk = overlap_text + sentence
                else:
                    current_chunk = sentence
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        将文本分割成句子

        使用中文句子分隔符进行分割，保留分隔符。

        Args:
            text: 要分割的文本

        Returns:
            句子列表
        """
        # 构建正则表达式模式，匹配句子分隔符
        pattern = '([' + ''.join(re.escape(sep) for sep in self.SENTENCE_SEPARATORS) + '])'
        
        # 分割并保留分隔符
        parts = re.split(pattern, text)
        
        # 重新组合句子和分隔符
        sentences = []
        for i in range(0, len(parts) - 1, 2):
            if i + 1 < len(parts):
                sentence = parts[i] + parts[i + 1]
                if sentence.strip():
                    sentences.append(sentence)
        
        # 处理最后一个部分（如果没有分隔符结尾）
        if len(parts) % 2 == 1 and parts[-1].strip():
            sentences.append(parts[-1])
        
        return sentences

    def _split_long_sentence(self, sentence: str) -> List[str]:
        """
        分割过长的句子

        使用次要分隔符（逗号、顿号等）进一步切分长句子。

        Args:
            sentence: 要分割的长句子

        Returns:
            分割后的文本块列表
        """
        # 首先尝试使用次要分隔符
        pattern = '([' + ''.join(re.escape(sep) for sep in self.SECONDARY_SEPARATORS) + '])'
        parts = re.split(pattern, sentence)
        
        chunks = []
        current_chunk = ""
        
        for i in range(0, len(parts)):
            part = parts[i]
            
            if len(current_chunk) + len(part) <= self.chunk_size:
                current_chunk += part
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # 如果单个part还是太长，按字符切分
                if len(part) > self.chunk_size:
                    char_chunks = self._split_by_chars(part)
                    chunks.extend(char_chunks)
                    current_chunk = ""
                else:
                    current_chunk = part
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def _split_by_chars(self, text: str) -> List[str]:
        """
        按字符数分割（避免在词语中间切分）

        当无法按句子边界分割时使用。
        尽量在空格或标点符号处切分。

        Args:
            text: 要分割的文本

        Returns:
            分割后的文本块列表
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        
        while start < len(text):
            # 计算当前块的结束位置
            end = start + self.chunk_size
            
            if end >= len(text):
                # 最后一块
                chunks.append(text[start:].strip())
                break
            
            # 尝试在合适的位置切分（空格、标点等）
            split_pos = self._find_split_position(text, start, end)
            
            chunks.append(text[start:split_pos].strip())
            
            # 下一块的起始位置考虑重叠
            start = split_pos - self.chunk_overlap if self.chunk_overlap > 0 else split_pos
            
            # 确保不会倒退
            if start <= chunks[-1].find(text[start:start+10]):
                start = split_pos
        
        return chunks

    def _find_split_position(self, text: str, start: int, end: int) -> int:
        """
        在指定范围内找到合适的切分位置

        优先在标点符号或空格处切分。

        Args:
            text: 文本
            start: 起始位置
            end: 结束位置

        Returns:
            切分位置
        """
        # 在end附近查找合适的切分点（向前查找最多50个字符）
        search_start = max(start, end - 50)
        search_text = text[search_start:end]
        
        # 查找所有可能的分隔符
        all_separators = self.SENTENCE_SEPARATORS + self.SECONDARY_SEPARATORS + [' ', '\t']
        
        # 从后向前查找最近的分隔符
        best_pos = -1
        for i in range(len(search_text) - 1, -1, -1):
            if search_text[i] in all_separators:
                best_pos = search_start + i + 1
                break
        
        # 如果找到了合适的位置，返回
        if best_pos > start:
            return best_pos
        
        # 否则就在end位置切分
        return end

    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """
        从文本末尾获取指定长度的重叠文本

        尝试在句子或词语边界处获取重叠。

        Args:
            text: 源文本
            overlap_size: 重叠大小

        Returns:
            重叠文本
        """
        if len(text) <= overlap_size:
            return text
        
        # 从末尾取overlap_size个字符
        overlap_start = len(text) - overlap_size
        overlap_text = text[overlap_start:]
        
        # 尝试找到一个好的起始点（句子或词语边界）
        all_separators = self.SENTENCE_SEPARATORS + self.SECONDARY_SEPARATORS + [' ', '\t']
        
        for i in range(len(overlap_text)):
            if overlap_text[i] in all_separators:
                return overlap_text[i+1:]
        
        return overlap_text

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        将文档列表分割成更小的块

        Args:
            documents: 要分割的Document对象列表

        Returns:
            分割后的Document块列表

        Raises:
            ValueError: 如果documents为空或无效
        """
        if not documents:
            raise ValueError("文档列表不能为空")

        if not isinstance(documents, list):
            raise ValueError("documents必须是列表类型")

        logger.info(f"开始分割 {len(documents)} 个文档（使用中文分块器）...")

        all_chunks = []
        
        for doc in documents:
            try:
                # 分割文本
                text_chunks = self.split_text(doc.page_content)
                
                # 为每个文本块创建Document对象
                for i, chunk_text in enumerate(text_chunks):
                    chunk_doc = Document(
                        page_content=chunk_text,
                        metadata={
                            **doc.metadata,
                            'chunk_index': i,
                            'splitter': 'chinese'
                        }
                    )
                    all_chunks.append(chunk_doc)
                    
            except Exception as e:
                logger.error(f"分割文档时出错: {e}")
                # 继续处理其他文档
                continue

        if not all_chunks:
            logger.warning("分割后未生成任何块")
            return []

        # 计算统计信息
        total_chars = sum(len(chunk.page_content) for chunk in all_chunks)
        avg_chunk_size = total_chars // len(all_chunks) if all_chunks else 0

        logger.info(f"✓ 分割完成: 生成 {len(all_chunks)} 个块")
        logger.info(f"  - 平均块大小: {avg_chunk_size} 字符")
        logger.info(f"  - 总字符数: {total_chars}")

        return all_chunks
