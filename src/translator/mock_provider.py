"""Mock LLM Provider for testing when real providers aren't available"""

from typing import Optional
from .base import LLMProvider

class MockLLMProvider(LLMProvider):
    """Mock LLM provider that simulates translation without external dependencies"""

    def __init__(self, provider_name: str, model: str):
        self.provider_name = provider_name
        self.model = model

    def translate(self, text: str, source_lang: str = "zh", target_lang: str = "en") -> str:
        """
        Mock translation/rewrite - handle both translation and rewriting scenarios
        """
        # Handle Chinese to Chinese rewriting
        if source_lang == "zh" and target_lang == "zh":
            # Handle translation-oriented prompt format ending with "改写后："
            if text.endswith("改写后："):
                # Extract the content before "改写后：" to find the original text
                content_section = text[:-4]  # Remove "改写后："

                # Look for "原文：" or content markers to extract the text to rewrite
                if "原文：" in content_section:
                    lines = content_section.split('\n')
                    original_content = ""
                    found_original = False
                    for line in lines:
                        if "原文：" in line:
                            original_content = line.split("原文：", 1)[-1].strip()
                            found_original = True
                        elif found_original and line.strip() and not line.strip().startswith('改写后：'):
                            # Continue capturing content if it spans multiple lines
                            original_content += line.strip()
                        elif line.strip().startswith('改写后：'):
                            break
                else:
                    # Try to find the last substantial line before "改写后："
                    lines = content_section.split('\n')
                    content_lines = []
                    for line in lines:
                        line_stripped = line.strip()
                        if (line_stripped and
                            not line_stripped.startswith('-') and
                            not any(marker in line_stripped for marker in [
                                '改写原则：', '约束条件：', '上下文信息：', '内容类型：',
                                '文档意图：', '目标读者：', '专业领域：', '语气风格：'
                            ])):
                            content_lines.append(line_stripped)

                    original_content = content_lines[-1] if content_lines else ""

                if original_content:
                    # Apply comprehensive rewrite rules
                    return self._rewrite_content(original_content)
                else:
                    # Fallback: try to extract from the full text before context information
                    lines = content_section.split('\n')
                    for line in reversed(lines):  # Start from the end
                        line_stripped = line.strip()
                        if (line_stripped and
                            not any(marker in line_stripped for marker in [
                                '改写原则：', '约束条件：', '常见优化规则：', '上下文信息：',
                                '文档意图：', '目标读者：', '专业领域：', '语气风格：',
                                '内容类型：', '前后文参考：', '原文：'
                            ]) and
                            not line_stripped.endswith('：') and
                            len(line_stripped) > 5):  # Reasonable content length
                            return self._rewrite_content(line_stripped)

                    return "改写后的内容"
            # Apply translation-oriented rules first
            if "更适合机器翻译" in text:
                # Extract content for translation optimization - handle multiple formats
                lines = text.split('\n')
                content_start = -1
                content_marker = None

                # Look for content markers
                for i, line in enumerate(lines):
                    if "原文：" in line:
                        content_start = i + 1
                        content_marker = "原文："
                        break
                    elif "原内容：" in line:
                        content_start = i + 1
                        content_marker = "原内容："
                        break

                if content_start >= 0 and content_start < len(lines):
                    original_content = lines[content_start].strip()
                    if original_content:
                        # Enhanced translation-oriented rewriting rules
                        translation_rules = {
                            # Basic rhetorical expressions
                            "事半功倍": "显著提高效率",
                            "面面俱到": "全面覆盖",
                            "一石二鸟": "同时支持两种功能",
                            "总而言之": "总结来说",
                            "众所周知": "众所周知",
                            "由于种种原因": "由于多种原因",

                            # System and performance descriptions
                            "深受用户喜爱": "获得用户广泛认可",
                            "非常强大的系统": "功能强大的系统",
                            "能够处理海量的文本数据": "可以处理大量文本数据",
                            "具有广阔的应用前景": "有很大的应用潜力",
                            "性能卓越": "性能出色",

                            # Common patterns
                            "不仅...而且...": "且",
                            "不仅...还": "且",
                            "本文档主要介绍了": "本文档介绍了",
                            "我们开发了": "我们开发了",

                            # Simplifications
                            "智能化算法": "智能算法",
                            "显著提升": "大幅提升",
                            "各种应用场景": "所有应用场景"
                        }

                        # Apply translation rules with context-aware replacement
                        optimized_content = original_content

                        # Replace patterns first
                        optimized_content = optimized_content.replace("不仅", "且").replace("，还", "，且")

                        # Apply word-level rules
                        for original, rewritten in translation_rules.items():
                            optimized_content = optimized_content.replace(original, rewritten)

                        return optimized_content
                else:
                    # Fallback - return simple optimization message
                    return "优化后的内容"

            # Also handle simple prompt format without markers
            if "改写后：" in text and "原文：" not in text and "原内容：" not in text:
                # Extract the last non-empty line before "改写后："
                lines = text.split('\n')
                content_lines = []
                for line in lines:
                    if "改写后：" in line:
                        break
                    if line.strip():
                        content_lines.append(line.strip())

                if content_lines:
                    original_content = content_lines[-1]  # Last line before "改写后："

                    # Enhanced rules for personal narrative content
                    personal_narrative_rules = {
                        # Basic optimization rules
                        "事半功倍": "显著提高效率",
                        "面面俱到": "全面覆盖",
                        "一石二鸟": "同时支持两种功能",
                        "总而言之": "总结来说",
                        "深受用户喜爱": "获得用户广泛认可",

                        # Personal narrative specific rules
                        "众所周知": "众所周知",
                        "由于种种原因": "由于多种原因",
                        "手头宽裕就放开花钱": "经济宽裕时增加支出",
                        "这并不是说我完全失去了理智": "这并不意味着完全失去理智",
                        "更容易掏出钱包": "更愿意花钱",
                        "尽情地享受": "充分享受",
                        "零碎的、随意的、不必要的小额支出": "零散的、不必要的支出",
                        "并没有真正提升我的生活质量": "没有实质提升生活质量",
                        "大手笔的奢侈消费": "大额奢侈消费",

                        # Experience and reflection rules
                        "让我觉得自己恢复了一定的社会地位": "让我恢复了社会地位感",
                        "理所当然地'奢侈'一些": "可以适度'奢侈'",
                        "掌控金钱的快感": "控制金钱的满足感",
                        "暂时跳出了消费主义的圈子": "暂时脱离消费主义模式",
                        "回到了正常的消费模式": "恢复正常消费方式",

                        # Work and career rules
                        "我又回到了职场": "我重返职场",
                        "找到了一份高薪工作": "获得了一份高薪工作",
                        "生活终于回归正常": "生活恢复正常",
                        "朝九晚五的节奏": "规律的工作节奏",
                        "收到这份工作的录用通知": "收到工作录用通知",
                        "重新回归高薪职业": "重新从事高薪职业",

                        # Personal finance rules
                        "花钱方面明显变得随意了许多": "消费变得更加随意",
                        "更容易掏出钱包": "更愿意消费",
                        "大手笔的奢侈消费": "大额奢侈消费",
                        "零碎的、随意的、不必要的小额支出": "零散的、不必要的小额支出",
                        "手头宽裕就放开花钱": "经济宽裕时增加支出",
                        "这并不是说我完全失去了理智": "这并不意味着完全失去理智",

                        # Travel experience rules
                        "最惊讶的发现之一": "最令人惊讶的发现之一",
                        "每个月的花费比在国内...要少得多": "每月花费比国内...少很多",
                        "认识了许多新朋友": "认识了很多新朋友",
                        "心态平和": "心态平静",
                        "度过了一段难忘的时光": "度过了一段难忘的经历",
                        "每一分钱都能换取更多的价值": "每分钱都能获得更高价值",
                        "物价最低的城市": "物价最低的城市",

                        # Lifestyle comparison rules
                        "在国外旅行时": "在国外旅行期间",
                        "当一名普通上班族时": "作为普通上班族时",
                        "比加拿大物价更高的国家": "物价高于加拿大的国家",
                        "去世界上许多美丽的地方": "前往世界各地许多美丽的地方",
                        "结识了无数新朋友": "认识了许多新朋友"
                    }

                    # Apply personal narrative rules first
                    optimized_content = original_content
                    for original, rewritten in personal_narrative_rules.items():
                        optimized_content = optimized_content.replace(original, rewritten)

                    # Apply basic rules as fallback
                    basic_rules = {
                        "非常强大的系统": "功能强大的系统",
                        "海量的文本数据": "大量文本数据",
                        "不仅性能卓越，而且易于使用": "性能卓越且易于使用"
                    }

                    for original, rewritten in basic_rules.items():
                        if original in optimized_content:  # Only apply if not already replaced
                            optimized_content = optimized_content.replace(original, rewritten)

                    return optimized_content

            # Enhanced mock rewriting for Chinese text with personal narrative focus
            rewrite_rules = {
                # General document improvements
                "这是一个非常好的文档": "这是一份卓越的文档",
                "我们一般会写一些比较重要的内容": "笔者通常会撰写若干至关重要的内容",
                "这个功能很不错": "该功能表现优异",
                "大家都应该使用": "各位应当采纳使用",

                # Personal narrative optimizations based on the user's document
                "由于之前我外出旅行的生活方式截然不同": "由于之前旅行生活方式的差异",
                "让我察觉到一些以前忽略的事情": "让我注意到以前忽略的事情",
                "经过九个月的旅行后": "经过九个月的旅行",
                "远不如新西兰的馥芮白美味": "不如新西兰的馥芮白美味",
                "悠闲地坐在阳光明媚的咖啡馆露台上慢慢品味": "在阳光明媚的咖啡馆露台悠闲品味",
                "并没有真正提升我的生活质量": "没有实质提升生活质量",
                "回顾以往": "回顾过去",
                "经历了九个月没有收入的背包客生活后": "经历九个月无收入的背包客生活后",
                "不禁对这种现象更加留意了": "对这种现象更加关注",
                "花钱的那一刻": "消费时",
                "尤其是当你知道这些钱很快又会赚回来时": "特别是当知道这些钱很快能赚回来时",
                "几乎所有人都在这样做": "大多数人都是这样",
                "换句话说": "也就是说",
                "为什么呢？": "原因是什么？"
            }

            # Apply rewrite rules if matched
            for original, rewritten in rewrite_rules.items():
                if original in text:
                    return text.replace(original, rewritten)

            # If no rule matches, return a mock rewrite
            if "请改写以下中文句子" in text and "原句：" in text:
                # Extract the original sentence from the prompt
                lines = text.split('\n')
                for line in lines:
                    if line.startswith("原句："):
                        original_sentence = line.replace("原句：", "").strip()
                        return f"{original_sentence}（经过AI优化改写）"

            return text + " [Mock改写]"

        # Handle Chinese to English translation
        elif source_lang == "zh" and target_lang == "en":
            return f"[MOCK Translation of {len(text)} characters from {self.model}]"

        # Default: return text unchanged
        return text

    def _rewrite_content(self, original_content: str) -> str:
        """Apply comprehensive rewrite rules to content."""
        # Enhanced translation-oriented rewriting rules
        translation_rules = {
            # Basic rhetorical expressions
            "事半功倍": "显著提高效率",
            "面面俱到": "全面覆盖",
            "一石二鸟": "同时支持两种功能",
            "总而言之": "总结来说",
            "众所周知": "众所周知",
            "由于种种原因": "由于多种原因",

            # System and performance descriptions
            "深受用户喜爱": "获得用户广泛认可",
            "非常强大的系统": "功能强大的系统",
            "能够处理海量的文本数据": "可以处理大量文本数据",
            "具有广阔的应用前景": "有很大的应用潜力",
            "性能卓越": "性能出色",

            # Common patterns
            "不仅...而且...": "且",
            "不仅...还": "且",
            "本文档主要介绍了": "本文档介绍了",
            "我们开发了": "我们开发了",

            # Simplifications
            "智能化算法": "智能算法",
            "显著提升": "大幅提升",
            "各种应用场景": "所有应用场景",

            # Work and career rules
            "我又回到了职场": "我重返职场",
            "找到了一份高薪工作": "获得了一份高薪工作",
            "生活终于回归正常": "生活恢复正常",
            "朝九晚五的节奏": "规律的工作节奏",
            "收到这份工作的录用通知": "收到工作录用通知",
            "重新回归高薪职业": "重新从事高薪职业",

            # Personal finance rules
            "花钱方面明显变得随意了许多": "消费变得更加随意",
            "更容易掏出钱包": "更愿意消费",
            "大手笔的奢侈消费": "大额奢侈消费",
            "零碎的、随意的、不必要的小额支出": "零散的、不必要的小额支出",
            "手头宽裕就放开花钱": "经济宽裕时增加支出",
            "这并不是说我完全失去了理智": "这并不意味着完全失去理智",

            # Travel experience rules
            "最惊讶的发现之一": "最令人惊讶的发现之一",
            "每个月的花费比在国内...要少得多": "每月花费比国内...少很多",
            "认识了许多新朋友": "认识了很多新朋友",
            "心态平和": "心态平静",
            "度过了一段难忘的时光": "度过了一段难忘的经历",
            "每一分钱都能换取更多的价值": "每分钱都能获得更高价值",
            "物价最低的城市": "物价最低的城市",

            # Lifestyle comparison rules
            "在国外旅行时": "在国外旅行期间",
            "当一名普通上班族时": "作为普通上班族时",
            "比加拿大物价更高的国家": "物价高于加拿大的国家",
            "去世界上许多美丽的地方": "前往世界各地许多美丽的地方",
            "结识了无数新朋友": "认识了许多新朋友",

            # Personal narrative optimizations based on the user's document
            "由于之前我外出旅行的生活方式截然不同": "由于之前旅行生活方式的差异",
            "让我察觉到一些以前忽略的事情": "让我注意到以前忽略的事情",
            "经过九个月的旅行后": "经过九个月的旅行",
            "远不如新西兰的馥芮白美味": "不如新西兰的馥芮白美味",
            "悠闲地坐在阳光明媚的咖啡馆露台上慢慢品味": "在阳光明媚的咖啡馆露台悠闲品味",
            "并没有真正提升我的生活质量": "没有实质提升生活质量",
            "回顾以往": "回顾过去",
            "经历了九个月没有收入的背包客生活后": "经历九个月无收入的背包客生活后",
            "不禁对这种现象更加留意了": "对这种现象更加关注",
            "花钱的那一刻": "消费时",
            "尤其是当你知道这些钱很快又会赚回来时": "特别是当知道这些钱很快能赚回来时",
            "几乎所有人都在这样做": "大多数人都是这样",
            "换句话说": "也就是说",
            "为什么呢？": "原因是什么？"
        }

        # Apply translation rules with context-aware replacement
        optimized_content = original_content

        # Replace patterns first
        optimized_content = optimized_content.replace("不仅", "且").replace("，还", "，且")

        # Apply word-level rules
        for original, rewritten in translation_rules.items():
            optimized_content = optimized_content.replace(original, rewritten)

        # Clean up any context information that might have been included
        # Remove context patterns that might appear in the output
        context_patterns = [
            r'上下文信息：.*',
            r'文档意图：.*',
            r'目标读者：.*',
            r'专业领域：.*',
            r'语气风格：.*',
            r'内容类型：.*',
            r'前后文参考：.*'
        ]

        import re
        for pattern in context_patterns:
            optimized_content = re.sub(pattern, '', optimized_content, flags=re.MULTILINE)

        return optimized_content.strip()

    def is_configured(self) -> bool:
        """Mock provider is always configured"""
        return True

    def get_name(self) -> str:
        """Get the provider name"""
        return self.provider_name