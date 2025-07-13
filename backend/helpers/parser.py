from typing import Optional
import docx
import PyPDF2
import io
import logging
from .logger import get_logger
logger = get_logger(__name__)

class DocumentParser:
    @staticmethod
    def parse_file(file_content: bytes, file_type: str) -> Optional[str]:
        """
        Parse the uploaded file and extract text content.
        
        Args:
            file_content: Raw bytes of the uploaded file
            file_type: File extension (pdf, docx, txt)
            
        Returns:
            Extracted text content or None if parsing fails
        """
        try:
            if file_type == 'txt':
                return file_content.decode('utf-8')
            
            elif file_type == 'pdf':
                return DocumentParser._parse_pdf(file_content)
            
            elif file_type == 'docx':
                return DocumentParser._parse_docx(file_content)
            
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            logger.error(f"Error parsing file: {str(e)}")
            return None
    
    @staticmethod
    def _parse_pdf(file_content: bytes) -> str:
        """Extract text from PDF file."""
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
            
        return text.strip()
    
    @staticmethod
    def _parse_docx(file_content: bytes) -> str:
        """Extract text from DOCX file."""
        docx_file = io.BytesIO(file_content)
        doc = docx.Document(docx_file)
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
            
        return text.strip() 