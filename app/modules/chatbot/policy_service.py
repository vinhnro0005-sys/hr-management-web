import os
from dotenv import load_dotenv
from google import genai
from app.modules.chatbot.policy_repository import search_policy_chunks
load_dotenv()
_ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def handle_policy_inquiry(question: str) -> dict:
    # 1. Tạo vector câu hỏi
    embed_res = _ai_client.models.embed_content(
        model="gemini-embedding-2",
        contents=question
    )
    query_vector = embed_res.embeddings[0].values

    # 2. Gọi Repo lấy các đoạn liên quan
    search_data = search_policy_chunks(query_vector, top_k=3)
    context = "\n---\n".join(search_data["documents"])

    # 3. Ép LLM trả lời kèm trích dẫn
    prompt = f"""
    Dựa DUY NHẤT vào trích đoạn quy chế sau để trả lời câu hỏi:
    {context}

    Câu hỏi: {question}
    Nếu thông tin không có, trả lời: "Nội quy công ty hiện không quy định về vấn đề này."
    """
    resp = _ai_client.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt)
    pages = sorted(list(set([m["page"] for m in search_data["metadatas"] if "page" in m])))

    return {
        "type": "TEXT",
        "message": resp.text.strip(),
        "citation": {"source": "Noi_quy_lao_dong.pdf", "pages": pages}
    }
    