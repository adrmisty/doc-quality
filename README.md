# Document Quality assessment pipeline

A robust, modular Python pipeline and REST API designed to assess the quality of digital documents (primarily PDFs). This system validates document structure, extracts semantic metadata using LLM interfaces, and performs topic modeling to cluster documents by content.

## Project architecture

The system is designed as a multi-stage pipeline that can be run via a **CLI** for batch processing or hosted as a **FastAPI** service for real-time validation.

### Core modules

1. **Loader**: Efficient batch downloading of documents from JSON sources.
2. **Structural validator**:
   - Performs strict file signature checks to reject masked binary/video files.
   - Analyzes text density, page count, and metadata integrity.
   - Assigns a quality score to every document.
      --> this structural analysis depends on typology-based criteria (practice abstracts & policy briefs, project deliverables & reports, promotional content & newsletters, or scientific/technical papers).
3. **Metadata extractor**: Interface for external LLM-based metadata extraction (title, summary, keywords, topics).
4. **Topic modeling**: Implements **BERTopic**, with **UMAP** and **HDBSCAN**, model to generate semantic clusters from the validated dataset.


## Getting started

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional, for containerized deployment)
- NVIDIA GPU (recommended for topic modeling / Torch)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/adrmisty/doc-quality-app.git
   cd doc-quality
   ```

2. Install dependencies:
   ```bash
    pip install -r requirements.txt
   ```


## Usage

### CLI
The application uses a unified entry point main.py located in the `app/` module. You can run individual functionality stages (of the pipeline: downloading, metadata extraction or topic modeling) or the full workflow.

**Note**: Run these commands from the project root.


1. Download a maximum of `n` documents from a source list of URLs off a JSON file:
   ```bash
   python3 -m doc_quality.app.main download --n 100 --output ./data/pdf
   ```

2. Extract metadata and validate document structure for a maximum of `n_meta` files. **Note**: takes quite long depending on how many/type of documents used as input.
   ```bash
   python3 -m doc_quality.app.main metadata --n_meta 50 --input_dir ./data/pdf
   ```

3. Train topic model on extracted metadata and content:
   ```bash
   python3 -m doc_quality.app.main topics --input_dir ./data/metadata/valid --output_dir ./data/models
   ```

3. Run full pipeline sequentially:
   ```bash
   python3 -m doc_quality.app.main all --n 500
   ```

### API 

The project includes a production-ready FastAPI server that exposes the quality assessment logic, accessibly locally at `http://localhost:8000/docs`.

   ```bash
   python3 -m doc_quality.app.main serve --host 0.0.0.0 --port 8000
   ```

### Docker 

The project is containerized for easy deployment, including (much-needed) GPU support for the machine learning components.

1. Build the container:
   ```bash
   docker-compose build
   ```

2. Start the service:
   ```bash
   # must have NVIDIA Container Toolkit installed for GPU support
   docker-compose up -d
   ```
   

## Project structure

```
doc-quality-app/
├── Dockerfile                  # containerization
├── docker-compose.yml          
├── requirements.txt            # python dependencies
└── ko_quality/                 
    ├── app/                    # app entry points and API routers
    ├── config/                 # config prompt templates, .env defs if needed
    ├── pipeline/               
    │   ├── loader/             # document ingestion
    │   ├── metadata/           # outsourced metadata extraction
    │   ├── quality/            # structural validation
    │   └── topics/             # topic model training & inference
    └── scripts/                # CLI command wrappers
```


### Configuration

Configuration is managed via the `pydantic-settings` library. You can override defaults (to be defined in `config.py`) using environment variables or a .env file.

### Design details

The system employs several software design patterns to ensure modularity, scalability, and maintainability:

- **Singleton** pattern: Used in the API's `global_state` to manage heavy resources (like the topic model), which are loaded only once upon application startup, preventing memory shortages and reducing inference latency.

- **Strategy** / **Factory** pattern: common interface for different file types and their respective processing, to be extended (e.g. PowerPoints, HTML... or videos)

- Heuristics: The PDF processor uses a multi-layered heuristic approach to score document quality before using expensive downstream LLM calls.


## Author

**Adriana R. Flórez**
*Computational Linguist & Software Engineer*
[GitHub Profile](https://github.com/adrmisty) | [LinkedIn](https://linkedin.com/in/adriana-rodriguez-florez)

---

*Built with ❤️ using Python, FastAPI, and BERTopic.*
