import google.generativeai as genai
from typing import List, Dict
import os
from datetime import datetime, timezone

# Cấu hình Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def create_news_bulletin(articles: List[Dict]) -> Dict:
    
    if not GEMINI_API_KEY:
        return {
            "success": False,
            "error": "GEMINI_API_KEY không được cấu hình",
            "bulletin": None
        }
    
    if not articles:
        return {
            "success": False, 
            "error": "Không có bài viết nào để tổng hợp",
            "bulletin": None
        }
    
    try:
        prompt = create_bulletin_prompt(articles)
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate content
        response = model.generate_content(prompt)
        
        if response and response.text:
            return {
                "success": True,
                "bulletin": response.text.strip(),
                "articles_processed": len(articles),
                "sources_used": list(set([article.get("source", "unknown") for article in articles])),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "error": None
            }
        else:
            return {
                "success": False,
                "error": "Gemini không trả về kết quả",
                "bulletin": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi gọi Gemini API: {str(e)}",
            "bulletin": None
        }


def create_bulletin_prompt(articles: List[Dict]) -> str:
    
    # Header của prompt
    prompt = """Bạn là một biên tập viên chuyên nghiệp về tin tức tiền điện tử. Hãy tạo một bản tin tổng hợp ngắn gọn và chuyên nghiệp từ các bài viết tin tức crypto sau đây.

YÊU CẦU:
1. Tóm tắt các tin tức quan trọng nhất trong 3-5 điểm chính
2. Sắp xếp theo mức độ quan trọng (tin tác động lớn trước)
3. Mỗi điểm không quá 2-3 câu
4. Sử dụng tiếng Việt chuyên nghiệp
5. Tập trung vào những thông tin có tác động đến thị trường crypto
6. Tránh lặp lại thông tin giống nhau từ nhiều nguồn

ĐỊNH DẠNG:
📊 BẢN TIN CRYPTO TỔNG HỢP

🔥 ĐIỂM CHÍNH:
• [Điểm 1]
• [Điểm 2]  
• [Điểm 3]

---
CÁC BÀI VIẾT NGUỒN:

"""
    
    for i, article in enumerate(articles, 1):
        title = article.get("title", "Không có tiêu đề")
        content = article.get("content", "Không có nội dung")
        source = article.get("source", "unknown")
        published_time = article.get("published_time", "")
        
        prompt += f"""
{i}. NGUỒN: {source.upper()}
TIÊU ĐỀ: {title}
THỜI GIAN: {published_time}
NỘI DUNG: {content}

---
"""
    
    prompt += "\nHãy tạo bản tin tổng hợp theo yêu cầu trên:"
    
    return prompt


def summarize_single_article(title: str, content: str) -> Dict:
    """
    Tóm tắt một bài viết đơn lẻ bằng Gemini
    
    Args:
        title: Tiêu đề bài viết
        content: Nội dung bài viết
        
    Returns:
        Dict: Kết quả tóm tắt
    """
    
    if not GEMINI_API_KEY:
        return {
            "success": False,
            "error": "GEMINI_API_KEY không được cấu hình",
            "summary": None
        }
    
    try:
        prompt = f"""Hãy tóm tắt bài viết crypto này thành 2-3 câu ngắn gọn, tập trung vào thông tin quan trọng nhất:

TIÊU ĐỀ: {title}

NỘI DUNG: {content}

TÓM TẮT:"""

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        if response and response.text:
            return {
                "success": True,
                "summary": response.text.strip(),
                "error": None
            }
        else:
            return {
                "success": False,
                "error": "Gemini không trả về kết quả",
                "summary": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi gọi Gemini API: {str(e)}",
            "summary": None
        }
