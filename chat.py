"""
知识图谱问答系统 - 命令行界面
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.qa.qa_system import QASystem


def main():
    print("\n" + "=" * 70)
    print("🤖 MSI-HBP 中医知识图谱问答系统")
    print("=" * 70)
    
    print("\n正在初始化...")
    qa = QASystem(use_neo4j=False)
    
    print("\n" + "=" * 70)
    print("✅ 系统已就绪！")
    print("=" * 70)
    
    print("\n💡 使用说明:")
    print("  - 输入问题，按回车获取答案")
    print("  - 输入 'exit' 或 'quit' 退出")
    print("  - 输入 'examples' 查看示例问题")
    print()
    
    # 示例问题
    examples = [
        "精神应激性高血压有什么症状？",
        "肝阳上亢怎么治疗？",
        "天麻钩藤饮的作用是什么？",
        "失眠和高血压有什么关系？",
        "什么中药可以治疗焦虑？",
        "平肝潜阳的方法有哪些？",
        "高血压的病机是什么？",
        "逍遥散由什么组成？"
    ]
    
    while True:
        try:
            # 获取用户输入
            question = input("🙋 请输入问题: ").strip()
            
            if not question:
                continue
            
            # 退出命令
            if question.lower() in ['exit', 'quit', '退出', 'q']:
                print("\n👋 再见！")
                break
            
            # 显示示例
            if question.lower() in ['examples', '示例', 'help', '帮助']:
                print("\n📝 示例问题:")
                for i, ex in enumerate(examples, 1):
                    print(f"  {i}. {ex}")
                print()
                continue
            
            # 回答问题
            print("\n🤔 正在思考...")
            result = qa.answer(question)
            
            print(f"\n💬 答案:")
            print(f"  {result['answer']}")
            
            # 显示相关知识
            if result['knowledge']:
                print(f"\n📚 相关知识:")
                for i, k in enumerate(result['knowledge'][:5], 1):
                    print(f"  {i}. {k['subject']} -[{k['relation']}]-> {k['object']}")
            
            print("\n" + "-" * 70 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 出错了: {e}")
            print()


if __name__ == "__main__":
    main()
