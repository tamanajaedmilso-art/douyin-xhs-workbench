import re
from typing import Dict, List


class ContentAnalyzer:
    """爆款文案结构拆解器"""

    # 引导话术关键词
    CTA_KEYWORDS = [
        "扣1", "扣 1", "扣一", "私信", "评论区", "留言", "点左下角",
        "戳左下角", "点击主页", "看我主页", "进群", "加群", "添加",
        "关注", "点赞收藏", "收藏转发", "转发给", "分享给你",
        "想要的", "想了解", "有问必答", "滴滴", "s我"
    ]

    # 结尾转化关键词
    ENDING_KEYWORDS = [
        "有问题", "不懂就问", "欢迎", "下期", "持续更新", "记得",
        "赶紧", "千万别错过", "行动起来", "行动起来", "祝你"
    ]

    # 痛点/情绪词
    PAIN_KEYWORDS = [
        "焦虑", "崩溃", "自卑", "烦恼", "痛苦", "难受", "担心",
        "害怕", "恐惧", "迷茫", "纠结", "后悔", "失望", "累",
        "内耗", "熬夜", "暗沉", "松弛", "下垂", "凹陷", "皱纹",
        "失败", "反复", " expensive", "贵", "坑", "踩坑", "智商税"
    ]

    def __init__(self):
        pass

    def split_sentences(self, text: str) -> List[str]:
        """按中文句号/感叹号/问号/换行拆分句子"""
        if not text:
            return []
        parts = re.split(r"[。！？\n]+", text)
        return [p.strip() for p in parts if p.strip()]

    def extract_hook_and_pain(self, text: str) -> str:
        """提取钩子/痛点：前 1-2 句"""
        sentences = self.split_sentences(text)
        if not sentences:
            return ""
        # 取前两句，或第一句较长则只取第一句
        if len(sentences) >= 2 and len(sentences[0]) < 20:
            return sentences[0] + "。" + sentences[1]
        return sentences[0]

    def extract_value_output(self, text: str) -> str:
        """提取价值输出：中间核心段落（去掉首尾）"""
        sentences = self.split_sentences(text)
        if len(sentences) <= 2:
            return text
        return "。".join(sentences[1:-1])

    def extract_guidance(self, text: str) -> str:
        """提取引导话术：包含 CTA 关键词的句子"""
        sentences = self.split_sentences(text)
        result = []
        for s in sentences:
            for kw in self.CTA_KEYWORDS:
                if kw in s:
                    result.append(s)
                    break
        return "；".join(result)

    def extract_ending(self, text: str) -> str:
        """提取结尾转化：最后 1-2 句，或含结尾关键词的句子"""
        sentences = self.split_sentences(text)
        if not sentences:
            return ""
        # 优先返回最后一句
        last = sentences[-1]
        # 如果倒数第二句含结尾关键词，也加入
        if len(sentences) >= 2:
            second_last = sentences[-2]
            for kw in self.ENDING_KEYWORDS:
                if kw in second_last:
                    return second_last + "。" + last
        return last

    def analyze(self, text: str) -> Dict[str, str]:
        """拆解一条文案，返回结构字典"""
        return {
            "hook_pain": self.extract_hook_and_pain(text),
            "value_output": self.extract_value_output(text),
            "guidance": self.extract_guidance(text),
            "ending": self.extract_ending(text),
        }

    def batch_analyze(self, items: List[Dict]) -> List[Dict]:
        """批量拆解"""
        for item in items:
            text = item.get("content", "") or item.get("title", "") or ""
            item["structure"] = self.analyze(text)
        return items
