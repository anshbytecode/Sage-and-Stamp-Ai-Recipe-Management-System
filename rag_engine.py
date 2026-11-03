"""
rag_engine.py
RAG (Retrieval-Augmented Generation) System for Sage & Stamp – Advanced AI Edition.
Features:
- PDF and Text cookbook upload & ingestion
- Recipe document extraction (pypdf + fallback)
- Text chunking with overlap and page/section tracking
- Vector Embeddings & Vector Database with cosine similarity retrieval
- Context-based answers with source references & highlighted citations
"""
import os
import re
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

# Storage directory for uploaded and sample cookbooks
COOKBOOK_DIR = os.path.join(os.path.dirname(__file__), "data", "cookbooks")
if os.environ.get("VERCEL") or (os.name != "nt" and not os.access(os.path.dirname(COOKBOOK_DIR) or ".", os.W_OK)):
    TMP_COOKBOOK = "/tmp/cookbooks"
    try:
        os.makedirs(TMP_COOKBOOK, exist_ok=True)
        if os.path.exists(COOKBOOK_DIR):
            import shutil
            for fn in os.listdir(COOKBOOK_DIR):
                src = os.path.join(COOKBOOK_DIR, fn)
                dst = os.path.join(TMP_COOKBOOK, fn)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
    except Exception:
        pass
    COOKBOOK_DIR = TMP_COOKBOOK
else:
    try:
        os.makedirs(COOKBOOK_DIR, exist_ok=True)
    except Exception:
        pass


class VectorStore:
    """
    Vector Database index for document chunks.
    Uses TF-IDF semantic embeddings with cosine similarity.
    Provides identical semantics to FAISS (FlatIP / cosine similarity).
    """
    def __init__(self):
        self.chunks = []  # list of dicts: {text, doc_name, page, chunk_id}
        self.vectorizer = None
        self.matrix = None

    def build_index(self, chunks):
        self.chunks = chunks
        if not chunks:
            self.vectorizer = None
            self.matrix = None
            return

        corpus = [c["text"] for c in chunks]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 4):
        if self.matrix is None or not self.chunks or not query.strip():
            return []

        q_clean = query.lower()
        q_vec = self.vectorizer.transform([q_clean])
        sims = cosine_similarity(q_vec, self.matrix).flatten()
        top_indices = np.argsort(-sims)

        results = []
        for idx in top_indices[:top_k]:
            score = float(sims[idx])
            if score > 0.04:  # relevance threshold
                chunk_copy = dict(self.chunks[idx])
                chunk_copy["score"] = round(score * 100, 1)
                results.append(chunk_copy)

        return results


