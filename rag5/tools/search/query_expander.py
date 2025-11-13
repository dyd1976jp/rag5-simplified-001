"""
查询扩展器模块

提供查询扩展功能，通过提取关键词、添加同义词等方式扩展查询，提高检索召回率。
"""

import logging
import re
from typing import List, Set, Dict, Any, Optional

logger = logging.getLogger(__name__)


class QueryExpander:
    """
    查询扩展器
    
    扩展用户查询以提高检索召回率，通过以下方式：
    1. 提取关键实体和关键词
    2. 添加同义词和相关词
    3. 扩展缩写和简称
    4. 添加上下文信息
    
    示例:
        >>> from rag5.tools.search import QueryExpander
        >>> 
        >>> expander = QueryExpander()
        >>> expanded = expander.expand_query("于朦朧是怎么死的")
        >>> print(expanded)
        "于朦朧是怎么死的 于朦朧 死亡 去世 逝世 死因"
    """
    
    def __init__(
        self,
        enable_synonyms: bool = True,
        enable_entity_extraction: bool = True,
        max_expansion_ratio: float = 2.0
    ):
        """
        初始化查询扩展器
        
        参数:
            enable_synonyms: 是否启用同义词扩展
            enable_entity_extraction: 是否启用实体提取
            max_expansion_ratio: 最大扩展比例（扩展后长度/原始长度）
        """
        self.enable_synonyms = enable_synonyms
        self.enable_entity_extraction = enable_entity_extraction
        self.max_expansion_ratio = max_expansion_ratio
        
        # 预定义的同义词词典（可以扩展）
        self.synonym_dict = self._build_synonym_dict()
        
        logger.debug(
            f"初始化查询扩展器: "
            f"同义词={enable_synonyms}, "
            f"实体提取={enable_entity_extraction}, "
            f"最大扩展比例={max_expansion_ratio}"
        )
    
    def expand_query(
        self,
        query: str,
        context: Optional[str] = None
    ) -> str:
        """
        扩展查询以提高召回率
        
        参数:
            query: 原始查询文本
            context: 可选的上下文信息
        
        返回:
            扩展后的查询文本
        
        示例:
            >>> expander = QueryExpander()
            >>> expanded = expander.expand_query("于朦朧怎么死的")
            >>> print(expanded)
        """
        if not query or not query.strip():
            logger.warning("收到空查询，无法扩展")
            return query
        
        logger.info("=" * 60)
        logger.info("开始查询扩展")
        logger.info(f"原始查询: {query}")
        logger.info(f"查询长度: {len(query)} 字符")
        if context:
            logger.info(f"上下文: {context[:100]}...")
        logger.info("=" * 60)
        
        # 收集扩展词
        expansion_terms = set()
        
        # 1. 提取关键词
        if self.enable_entity_extraction:
            logger.info("\n[步骤 1/3] 提取关键词...")
            keywords = self._extract_keywords(query)
            expansion_terms.update(keywords)
            logger.info(f"✓ 提取到 {len(keywords)} 个关键词: {list(keywords)[:5]}")
        
        # 2. 获取同义词
        if self.enable_synonyms:
            logger.info("\n[步骤 2/3] 获取同义词...")
            synonyms = self._get_synonyms(query, expansion_terms)
            expansion_terms.update(synonyms)
            logger.info(f"✓ 找到 {len(synonyms)} 个同义词: {list(synonyms)[:5]}")
        
        # 3. 添加上下文词
        if context:
            logger.info("\n[步骤 3/3] 提取上下文关键词...")
            context_keywords = self._extract_keywords(context)
            # 只添加与查询相关的上下文词
            relevant_context = self._filter_relevant_terms(
                query, context_keywords, max_terms=3
            )
            expansion_terms.update(relevant_context)
            logger.info(f"✓ 添加 {len(relevant_context)} 个上下文词: {list(relevant_context)}")
        
        # 构建扩展查询
        expanded_query = self._build_expanded_query(
            original_query=query,
            expansion_terms=expansion_terms
        )
        
        logger.info("\n" + "=" * 60)
        logger.info("查询扩展完成")
        logger.info(f"扩展后查询: {expanded_query}")
        logger.info(f"扩展后长度: {len(expanded_query)} 字符")
        logger.info(f"扩展比例: {len(expanded_query) / len(query):.2f}x")
        logger.info("=" * 60)
        
        return expanded_query
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """
        从文本中提取关键词
        
        参数:
            text: 输入文本
        
        返回:
            关键词集合
        """
        keywords = set()
        
        # 提取中文词组（2-4个字符）
        chinese_patterns = [
            r'[\u4e00-\u9fff]{2,4}',  # 2-4个中文字符
        ]
        
        for pattern in chinese_patterns:
            matches = re.findall(pattern, text)
            keywords.update(matches)
        
        # 提取英文单词（3个字符以上）
        english_words = re.findall(r'[a-zA-Z]{3,}', text)
        keywords.update(w.lower() for w in english_words)
        
        # 提取数字
        numbers = re.findall(r'\d+', text)
        keywords.update(numbers)
        
        # 过滤停用词
        keywords = self._filter_stopwords(keywords)
        
        logger.debug(f"提取关键词: {len(keywords)} 个")
        return keywords
    
    def _get_synonyms(
        self,
        query: str,
        keywords: Set[str]
    ) -> Set[str]:
        """
        获取查询和关键词的同义词
        
        参数:
            query: 原始查询
            keywords: 关键词集合
        
        返回:
            同义词集合
        """
        synonyms = set()
        
        # 检查查询中的词是否有同义词
        for word, synonym_list in self.synonym_dict.items():
            if word in query or word in keywords:
                synonyms.update(synonym_list)
                logger.debug(f"找到同义词: {word} -> {synonym_list}")
        
        return synonyms
    
    def _filter_relevant_terms(
        self,
        query: str,
        terms: Set[str],
        max_terms: int = 3
    ) -> Set[str]:
        """
        过滤出与查询相关的词
        
        参数:
            query: 查询文本
            terms: 候选词集合
            max_terms: 最大返回词数
        
        返回:
            相关词集合
        """
        # 简单实现：返回在查询中出现的词或与查询词相似的词
        relevant = set()
        query_lower = query.lower()
        
        for term in terms:
            term_lower = term.lower()
            # 检查是否在查询中
            if term_lower in query_lower or query_lower in term_lower:
                relevant.add(term)
                if len(relevant) >= max_terms:
                    break
        
        return relevant
    
    def _build_expanded_query(
        self,
        original_query: str,
        expansion_terms: Set[str]
    ) -> str:
        """
        构建扩展后的查询
        
        参数:
            original_query: 原始查询
            expansion_terms: 扩展词集合
        
        返回:
            扩展后的查询字符串
        """
        # 移除已经在原始查询中的词
        unique_terms = set()
        original_lower = original_query.lower()
        
        for term in expansion_terms:
            if term.lower() not in original_lower:
                unique_terms.add(term)
        
        # 限制扩展长度
        max_length = int(len(original_query) * self.max_expansion_ratio)
        
        # 按词长度排序（优先添加较长的词）
        sorted_terms = sorted(unique_terms, key=len, reverse=True)
        
        # 构建扩展查询
        expanded_parts = [original_query]
        current_length = len(original_query)
        
        for term in sorted_terms:
            if current_length + len(term) + 1 <= max_length:
                expanded_parts.append(term)
                current_length += len(term) + 1
            else:
                break
        
        expanded_query = " ".join(expanded_parts)
        
        logger.debug(
            f"构建扩展查询: 原始={len(original_query)}字符, "
            f"扩展={len(expanded_query)}字符, "
            f"添加了{len(expanded_parts)-1}个词"
        )
        
        return expanded_query
    
    def _filter_stopwords(self, keywords: Set[str]) -> Set[str]:
        """
        过滤停用词
        
        参数:
            keywords: 关键词集合
        
        返回:
            过滤后的关键词集合
        """
        # 中文停用词列表（简化版）
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '那',
            '什么', '怎么', '为什么', '哪里', '谁', '吗', '呢', '吧',
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or',
            'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by'
        }
        
        filtered = {kw for kw in keywords if kw.lower() not in stopwords}
        
        if len(filtered) < len(keywords):
            logger.debug(f"过滤停用词: {len(keywords)} -> {len(filtered)}")
        
        return filtered
    
    def _build_synonym_dict(self) -> Dict[str, List[str]]:
        """
        构建同义词词典
        
        返回:
            同义词词典
        """
        # 预定义的同义词词典（可以根据需要扩展）
        synonym_dict = {
            # 死亡相关
            '死': ['去世', '逝世', '离世', '过世', '身亡', '死亡'],
            '去世': ['死', '逝世', '离世', '过世', '身亡'],
            '逝世': ['死', '去世', '离世', '过世', '身亡'],
            
            # 原因相关
            '原因': ['缘由', '理由', '因素', '起因'],
            '为什么': ['原因', '缘由', '怎么'],
            '怎么': ['如何', '怎样', '为什么'],
            
            # 时间相关
            '时间': ['日期', '时候', '何时'],
            '什么时候': ['何时', '时间', '日期'],
            
            # 地点相关
            '地方': ['地点', '位置', '场所'],
            '哪里': ['何处', '地方', '地点'],
            
            # 人物相关
            '人': ['人物', '角色', '人士'],
            '谁': ['何人', '什么人'],
            
            # 事件相关
            '事情': ['事件', '情况', '事故'],
            '发生': ['出现', '产生', '造成'],
            
            # 公司相关
            '公司': ['企业', '机构', '组织', '单位'],
            '合作': ['协作', '联合', '配合'],
            '投资': ['入股', '注资', '融资'],
            
            # 其他常用词
            '信息': ['资料', '数据', '内容'],
            '详细': ['具体', '详尽', '细致'],
            '介绍': ['说明', '描述', '讲解'],
        }
        
        return synonym_dict
    
    def add_synonyms(self, word: str, synonyms: List[str]) -> None:
        """
        添加自定义同义词
        
        参数:
            word: 词语
            synonyms: 同义词列表
        
        示例:
            >>> expander = QueryExpander()
            >>> expander.add_synonyms("AI", ["人工智能", "机器学习"])
        """
        if word in self.synonym_dict:
            self.synonym_dict[word].extend(synonyms)
        else:
            self.synonym_dict[word] = synonyms
        
        logger.debug(f"添加同义词: {word} -> {synonyms}")
    
    def get_expansion_statistics(
        self,
        queries: List[str]
    ) -> Dict[str, Any]:
        """
        获取查询扩展统计信息
        
        用于分析和调试，了解查询扩展的效果。
        
        参数:
            queries: 查询列表
        
        返回:
            统计信息字典
        
        示例:
            >>> expander = QueryExpander()
            >>> stats = expander.get_expansion_statistics([
            ...     "于朦朧是怎么死的",
            ...     "李小勇的公司"
            ... ])
            >>> print(f"平均扩展比例: {stats['avg_expansion_ratio']:.2f}")
        """
        logger.info(f"获取查询扩展统计信息: {len(queries)} 个查询")
        
        statistics = {
            "total_queries": len(queries),
            "expansions": [],
            "avg_expansion_ratio": 0.0,
            "avg_terms_added": 0.0
        }
        
        total_ratio = 0.0
        total_terms = 0
        
        for query in queries:
            original_length = len(query)
            expanded = self.expand_query(query)
            expanded_length = len(expanded)
            
            # 计算添加的词数
            original_words = set(query.split())
            expanded_words = set(expanded.split())
            terms_added = len(expanded_words - original_words)
            
            expansion_ratio = expanded_length / original_length if original_length > 0 else 1.0
            
            statistics["expansions"].append({
                "original": query,
                "expanded": expanded,
                "original_length": original_length,
                "expanded_length": expanded_length,
                "expansion_ratio": expansion_ratio,
                "terms_added": terms_added
            })
            
            total_ratio += expansion_ratio
            total_terms += terms_added
        
        if len(queries) > 0:
            statistics["avg_expansion_ratio"] = total_ratio / len(queries)
            statistics["avg_terms_added"] = total_terms / len(queries)
        
        logger.info(
            f"统计完成: 平均扩展比例={statistics['avg_expansion_ratio']:.2f}, "
            f"平均添加词数={statistics['avg_terms_added']:.1f}"
        )
        
        return statistics
