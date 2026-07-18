# Week 15 Graded Mini Project — E-Commerce Domain Support Assistant

## Domain
**E-Commerce** — real, publicly available Amazon.in Customer Service help pages covering returns, shipping & delivery, warranty, and payment issues.

## Public Data Sources
All documents are official Amazon.in Customer Service help pages, saved as PDF:

| Document | Source |
|---|---|
| Returns Policy | https://www.amazon.in/gp/help/customer/display.html?nodeId=202111910 |
| Shipping and Delivery | https://www.amazon.in/gp/help/customer/display.html?nodeId=GGE5X8EV7VNVTK6R |
| Warranty FAQ | https://www.amazon.in/gp/help/customer/display.html?nodeId=Ts7lpDVCMmhh8hYKx2 |
| Payment Issues | https://www.amazon.in/gp/help/customer/display.html?nodeId=GJLLHTPTG32P95DR |

## Project Structure
```
week15_project/
├── documents/                       # Source PDFs for retrieval
│   ├── Amazon_in_Returns_Policy_-_Amazon_Customer_Service.pdf
│   ├── About_Amazon_s_Shipping_and_Delivery_services_-_Amazon_Customer_Service.pdf
│   ├── Frequently_Asked_Questions_about_Warranty_-_Amazon_Customer_Service.pdf
│   └── Payment_Issues_-_Amazon_Customer_Service.pdf
├── ingest.py                        # Document ingestion + FAISS indexing (PyMuPDFLoader)
├── app.py                           # Streamlit chat UI (memory enabled) — bonus
├── ecommerce_rag_agent.ipynb        # Main notebook (Sections A-D, mandatory)
├── sample_conversation_log.txt      # Sample conversation log
├── .env.example                     # Template for your API key — copy to .env
├── .gitignore                       # Excludes .env, vector store, caches from version control
└── README.md
```

## Setup

1. **Install dependencies** (also included as the first cell of the notebook)
   ```bash
   pip install langchain langchain-community langchain-openai faiss-cpu streamlit pymupdf python-dotenv
   ```

2. **Set your API key using a `.env` file** (never hard-code it in source files):
   ```bash
   cp .env.example .env
   ```
   Then open `.env` and replace the placeholder with your real key:
   ```
   OPENAI_API_KEY=your-actual-key-here
   ```
   `ingest.py`, `app.py`, and the notebook all call `load_dotenv()` at startup, which reads
   this file automatically. `.env` is listed in `.gitignore` so it's never committed or shared.

   (Alternatively, you can skip the `.env` file and export the variable directly in your shell:
   `export OPENAI_API_KEY="your-key-here"` on macOS/Linux, or `setx OPENAI_API_KEY "your-key-here"` on Windows.)

3. **Run ingestion** to build the FAISS vector store:
   ```bash
   python ingest.py
   ```
   This reads all `.pdf` files from `documents/` using `PyMuPDFLoader`, chunks them,
   embeds them with `text-embedding-3-small`, and saves the index to `ecommerce_vector_db/`.

## Usage

### Option A — Notebook (CLI chat, mandatory deliverable)
Open `ecommerce_rag_agent.ipynb` and run all cells top to bottom (the first cell installs
dependencies). Section D includes a live demo of:
- a grounded answer (international return eligibility)
- a follow-up question resolved via conversation memory
- an out-of-scope question correctly refused

You can also call the interactive `chat()` function defined in Section C for a live CLI session.

### Option B — Streamlit UI (bonus)
```bash
streamlit run app.py
```
Opens a browser chat interface with persistent conversation memory for the session.

## How It Meets the Requirements

| Requirement | Implementation |
|---|---|
| Document ingestion | `ingest.py` / Notebook Section A — `DirectoryLoader` + `PyMuPDFLoader` + `RecursiveCharacterTextSplitter` + `OpenAIEmbeddings` + `FAISS` |
| Retrieval-augmented chat | Notebook Section B — top-k (k=4) retrieval injected into the prompt as `{context}` |
| Context awareness / follow-ups | Notebook Section C — last 6 turns converted to `HumanMessage`/`AIMessage` and passed via `MessagesPlaceholder("chat_history")` |
| Safety & accuracy | System prompt restricts answers strictly to retrieved context; exact fallback string `"I don't have enough information in the provided documents."` when the answer isn't grounded |
| No fine-tuning | Uses `gpt-4o-mini` via API only, zero-shot with retrieved context |
| No hard-coded answers/secrets | All answers generated from retrieved context; API key loaded from `.env` via `python-dotenv` (never committed — see `.gitignore`) |
| Publicly available documents | Real Amazon.in Customer Service pages (see Public Data Sources above) |

## Troubleshooting

**`AuthenticationError: Incorrect API key provided: voc-...`**
This means you're using a Vocareum-issued key (they start with `voc-`), which is *not*
a standard OpenAI key — Vocareum proxies requests through its own gateway rather than
`api.openai.com`, so the standard endpoint correctly rejects it. Fix:
1. Open the `Vocareum_GenAI_API_Students_Guide.pdf` from your course materials and find the base URL for the proxy (commonly something like `https://openai.vocareum.com/v1`).
2. In your `.env` file, uncomment and set: `OPENAI_API_BASE=<that-url>`.
3. Re-run ingestion / the app — `ingest.py`, `app.py`, and the notebook all read `OPENAI_API_BASE` automatically and pass it through as `base_url` to both `OpenAIEmbeddings` and `ChatOpenAI`.

If you're using a real (non-Vocareum) OpenAI key and still see this error, double-check the key wasn't truncated when copied and hasn't expired or been revoked.

## Notes
- Retrieval is performed using the **current question only** (not the full chat history) — a standard simplification also used in the reference HR chatbot — while the **LLM reasoning** still has access to the full recent conversation for resolving follow-ups like "what about refunds for those international orders instead?".
- `k=4` and `chunk_size=600 / overlap=50` were chosen to balance context relevance against prompt length; adjust as needed if you add more source PDFs.
- `PyMuPDFLoader` returns one `Document` per PDF page, so the "documents loaded" count in Section A reflects total pages across all 4 PDFs, not file count.