class RAGCookbookEngine:
    def __init__(self):
        self.vector_store = VectorStore()
        self.documents = []  # metadata about indexed books
        self.initialize_default_cookbooks()

    def chunk_text(self, text: str, doc_name: str, page_num: int = 1, chunk_size: int = 450, overlap: int = 80):
        """Splits document text into overlapping semantic passages with metadata."""
        cleaned_text = re.sub(r"\s+", " ", text).strip()
        if not cleaned_text:
            return []

        chunks = []
        start = 0
        chunk_idx = 1
        text_len = len(cleaned_text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            
            # Avoid cutting mid-word if possible
            if end < text_len:
                next_space = cleaned_text.rfind(" ", start, end)
                if next_space > start + (chunk_size // 2):
                    end = next_space

            passage = cleaned_text[start:end].strip()
            if len(passage) > 30:
                chunks.append({
                    "chunk_id": f"{doc_name}-p{page_num}-c{chunk_idx}",
                    "doc_name": doc_name,
                    "page": page_num,
                    "text": passage
                })
                chunk_idx += 1

            start += (chunk_size - overlap)

        return chunks

    def extract_text_from_pdf(self, file_path: str):
        """Extracts text per page from a PDF file."""
        pages = []
        if HAS_PYPDF:
            try:
                reader = pypdf.PdfReader(file_path)
                for i, page in enumerate(reader.pages):
                    txt = page.extract_text() or ""
                    pages.append((i + 1, txt))
            except Exception as e:
                pages.append((1, f"Error reading PDF with pypdf: {str(e)}"))
        else:
            # Fallback if pypdf is unavailable
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                pages.append((1, f.read()))
        return pages

    def ingest_document(self, file_path: str, custom_name: str = None):
        """Ingests a PDF or text file into the vector database."""
        filename = custom_name or os.path.basename(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        new_chunks = []
        if ext == ".pdf":
            pages = self.extract_text_from_pdf(file_path)
            for page_num, txt in pages:
                page_chunks = self.chunk_text(txt, filename, page_num=page_num)
                new_chunks.extend(page_chunks)
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read()
            new_chunks.extend(self.chunk_text(txt, filename, page_num=1))

        # Check existing and rebuild index
        existing_chunks = [c for c in self.vector_store.chunks if c["doc_name"] != filename]
        all_chunks = existing_chunks + new_chunks
        self.vector_store.build_index(all_chunks)

        doc_meta = {
            "name": filename,
            "chunks_count": len(new_chunks),
            "pages_count": max([c["page"] for c in new_chunks]) if new_chunks else 1
        }
        self.documents = [d for d in self.documents if d["name"] != filename]
        self.documents.append(doc_meta)
        return doc_meta

    def query(self, question: str, top_k: int = 3):
        """
        Retrieval-Augmented Generation Q&A:
        1. Embeds question and searches vector store
        2. Retrieves most relevant text chunks
        3. Formulates context-grounded answer with source citations
        """
        chunks = self.vector_store.search(question, top_k=top_k)
        
        if not chunks:
            return {
                "answer": "I could not find a sufficiently close match in the indexed cookbooks for your query. Try rephrasing with specific ingredient terms (e.g., 'biryani dum', 'slow simmer dal', 'paneer softness', 'temper mustard seeds').",
                "citations": [],
                "confidence": 0
            }

        # Synthesize answer from retrieved chunks
        context_text = "\n\n".join([f"[{c['doc_name']} (Page {c['page']})]: {c['text']}" for c in chunks])
        
        # Build synthesis response
        primary_chunk = chunks[0]
        answer_paragraphs = [
            f"Based on **{primary_chunk['doc_name']}** (Page {primary_chunk['page']}):",
            f"\"{primary_chunk['text']}\""
        ]

        if len(chunks) > 1:
            sec_chunk = chunks[1]
            answer_paragraphs.append(
                f"Additionally, **{sec_chunk['doc_name']}** notes: \"{sec_chunk['text'][:250]}...\""
            )

        citations = [
            {
                "doc_name": c["doc_name"],
                "page": c["page"],
                "chunk_id": c["chunk_id"],
                "score_pct": c["score"],
                "snippet": c["text"][:180] + ("..." if len(c["text"]) > 180 else "")
            }
            for c in chunks
        ]

        return {
            "answer": "\n\n".join(answer_paragraphs),
            "citations": citations,
            "confidence": primary_chunk["score"]
        }

    def initialize_default_cookbooks(self):
        """Pre-seeds standard heritage cookbooks for instant out-of-the-box RAG capabilities."""
        cookbook_1_name = "The Heritage Indian Culinary Compendium.txt"
        cookbook_1_path = os.path.join(COOKBOOK_DIR, cookbook_1_name)
        
        if not os.path.exists(cookbook_1_path):
            content_1 = """
            Chapter 1: The Alchemy of Tadka (Tempering)
            In classical Indian gastronomy, spices are rarely tossed in raw. Fat (ghee, cold-pressed mustard oil, or groundnut oil) acts as a solvent that extracts fat-soluble essential oils from whole spices. When mustard seeds splutter, their glucosinolates break down into pungent isothiocyanates. Cumin seeds must be sizzled until deeply browned, not burned, releasing cuminaldehyde. The addition of hing (asafoetida) should always occur in medium-hot fat just before wet aromatics like ginger and green chili are introduced to prevent burning the delicate resin.

            Chapter 2: The Architecture of Dal Makhani
            Authentic Dal Makhani derives its iconic silkiness not from excessive cream, but from slow starches dissolving over low heat. Whole black urad dal and Kashmiri rajma must be soaked for a minimum of 12 hours. During the initial pressure boil, the legumes must yield completely under gentle finger pressure. A slow simmer of at least 45 to 60 minutes with butter, ripe tomato puree, and julienned ginger allows the amylose starches to gelatinize. Cream is added off the flame at the very conclusion, followed by crushed toasted kasuri methi (fenugreek leaves).

            Chapter 3: The Dum Technique for Royal Biryani
            Dum Pukht (slow steam cooking in a sealed vessel) creates thermal convection currents that permeate each grain of long basmati rice with aromatic poultry, mutton, or vegetable essence. Parboil aged basmati rice to exactly 70% tenderness with whole cinnamon, green cardamom, cloves, and bay leaf. Layer with tender spiced base, caramel-fried onions (birista), fresh mint, coriander, and saffron steeped in warm whole milk. Seal the pot perimeter with a dough ribbon or heavy-duty foil. Cook on low heat over a heavy cast-iron tawa for 25 minutes, then rest for 15 minutes before unsealing.

            Chapter 4: The Physics of Paneer Softness
            Paneer is an unaged acid-set cheese made by curdling heated cow or buffalo milk with lemon juice or whey. The secret to keeping paneer supple in rich gravies is never to over-brown it. If shallow frying, limit cooking to 60 seconds per side. Alternatively, soak commercial paneer blocks in warm water with 1/2 teaspoon of salt for 15 minutes before dicing. The osmosis hydrates the protein matrix, preventing dehydration during simmering.

            Chapter 5: Fermentation Principles for Crisp Masala Dosa
            The secret to a crisp yet pliable dosa is the exact 3:1 ratio of parboiled idli rice to whole skinned urad dal, fortified with a tablespoon of methi (fenugreek) seeds and chana dal. Methi seeds harbor wild lactobacillus and natural yeasts that produce carbon dioxide, giving the batter airy lightness. Ferment for 10-14 hours at 28°C to 32°C. Spread paper-thin on a seasoned cast-iron tawa, dabbing with clarified ghee, until golden lattice crisps appear.
            """
            try:
                with open(cookbook_1_path, "w", encoding="utf-8") as f:
                    f.write(content_1.strip())
            except Exception:
                pass

        cookbook_2_name = "Ayurvedic Food Synergy & Modern Nutrition.txt"
        cookbook_2_path = os.path.join(COOKBOOK_DIR, cookbook_2_name)
        if not os.path.exists(cookbook_2_path):
            content_2 = """
            Section 1: The Six Tastes (Shad Rasa) in Every Meal
            A truly satisfying and nutritionally complete meal balances six distinct tastes: Sweet (Madhura - grains, dairy), Sour (Amla - lemon, tomatoes, yogurt), Salty (Lavana - rock salt), Pungent (Katu - chilies, black pepper), Bitter (Tikta - turmeric, fenugreek, leafy greens), and Astringent (Kashaya - lentils, legumes, pomegranate). When all six tastes are present, brain satiety centers trigger fullness quickly, eliminating unnecessary cravings.

            Section 2: Enhancing Curcumin Bioavailability
            Turmeric (Curcuma longa) contains curcumin, a formidable polyphenol known for anti-inflammatory and cellular longevity benefits. Curcumin by itself has low oral bioavailability because it is rapidly metabolized in the liver and intestinal wall. Pairing turmeric with black pepper (which contains piperine) increases the serum concentration and bio-efficacy of curcumin by up to 2,000%. Furthermore, because curcumin is lipophilic (fat-soluble), it must always be cooked in warm oil, ghee, or milk fat for optimal intestinal absorption.

            Section 3: Legume Digestion & Flatulence Prevention
            Lentils, chickpeas, and beans are rich in prebiotic fiber and plant protein, but contain complex oligosaccharides like raffinose that humans lack enzymes to digest. In the colon, bacteria ferment these into gas. To completely eliminate bloating: soak legumes with a pinch of baking soda or salt, discard soaking water completely, boil with fresh water, and temper with asafoetida (hing), cumin, and fresh ginger.
            """
            try:
                with open(cookbook_2_path, "w", encoding="utf-8") as f:
                    f.write(content_2.strip())
            except Exception:
                pass

        # Ingest both books into the vector store
        self.ingest_document(cookbook_1_path, "The Heritage Indian Culinary Compendium")
        self.ingest_document(cookbook_2_path, "Ayurvedic Food Synergy & Modern Nutrition")


rag_engine = RAGCookbookEngine()
