from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os

# ===================== 1. 初始化核心组件（复用你的Ollama+Qwen-1.8B） =====================
# 初始化Ollama对接Qwen-1.8B（ollama run qwen:1.8b 已启动，直接调用）
llm = ChatOllama(
    model="qwen:1.8b",  # 你的本地模型名，Ollama中qwen:1.8b对应阿里Qwen-1.8B
    temperature=0.3,    # 代码生成温度，越低越严谨，越高越灵活
    max_tokens=2048     # 最大生成token，适配1.8B模型
)
# 初始化Ollama嵌入模型（用于代码文本向量化，对接Chroma，与Qwen同源，无需额外配置）
embeddings = OllamaEmbeddings(model="qwen:1.8b")
# 初始化对话历史存储（本地内存，简单易用）
store = {}
def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# ===================== 2. 加载本地代码知识库并构建Chroma向量库 =====================
# 配置路径（与你的项目结构对应）
CODE_DOCS_PATH = "code_docs"  # 本地代码/文档目录
CHROMA_DB_PATH = "knowledge_base"  # Chroma向量库存储目录
# 加载本地文档（支持.py/.md/.txt/.java等主流格式）
if os.path.exists(CODE_DOCS_PATH) and len(os.listdir(CODE_DOCS_PATH)) > 0:
    loader = DirectoryLoader(
        path=CODE_DOCS_PATH,
        glob="**/*",
        loader_cls=TextLoader,
        show_progress=True
    )
    docs = loader.load()
    # 文本分块（适配代码场景，小分块更精准）
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,    # 分块大小，适配1.8B模型
        chunk_overlap=64,  # 分块重叠，保证上下文连续
        length_function=len,
        separators=["\n\n", "\n", "//", "/*", "*/", "#", "##"]  # 代码专属分隔符
    )
    split_docs = text_splitter.split_documents(docs)
    # 构建/加载Chroma本地向量库（首次构建自动生成，后续直接加载）
    vector_db = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH
    )
    # 初始化向量库检索器（相似度检索，取Top3最相关内容）
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
    print(f"✅ 本地代码知识库加载成功，共加载 {len(split_docs)} 个代码片段")
else:
    # 无本地代码知识库时，检索器返回空，直接调用大模型
    retriever = None
    print("ℹ️  未检测到本地代码知识库，将直接使用Qwen-1.8B进行通用代码问答")

# ===================== 3. 构建代码专属Prompt（中文友好，适配OpenCode场景） =====================
# Prompt模板：聚焦代码生成/解释/调试/优化，加入本地知识库上下文（如有）
if retriever:
    # 有本地知识库：结合检索内容+对话历史+用户问题
    template = """
    你是一名专业的开源代码助手OpenCode，基于阿里Qwen-1.8B大模型构建，擅长中文编程问答，核心能力包括代码生成、代码解释、BUG调试、代码优化、项目架构分析。
    请严格按照以下要求回答：
    1. 优先基于【本地代码知识库】的内容回答，若知识库无相关内容，再基于你的自身知识回答；
    2. 代码回答需给出完整可运行的代码片段，附带详细中文注释，说明代码逻辑和使用方法；
    3. 调试问题需先指出错误原因，再给出修正后的代码，说明修改思路；
    4. 优化问题需先分析原代码的问题，再给出优化后的代码，对比说明优化点和性能提升；
    5. 回答简洁专业，避免无关内容，纯代码问题直接给出代码+注释，无需多余话术。

    【本地代码知识库】：
    {context}

    【用户问题】：{question}
    """
    # 构建检索+大模型的链式调用
    def format_docs(docs):
        return "\n\n".join([doc.page_content for doc in docs])
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | ChatPromptTemplate.from_template(template)
        | llm
        | StrOutputParser()
    )
else:
    # 无本地知识库：仅结合对话历史+用户问题
    template = """
    你是一名专业的开源代码助手OpenCode，基于阿里Qwen-1.8B大模型构建，擅长中文编程问答，核心能力包括代码生成、代码解释、BUG调试、代码优化、项目架构分析。
    请严格按照以下要求回答：
    1. 代码回答需给出完整可运行的代码片段，附带详细中文注释，说明代码逻辑和使用方法；
    2. 调试问题需先指出错误原因，再给出修正后的代码，说明修改思路；
    3. 优化问题需先分析原代码的问题，再给出优化后的代码，对比说明优化点和性能提升；
    4. 回答简洁专业，避免无关内容，纯代码问题直接给出代码+注释，无需多余话术。

    【用户问题】：{question}
    """
    rag_chain = (
        {"question": RunnablePassthrough()}
        | ChatPromptTemplate.from_template(template)
        | llm
        | StrOutputParser()
    )

# ===================== 4. 加入对话历史（支持多轮代码问答） =====================
# 构建带对话历史的链式调用
chat_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)

# ===================== 5. 启动OpenCode本地代码助手（交互入口） =====================
def main():
    print("="*80)
    print("✅ OpenCode本地代码助手启动成功（基于Qwen-1.8B+Ollama+LangChain+Chroma）")
    print("ℹ️  支持能力：代码生成/解释/调试/优化 | 本地代码知识库问答 | 多轮对话")
    print("ℹ️  输入「exit」或「退出」可关闭程序")
    print("="*80)
    while True:
        # 获取用户输入
        user_question = input("\n🤔 请输入你的代码问题：")
        if user_question.lower() in ["exit", "退出", "q", "quit"]:
            print("👋 感谢使用OpenCode，程序已关闭！")
            break
        if not user_question.strip():
            print("⚠️  输入不能为空，请重新输入！")
            continue
        # 调用链式模型，生成回答
        try:
            response = chat_chain.invoke(
                user_question,
                config={"configurable": {"session_id": "opencode_001"}}  # 固定会话ID，保持多轮历史
            )
            # 输出回答
            print("\n💻 OpenCode回答：")
            print(response)
        except Exception as e:
            print(f"❌ 回答生成失败，错误信息：{str(e)}")
            print("ℹ️  请检查Ollama是否正常运行（ollama run qwen:1.8b），或环境依赖是否完整！")

if __name__ == "__main__":
    main()