"""
LLM客户端模块
封装大语言模型调用接口
"""
import json
from typing import List, Dict, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from .config import config


class LLMClient:
    """LLM客户端类"""
    
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model_name: str = None,
        temperature: float = None
    ):
        """
        初始化LLM客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            model_name: 模型名称
            temperature: 温度参数
        """
        self.api_key = api_key or config.MODEL_API_KEY
        self.base_url = base_url or config.MODEL_BASE_URL
        self.model_name = model_name or config.MODEL_NAME
        self.temperature = config.MODEL_TEMPERATURE if temperature is None else temperature
        self.llm = None

    def _get_llm(self):
        """延迟初始化模型客户端，允许无密钥时使用非LLM功能。"""
        if not self.api_key:
            raise ValueError("MODEL_API_KEY未配置，智能问答和知识抽取功能不可用")

        if self.llm is None:
            self.llm = ChatOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model_name,
            temperature=self.temperature
            )
        return self.llm
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        对话接口
        
        Args:
            messages: 消息列表，格式：[{"role": "user", "content": "..."}]
            system_prompt: 系统提示词
        
        Returns:
            模型回复内容
        """
        formatted_messages = []
        
        # 添加系统提示词
        if system_prompt:
            formatted_messages.append(SystemMessage(content=system_prompt))
        
        # 转换消息格式
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                formatted_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                formatted_messages.append(AIMessage(content=content))
            else:
                formatted_messages.append(HumanMessage(content=content))
        
        # 调用LLM
        response = self._get_llm().invoke(formatted_messages)
        return response.content if hasattr(response, 'content') else str(response)
    
    def extract_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提取JSON格式的响应
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
        
        Returns:
            解析后的JSON对象
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.chat(messages, system_prompt)
        
        # 清理响应内容
        content = response.strip()
        
        # 移除markdown代码块标记
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            print(f"响应内容: {content[:500]}")
            return {}
    
    def batch_process(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        show_progress: bool = True
    ) -> List[str]:
        """
        批量处理提示词
        
        Args:
            prompts: 提示词列表
            system_prompt: 系统提示词
            show_progress: 是否显示进度条
        
        Returns:
            响应列表
        """
        results = []
        
        if show_progress:
            from tqdm import tqdm
            prompts = tqdm(prompts, desc="批量处理")
        
        for prompt in prompts:
            try:
                response = self.chat(
                    [{"role": "user", "content": prompt}],
                    system_prompt
                )
                results.append(response)
            except Exception as e:
                print(f"处理失败: {e}")
                results.append("")
        
        return results
    
    def validate_response(
        self,
        response: str,
        expected_keys: List[str] = None
    ) -> bool:
        """
        验证响应格式
        
        Args:
            response: 响应内容
            expected_keys: 期望的JSON键列表
        
        Returns:
            是否有效
        """
        try:
            data = json.loads(response)
            
            if expected_keys:
                return all(key in data for key in expected_keys)
            
            return True
        except:
            return False


# 创建全局LLM客户端实例
llm_client = LLMClient()


if __name__ == "__main__":
    # 测试LLM客户端
    client = LLMClient()
    
    # 测试对话
    response = client.chat([
        {"role": "user", "content": "你好，请介绍一下精神应激性高血压"}
    ])
    print("对话测试:")
    print(response)
    
    # 测试JSON提取
    prompt = """
    请从以下文本中抽取实体：
    "天麻钩藤饮可以治疗肝阳上亢引起的头痛"
    
    输出JSON格式：
    {
        "entities": [{"name": "实体名", "type": "实体类型"}],
        "relations": [{"subject": "主体", "relation": "关系", "object": "客体"}]
    }
    """
    
    result = client.extract_json(prompt)
    print("\nJSON提取测试:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
