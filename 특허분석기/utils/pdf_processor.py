import pdfplumber
import fitz  # PyMuPDF
from fpdf import FPDF
import os

def extract_text_from_pdf(pdf_path):
    """
    주어진 경로의 PDF 파일에서 텍스트를 추출합니다.
    """
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted_page = page.extract_text()
                if extracted_page:
                    text += extracted_page + "\n"
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return None
    return text

def extract_images_from_pdf(pdf_path, temp_dir):
    """
    PDF 페이지를 이미지(도면)로 변환하여 임시 디렉토리에 저장합니다.
    """
    image_paths = []
    try:
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            page = doc.load_page(i)
            # 특허 도면은 대개 선명해야 하므로 2배 확대(Matrix) 렌더링
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_path = os.path.join(temp_dir, f"drawing_page_{i+1}.png")
            pix.save(img_path)
            image_paths.append(img_path)
    except Exception as e:
        print(f"Error extracting images: {e}")
    return image_paths

def create_pdf_report(content_dict, selected_items):
    """
    선택된 분석 결과를 한글 PDF로 생성하여 바이트 데이터를 반환합니다.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # 한글 폰트 설정 (윈도우 맑은 고딕 경로)
    font_path = r"C:\Windows\Fonts\malgun.ttf"
    if os.path.exists(font_path):
        pdf.add_font("Malgun", "", font_path)
        pdf.set_font("Malgun", size=11)
    else:
        # 폰트가 없을 경우 기본 폰트 사용 (한글 깨짐 주의)
        pdf.set_font("Helvetica", size=11)

    pdf.set_font("Malgun", size=16)
    pdf.cell(0, 15, txt="특허 분석 결과 리포트", ln=True, align='C')
    pdf.ln(10)

    # 선택된 항목만 PDF에 추가
    for item_name, display_name in [("summary", "요약 분석"), ("strategy", "방어 전략"), ("solution", "해결 방안")]:
        if item_name in selected_items and content_dict.get(item_name):
            pdf.set_font("Malgun", size=14)
            pdf.set_text_color(30, 70, 150) # 푸른색 계열 제목
            pdf.cell(0, 10, txt=f"■ {display_name}", ln=True)
            pdf.ln(2)
            
            pdf.set_font("Malgun", size=10)
            pdf.set_text_color(0, 0, 0)
            # Markdown 기호 제거 및 줄바꿈 처리
            clean_text = content_dict[item_name].replace("**", "").replace("#", "")
            pdf.multi_cell(0, 7, txt=clean_text)
            pdf.ln(10)

    return pdf.output()
