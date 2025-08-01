EXAMPLE_DATA = {
    "Summary": """### The Invisible Bottleneck Killing Enterprise AI Projects

Poor data chunking is a critical but often overlooked issue that can derail enterprise AI projects, leading to inaccurate results and significant costs. Understanding and implementing effective chunking strategies is foundational to the success of any AI system that relies on large datasets.

#### The High Cost of Bad Chunking: A Fintech Case Study [0:01-0:07, 0:56-1:21]

A fintech company nearly lost a major deal due to a poorly implemented AI chatbot. When asked about indemnification in a non-disclosure agreement (NDA), the chatbot gave a confidently incorrect answer. The contract stated, "Party A indemnifies Party B," but a crucial exception, "except as provided in section X," was located in the next data chunk. Because the system was using a simple token-count for chunking, it split the sentence in half.

The AI retrieved only the first chunk and incorrectly stated that Party A fully indemnified Party B [1:15-1:23]. This error, which took many billable hours to rectify, was not a failure of the AI's intelligence but a fundamental flaw in its data preparation—a context engineering problem that newer models like GPT-5 won't solve on their own [1:25-1:42].

#### Why Chunking is the Foundation of Effective AI

For companies implementing Retrieval-Augmented Generation (RAG) systems, the most critical question is not which embedding model to use, but "how should we chunk our data?" [1:43-1:53]. Proper chunking is the first line of defense against model hallucinations. When an AI is fed incomplete information from poorly divided chunks, it will attempt to fill in the gaps, leading to fabrications [1:54-2:00].

Here’s how the process works and where it can go wrong:
*   **The Retrieval Process** [2:16-2:31]: When a user asks a question, the AI system retrieves the 3-5 most relevant chunks of data based on semantic similarity to formulate an answer.
*   **The Problem of Split Answers** [2:32-2:41]: If the complete, true answer is split across multiple chunks, and the AI only retrieves some of them, the response will be incomplete and likely incorrect.

Beyond accuracy, chunking has a direct impact on operational costs. Inefficient chunking forces the system to retrieve more chunks than necessary, increasing token usage and costs. Loading excessive, and often meaningless, context into the AI's context window can overwhelm it, ironically leading to less accurate responses [2:51-3:04]. By optimizing chunking strategies, companies can reduce their AI-related expenses by double-digit percentages [3:04-3:12].

#### RAG vs. Agentic Search: Chunking is Still Key

While agentic search—which uses AI agents to iteratively search, read, and reason—can be effective for complex, exploratory queries across multiple data types, it is not a replacement for good chunking [3:42-3:57, 4:02-4:21]. Agentic search can be over 10 times slower and more expensive than a well-optimized RAG system [5:05-5:12].

RAG excels at providing fast, consistent, and economical answers when queries map cleanly to specific information [4:31-4:43]. Ultimately, even agentic systems rely on well-structured data, meaning that effective chunking remains a foundational requirement [6:22-6:26].

#### 5 Principles for Effective Chunking

To avoid the pitfalls of poor data preparation, follow these five principles:

1.  **Context Coherence** [8:05-8:24]: Never split a single, coherent thought or meaning across multiple chunks. Respect the natural boundaries within your data, such as sections in a legal document or functions in source code.
2.  **Know Your Three Levers** [8:44-9:03]: You can control chunking through three main levers:
    *   **Boundaries:** Where you make the cuts (e.g., by sentence, paragraph, or section).
    *   **Size:** How large each chunk is, which should be determined by what constitutes a complete unit of meaning.
    *   **Overlap:** Duplicating a small amount of information (e.g., 10-20%) between consecutive chunks to ensure no critical context is lost at the boundaries.
3.  **Let the Data Type Dictate Your Strategy** [9:46-10:11]: Different types of data require different chunking approaches:
    *   **Legal Contracts:** Chunk by section or subsection.
    *   **Source Code:** Chunk by function or class. Consider building dependency graphs to include all related functions in a single chunk.
    *   **Financial Tables:** This is notoriously difficult. A simple row-by-row approach will fail. Instead, chunk by calculable units or even convert tables to natural language descriptions.
4.  **Size for "Goldilocks" Outcomes** [10:54-11:17]: Find the right chunk size. If chunks are too small, they will lack context. If they are too large, they will be costly and can lead to unfocused answers. The ideal size often falls between 500 and 1000 tokens, but this should be tested against an evaluation set of questions.
5.  **Remember Overlap** [11:18-11:32]: Overlap is your insurance policy. It is a crucial, yet often underutilized, technique to prevent important information from being lost at chunk boundaries.

Ultimately, there is no magic solution for messy data. The path to a high-performing AI system requires confronting the complexities of your data architecture. By applying these principles, you can build a solid foundation for your AI, ensuring more accurate, cost-effective, and truly transformative results.""",
    "Title": "TEST Chunking 101: The Invisible Bottleneck Killing Enterprise AI Projects",
    "Channel": "AI News & Strategy Daily | Nate B Jones",
    "Video URL": "https://www.youtube.com/watch?v=pMSXPgAUq_k",
    "Cover": "https://img.youtube.com/vi/pMSXPgAUq_k/maxresdefault.jpg"
}