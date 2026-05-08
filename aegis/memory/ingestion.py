"""
aegis/memory/ingestion.py

Pipeline de ingestão de documentos para o AEGIS.
Suporta PDF, DOCX, TXT, MD, HTML, Código, Imagens (OCR) e Áudio (Transcrição).
Integrado com ResourceGuard para proteção de hardware na RTX 3060.
"""
from __future__ import annotations

import asyncio
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import structlog
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

from aegis.core.config import get_settings
from aegis.core.resource_guard import ResourceGuard

logger = structlog.get_logger(__name__)

class DocumentIngester:
    """
    Orquestrador de ingestão de documentos.
    Garante que apenas um documento seja processado por vez na RTX 3060.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.guard = ResourceGuard.get_instance()
        self.inbox_dir = Path(self.settings.AEGIS_DATA_DIR) / "inbox"
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        
        self._processing_lock = asyncio.Lock()
        self._processed_hashes: Set[str] = set()

    async def ingest_file(self, file_path: str | Path) -> List[Dict[str, Any]]:
        """
        Ingere um arquivo, extrai texto, realiza chunking e deduplicação.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error("ingestion.file_not_found", path=str(path))
            return []

        # 1. Verificar ResourceGuard (RAM e VRAM)
        if not self.guard.is_safe_for("ingest"):
            logger.warning("ingestion.waiting_for_resources", path=str(path))
            await self.guard.wait_for_safe("ingest")

        # 2. Garantir processamento sequencial (1 por vez na 3060 para evitar picos de RAM)
        async with self._processing_lock:
            logger.info("ingestion.started", path=str(path))
            try:
                # Extração
                content = await self._extract_text(path)
                if not content:
                    logger.warning("ingestion.no_content_extracted", path=str(path))
                    return []

                # Chunking (512 tokens ~ 2000 chars, 10% overlap)
                chunks = self._create_chunks(content, str(path))
                
                logger.info("ingestion.success", path=str(path), chunks=len(chunks))
                return chunks
            except Exception as e:
                logger.error("ingestion.error", path=str(path), error=str(e), exc_info=True)
                return []

    async def _extract_text(self, path: Path) -> str:
        """Extrai texto dependendo da extensão do arquivo."""
        suffix = path.suffix.lower()
        
        # Formatos de texto simples
        if suffix in [".txt", ".md", ".py", ".js", ".ts", ".c", ".cpp", ".h", ".json", ".yaml"]:
            return path.read_text(encoding="utf-8", errors="ignore")
        
        elif suffix == ".pdf":
            return await self._extract_pdf(path)
        
        elif suffix == ".docx":
            return await self._extract_docx(path)
        
        elif suffix in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            return await self._extract_image(path)
        
        elif suffix in [".mp3", ".wav", ".m4a", ".flac"]:
            return await self._extract_audio(path)
            
        elif suffix in [".html", ".htm"]:
            return await self._extract_html(path)

        logger.warning("ingestion.unsupported_format", suffix=suffix)
        return ""

    async def _extract_pdf(self, path: Path) -> str:
        """Extração de PDF via pypdf."""
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text
        except ImportError:
            logger.error("ingestion.missing_dependency", lib="pypdf")
            return ""
        except Exception as e:
            logger.error("ingestion.pdf_error", path=str(path), error=str(e))
            return ""

    async def _extract_docx(self, path: Path) -> str:
        """Extração de DOCX via python-docx."""
        try:
            import docx
            doc = docx.Document(str(path))
            return "\n".join([p.text for p in doc.paragraphs])
        except ImportError:
            logger.error("ingestion.missing_dependency", lib="python-docx")
            return ""
        except Exception as e:
            logger.error("ingestion.docx_error", path=str(path), error=str(e))
            return ""

    async def _extract_html(self, path: Path) -> str:
        """Extração de HTML via BeautifulSoup4."""
        try:
            from bs4 import BeautifulSoup
            content = path.read_text(encoding="utf-8", errors="ignore")
            soup = BeautifulSoup(content, "html.parser")
            # Remove scripts e estilos
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text(separator="\n")
        except ImportError:
            logger.error("ingestion.missing_dependency", lib="beautifulsoup4")
            return ""

    async def _extract_image(self, path: Path) -> str:
        """OCR local via Tesseract. Requer Tesseract-OCR instalado no sistema."""
        try:
            import pytesseract
            from PIL import Image
            return pytesseract.image_to_string(Image.open(str(path)))
        except ImportError:
            logger.error("ingestion.missing_dependency", lib="pytesseract/pillow")
            return ""
        except Exception as e:
            logger.error("ingestion.ocr_error", path=str(path), error=str(e))
            return ""

    async def _extract_audio(self, path: Path) -> str:
        """Transcrição local via faster-whisper na RTX 3060."""
        # Verificar se GPU está muito ocupada para Whisper
        if not self.guard.is_safe_for("inference"):
            logger.warning("ingestion.audio.gpu_busy_waiting")
            await self.guard.wait_for_safe("inference")

        try:
            from faster_whisper import WhisperModel
            # Modelo medium é o limite para co-existência na 3060 (0.9GB VRAM)
            model_size = "medium"
            # compute_type="float16" para melhor performance na 3060
            model = WhisperModel(model_size, device="cuda", compute_type="float16")
            segments, _ = model.transcribe(str(path), beam_size=5)
            return " ".join([segment.text for segment in segments])
        except ImportError:
            logger.error("ingestion.missing_dependency", lib="faster-whisper")
            return ""
        except Exception as e:
            logger.error("ingestion.audio_error", path=str(path), error=str(e))
            return ""

    def _create_chunks(self, text: str, source: str) -> List[Dict[str, Any]]:
        """
        Chunking: 512 tokens (aprox 2000 chars), 10% overlap (200 chars).
        Respeita parágrafos e quebras de linha para manter coesão.
        """
        chunk_size = 2000
        overlap = 200
        chunks = []
        
        # Deduplicação por hash do arquivo completo
        file_hash = hashlib.sha256(text.encode()).hexdigest()
        if file_hash in self._processed_hashes:
            logger.info("ingestion.duplicate_file_skipped", source=source)
            return []
        self._processed_hashes.add(file_hash)

        text = text.strip()
        if not text:
            return []

        start = 0
        while start < len(text):
            end = start + chunk_size
            
            # Tentar quebrar em parágrafo (\n\n) ou linha (\n)
            if end < len(text):
                # Busca o último parágrafo duplo no segundo terço do chunk
                last_p = text.rfind("\n\n", start + chunk_size // 2, end)
                if last_p != -1:
                    end = last_p + 2
                else:
                    # Tentar quebrar em linha simples
                    last_l = text.rfind("\n", start + chunk_size // 2, end)
                    if last_l != -1:
                        end = last_l + 1

            chunk_content = text[start:end].strip()
            if chunk_content:
                chunk_hash = hashlib.sha256(chunk_content.encode()).hexdigest()
                chunks.append({
                    "content": chunk_content,
                    "hash": chunk_hash,
                    "metadata": {
                        "source": source,
                        "file_hash": file_hash,
                        "start_index": start,
                        "end_index": end,
                        "type": "document_chunk"
                    }
                })
            
            # Próximo start com overlap
            start = end - overlap
            if start < 0: start = 0
            if end >= len(text):
                break

        return chunks

if WATCHDOG_AVAILABLE:
    class InboxWatcher(FileSystemEventHandler):
        """Handler para eventos do sistema de arquivos na pasta inbox."""
        
        def __init__(self, ingester: DocumentIngester, loop: asyncio.AbstractEventLoop):
            self.ingester = ingester
            self.loop = loop

        def on_created(self, event):
            if not event.is_directory:
                logger.info("watcher.file_created", path=event.src_path)
                # Não bloqueia o watcher, agenda a tarefa no loop
                asyncio.run_coroutine_threadsafe(
                    self.ingester.ingest_file(event.src_path), 
                    self.loop
                )

        def on_moved(self, event):
            if not event.is_directory:
                logger.info("watcher.file_moved", to_path=event.dest_path)
                asyncio.run_coroutine_threadsafe(
                    self.ingester.ingest_file(event.dest_path), 
                    self.loop
                )

async def start_inbox_watcher(loop: Optional[asyncio.AbstractEventLoop] = None):
    """
    Inicializa o monitoramento da pasta inbox.
    Deve ser rodado como uma task de background.
    """
    if not WATCHDOG_AVAILABLE:
        logger.error("watcher.failed", error="watchdog library not installed")
        return

    settings = get_settings()
    ingester = DocumentIngester()
    inbox_path = Path(settings.AEGIS_DATA_DIR) / "inbox"
    inbox_path.mkdir(parents=True, exist_ok=True)
    
    current_loop = loop or asyncio.get_running_loop()
    
    observer = Observer()
    handler = InboxWatcher(ingester, current_loop)
    observer.schedule(handler, str(inbox_path), recursive=False)
    observer.start()
    
    logger.info("watcher.started", path=str(inbox_path))
    
    try:
        while True:
            await asyncio.sleep(60) # Mantém a task viva
    except asyncio.CancelledError:
        logger.info("watcher.stopping")
        observer.stop()
        observer.join()
