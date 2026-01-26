# trainer.py
# /training of the topic model/
# adriana r.f.
# jan-2026

from pathlib import Path
import numpy as np
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS

# bertopic settings
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN

from ...config.settings import Settings
from .llm import TopicLLM
from .utils import load_docs, save_model

class DocTopicTrainer:
    """Training of a BERTopic model on a dataset of documents' metadata."""
    def __init__(self, config: Settings):
        self.config = config
        self.embed_model_name = getattr(config, "embedding_model", 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
        self.targets = self.config.topic_targets
        # metadata fields that will be passed as relevant context for topic modeling
        self.fields = ['title', 'topic', 'theme', 'description'] 

    def train(self, input_dir: Path, output_dir: Path):
        """Main training loop for BERTopic modeling on EUFB Knowledge Object metadata."""
        
        # load document relevant metadata
        docs, filenames, meta = load_docs(input_dir, self.fields)
        n_docs = len(docs)
        if not docs:
            print("    > Warning: No valid documents found for topic model training.")
            return

        # configure hyperparameters based on dataset size
        params = self._hyperparams(n_docs)

        # set up for embedding model
        embedding_model, embeddings = self._embed(docs)

        # reduce embedding dims
        umap_model = UMAP(
            n_neighbors=params['n_neighbors'],
            n_components=10, # target dims
            min_dist=0.0,
            metric="cosine",
            random_state=42
        )

        # hierarchical clustering
        hdbscan_model = HDBSCAN(
            min_cluster_size=params['min_cluster_size'],
            min_samples=params['min_samples'],
            metric='euclidean',
            cluster_selection_method='eom',
            prediction_data=True
        )

        # vectorization of documents
        vectorizer_model = self._get_vectorizer(n_docs)
        
        # topic representations: BERTopic, keyword similarity, custom labeling with LLM
        representation_model = {
            "KeyBERT": KeyBERTInspired(top_n_words=20, nr_candidate_words=100),
            "MMR": MaximalMarginalRelevance(diversity=0.3),
            "LLM": TopicLLM(self.config).text_generation()
        }

        # init and train model with all settings above
        topic_model = BERTopic(
            min_topic_size=params['min_cluster_size'],
            embedding_model=embedding_model,
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            representation_model=representation_model,
            vectorizer_model=vectorizer_model,
            language="multilingual",
            verbose=True,
            calculate_probabilities=True
        )

        print(f"> [Topic modeling] Training model on {n_docs} Knowledge Objects...")
        topics, probs = topic_model.fit_transform(docs, embeddings=embeddings)

        # post-processing (outlier reduction + labeling)
        topic_model = self._postprocess_model(topic_model, docs, topics, probs, meta)

        # saving and visualizing
        save_model(topic_model, output_dir, docs, filenames)
        self._visualize(topic_model, output_dir, docs, embeddings)

    # ---------------------------------------------------------------------------------------

    def _hyperparams(self, n_docs: int) -> dict:
        """Dynamic hyperparameter setting based on dataset size."""
        if n_docs > 1000:
            return {"min_cluster_size": 5, "min_samples": 5, "n_neighbors": 10}
        elif 100 <= n_docs <= 1000:
            return {"min_cluster_size": 5, "min_samples": 5, "n_neighbors": 10}
        else:
            return {"min_cluster_size": 3, "min_samples": 1, "n_neighbors": 3}

    def _embed(self, docs: list) -> tuple:
        """Embedding model set-up"""
        print(f"> [Topic modeling] Using embedding model: {self.embed_model_name}")
        model = SentenceTransformer(self.embed_model_name)
        embeddings = model.encode(docs, show_progress_bar=True)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True) # normalize
        return model, embeddings

    def _get_vectorizer(self, n_docs: int) -> CountVectorizer:
        """Feature extraction and ignoring stop-words for text n-grams in documents. """
        base_stops = list(ENGLISH_STOP_WORDS)
        custom_stops = [
            'co', 'https', 'http', 'www', 'com', 'org', 'project', 'abstract',
            'practice', 'guide', 'factsheet', 'report', 'results', 'summaries',
            'details', 'outlines', 'presents', 'description', 'information',
            'using', 'highlights', 'includes', 'aims', 'provides', 'used'
        ]
        min_df = 2 if n_docs > 500 else 1
        return CountVectorizer(
            min_df=min_df,
            max_df=0.5,
            stop_words=base_stops + custom_stops,
            token_pattern=r"(?u)\b[a-zA-Z]{4,}\b",
            ngram_range=(1, 3)
        )

    def _visualize(self, model, output_dir, docs, embeddings):
        """Graph/topic model space visualizaion."""
        try:
            viz = model.visualize_documents(docs, embeddings=embeddings, custom_labels=True)
            viz.write_html(output_dir / "document_dist_map.html")
            print(f"> [Topic modeling] Saved visualizations to {output_dir}")
        except Exception:
            pass

    # ---------------------------------------------------------------------------------------

    def _postprocess_model(self, model, docs, topics, probs, meta):
        """Outlier reduction and custom labeling for trained model."""
        n_docs = len(docs)
        
        # if confident enough, reduce outliers with c-tf-idf
        if probs is not None and n_docs >= 50:
            new_topics = model.reduce_outliers(docs, topics, strategy="c-tf-idf", threshold=0.1)
            model.update_topics(docs, topics=new_topics)

        # optional for now
        # model.reduce_topics(docs, nr_topics="auto")

        # custom labeling with llm
        topic_info = model.get_topic_info()
        all_reprs = model.get_topics(full=True)
        current_topics = model.topics_
        
        labels = {}
        for row in topic_info.itertuples():
            t_id = row.Topic
            if t_id == -1:
                labels[t_id] = "OUTLIERS"
                continue
            
            # CATEGORY (from metadata) + besy keyword (from MMR/KeyBERT)
            category = self._get_meta_category(t_id, current_topics, meta)
            keyword = self._get_best_keyword(all_reprs, t_id, category)
            
            labels[t_id] = f"{category}: {keyword}"
            
        model.set_topic_labels(labels)
        return model

    def _get_meta_category(self, t_id, topics, meta):
        """Retrieves the most common target topic assigned in metadata for documents in this cluster."""
        cluster_labels = [
            meta[i].get("topic", "").strip().upper()
            for i, t in enumerate(topics)
            if t == t_id and meta[i].get("topic")
        ]
        if not cluster_labels: return "UNKNOWN"
        return Counter(cluster_labels).most_common(1)[0][0]

    def _get_best_keyword(self, all_reprs, t_id, category):
        """Retrieves the best, most comprehensive keyword, for documents in this cluster. """
        # best MMR, then the Main BERTopic
        raw = all_reprs.get("MMR", {}).get(t_id, []) or all_reprs.get("Main", {}).get(t_id, [])
        
        candidates = []
        for item in raw[:10]:
            word = item[0] if isinstance(item, tuple) else str(item)
            candidates.append(word)
            
        valid = [c for c in candidates if c.lower() not in category.lower() and len(c) > 3]
        if valid:
            return max(valid, key=len) # Longest valid keyword
        return candidates[0] if candidates else "general"