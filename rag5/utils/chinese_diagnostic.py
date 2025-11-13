"""
中文文本诊断工具

提供中文文本分析和诊断功能，帮助识别潜在问题。
"""

import logging
import re
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ChineseTextDiagnostic:
    """
    中文文本诊断工具

    分析中文文本的特征，检测潜在问题，验证与嵌入模型的兼容性。

    示例:
        >>> diagnostic = ChineseTextDiagnostic()
        >>> result = diagnostic.analyze_text("这是一段中文文本。")
        >>> print(f"字符数: {result['char_count']}")
    """

    # 中文字符范围（Unicode）
    CHINESE_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fff]')
    
    # 中文标点符号
    CHINESE_PUNCTUATION = '，。！？；：""''（）【】《》、…—'
    
    # 句子分隔符
    SENTENCE_SEPARATORS = ['。', '！', '？', '；', '\n', '…']
    
    # 常见编码问题字符
    ENCODING_ISSUE_PATTERNS = [
        r'â€',  # UTF-8编码问题
        r'Ã',   # Latin-1编码问题
        r'�',   # 替换字符（编码错误）
    ]

    def __init__(self):
        """初始化中文文本诊断工具"""
        logger.debug("初始化ChineseTextDiagnostic")

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        分析中文文本

        提供详细的文本统计和特征分析。

        Args:
            text: 要分析的文本

        Returns:
            分析结果字典，包含：
            - char_count: 字符总数
            - chinese_char_count: 中文字符数
            - chinese_ratio: 中文字符占比
            - word_count: 词数（估算）
            - sentence_count: 句子数
            - encoding: 编码格式
            - has_special_chars: 是否包含特殊字符
            - potential_issues: 潜在问题列表

        Raises:
            ValueError: 如果text为空或无效
        """
        if not text:
            raise ValueError("文本不能为空")

        if not isinstance(text, str):
            raise ValueError("text必须是字符串类型")

        logger.debug(f"开始分析文本，长度: {len(text)} 字符")

        # 基本统计
        char_count = len(text)
        chinese_chars = self.CHINESE_CHAR_PATTERN.findall(text)
        chinese_char_count = len(chinese_chars)
        chinese_ratio = chinese_char_count / char_count if char_count > 0 else 0

        # 词数估算（中文按字符数，英文按空格分割）
        # 简化估算：中文字符数 + 英文单词数
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        word_count = chinese_char_count + english_words

        # 句子数统计
        sentence_count = self._count_sentences(text)

        # 编码检测
        encoding = self._detect_encoding(text)

        # 特殊字符检测
        has_special_chars = self._has_special_chars(text)

        # 潜在问题检测
        potential_issues = self._detect_issues(text, char_count, chinese_ratio)

        result = {
            'char_count': char_count,
            'chinese_char_count': chinese_char_count,
            'chinese_ratio': round(chinese_ratio, 2),
            'word_count': word_count,
            'sentence_count': sentence_count,
            'encoding': encoding,
            'has_special_chars': has_special_chars,
            'potential_issues': potential_issues
        }

        logger.debug(f"文本分析完成: {result}")
        return result

    def _count_sentences(self, text: str) -> int:
        """
        统计句子数量

        Args:
            text: 文本

        Returns:
            句子数量
        """
        count = 0
        for separator in self.SENTENCE_SEPARATORS:
            count += text.count(separator)
        
        # 如果没有句子分隔符，至少算一个句子
        return max(count, 1)

    def _detect_encoding(self, text: str) -> str:
        """
        检测文本编码

        Args:
            text: 文本

        Returns:
            编码格式字符串
        """
        try:
            # Python 3中字符串默认是Unicode
            # 检查是否可以编码为UTF-8
            text.encode('utf-8')
            return 'UTF-8'
        except UnicodeEncodeError:
            return 'Unknown'

    def _has_special_chars(self, text: str) -> bool:
        """
        检测是否包含特殊字符

        Args:
            text: 文本

        Returns:
            是否包含特殊字符
        """
        # 检测控制字符（除了常见的换行、制表符）
        control_chars = re.findall(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', text)
        return len(control_chars) > 0

    def _detect_issues(
        self,
        text: str,
        char_count: int,
        chinese_ratio: float
    ) -> List[str]:
        """
        检测潜在问题

        Args:
            text: 文本
            char_count: 字符数
            chinese_ratio: 中文字符占比

        Returns:
            问题列表
        """
        issues = []

        # 检测编码问题
        for pattern in self.ENCODING_ISSUE_PATTERNS:
            if re.search(pattern, text):
                issues.append(f"检测到可能的编码问题: 包含异常字符模式 '{pattern}'")
                break

        # 检测文本过长
        if char_count > 10000:
            issues.append(f"文本过长 ({char_count} 字符)，可能影响嵌入模型性能")

        # 检测文本过短
        if char_count < 10:
            issues.append(f"文本过短 ({char_count} 字符)，可能无法生成有意义的嵌入")

        # 检测中文占比异常
        if chinese_ratio < 0.1 and char_count > 100:
            issues.append(
                f"中文字符占比过低 ({chinese_ratio:.1%})，"
                "可能不适合使用中文优化的分块器"
            )

        # 检测特殊字符
        if self._has_special_chars(text):
            issues.append("包含控制字符或特殊字符，可能影响文本处理")

        # 检测连续空白
        if re.search(r'\s{10,}', text):
            issues.append("包含大量连续空白字符")

        return issues

    def check_embedding_compatibility(
        self,
        text: str,
        embeddings_manager: Any,
        max_test_length: int = 1000
    ) -> Dict[str, Any]:
        """
        检查文本与嵌入模型的兼容性

        通过实际调用嵌入模型来验证兼容性。

        Args:
            text: 要检查的文本
            embeddings_manager: 嵌入管理器实例
            max_test_length: 测试文本的最大长度

        Returns:
            兼容性检查结果字典，包含：
            - compatible: 是否兼容
            - vector_dim: 向量维度
            - embedding_time: 嵌入生成时间（秒）
            - issues: 问题列表
            - test_text_length: 测试文本长度

        Raises:
            ValueError: 如果text为空或embeddings_manager无效
        """
        if not text:
            raise ValueError("文本不能为空")

        if embeddings_manager is None:
            raise ValueError("embeddings_manager不能为None")

        logger.debug("开始检查嵌入兼容性")

        # 截取测试文本（避免过长）
        test_text = text[:max_test_length] if len(text) > max_test_length else text
        test_text_length = len(test_text)

        issues = []
        compatible = True
        vector_dim = None
        embedding_time = None

        try:
            # 尝试生成嵌入
            start_time = time.time()
            
            # 检查embeddings_manager是否有embed_query方法
            if hasattr(embeddings_manager, 'embed_query'):
                vector = embeddings_manager.embed_query(test_text)
            elif hasattr(embeddings_manager, 'embeddings') and hasattr(embeddings_manager.embeddings, 'embed_query'):
                vector = embeddings_manager.embeddings.embed_query(test_text)
            else:
                raise AttributeError("embeddings_manager没有embed_query方法")
            
            embedding_time = time.time() - start_time
            vector_dim = len(vector) if vector else None

            logger.debug(
                f"嵌入生成成功: 维度={vector_dim}, 耗时={embedding_time:.3f}秒"
            )

            # 检查向量维度
            if vector_dim is None or vector_dim == 0:
                issues.append("生成的向量维度无效")
                compatible = False

            # 检查生成时间
            if embedding_time > 10:
                issues.append(
                    f"嵌入生成时间过长 ({embedding_time:.2f}秒)，"
                    "可能需要优化文本长度"
                )

            # 检查向量值
            if vector and all(v == 0 for v in vector):
                issues.append("生成的向量全为0，可能存在问题")
                compatible = False

        except Exception as e:
            logger.error(f"嵌入兼容性检查失败: {e}", exc_info=True)
            issues.append(f"嵌入生成失败: {str(e)}")
            compatible = False

        result = {
            'compatible': compatible,
            'vector_dim': vector_dim,
            'embedding_time': embedding_time,
            'issues': issues,
            'test_text_length': test_text_length
        }

        logger.debug(f"兼容性检查完成: {result}")
        return result

    def generate_report(
        self,
        text: str,
        embeddings_manager: Optional[Any] = None
    ) -> str:
        """
        生成完整的诊断报告

        Args:
            text: 要诊断的文本
            embeddings_manager: 可选的嵌入管理器，用于兼容性检查

        Returns:
            格式化的诊断报告字符串
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("中文文本诊断报告")
        report_lines.append("=" * 60)
        report_lines.append("")

        # 文本分析
        analysis = self.analyze_text(text)
        
        report_lines.append("文本统计:")
        report_lines.append(f"  - 总字符数: {analysis['char_count']}")
        report_lines.append(f"  - 中文字符数: {analysis['chinese_char_count']}")
        report_lines.append(f"  - 中文占比: {analysis['chinese_ratio']:.1%}")
        report_lines.append(f"  - 词数（估算）: {analysis['word_count']}")
        report_lines.append(f"  - 句子数: {analysis['sentence_count']}")
        report_lines.append(f"  - 编码: {analysis['encoding']}")
        report_lines.append(f"  - 包含特殊字符: {'是' if analysis['has_special_chars'] else '否'}")
        report_lines.append("")

        # 潜在问题
        if analysis['potential_issues']:
            report_lines.append("潜在问题:")
            for issue in analysis['potential_issues']:
                report_lines.append(f"  ⚠ {issue}")
            report_lines.append("")
        else:
            report_lines.append("✓ 未发现明显问题")
            report_lines.append("")

        # 嵌入兼容性检查
        if embeddings_manager:
            report_lines.append("嵌入兼容性检查:")
            try:
                compat = self.check_embedding_compatibility(text, embeddings_manager)
                
                report_lines.append(f"  - 兼容性: {'✓ 兼容' if compat['compatible'] else '✗ 不兼容'}")
                if compat['vector_dim']:
                    report_lines.append(f"  - 向量维度: {compat['vector_dim']}")
                if compat['embedding_time']:
                    report_lines.append(f"  - 生成时间: {compat['embedding_time']:.3f}秒")
                report_lines.append(f"  - 测试文本长度: {compat['test_text_length']} 字符")
                
                if compat['issues']:
                    report_lines.append("  问题:")
                    for issue in compat['issues']:
                        report_lines.append(f"    ⚠ {issue}")
                
            except Exception as e:
                report_lines.append(f"  ✗ 检查失败: {e}")
            
            report_lines.append("")

        # 建议
        report_lines.append("建议:")
        if analysis['chinese_ratio'] > 0.5:
            report_lines.append("  ✓ 建议使用ChineseTextSplitter进行分块")
        else:
            report_lines.append("  ✓ 建议使用RecursiveSplitter进行分块")
        
        if analysis['char_count'] > 5000:
            report_lines.append("  ✓ 文本较长，建议使用较小的chunk_size")
        
        report_lines.append("")
        report_lines.append("=" * 60)

        return "\n".join(report_lines)
