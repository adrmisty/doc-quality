# topics.py
# /analyzes relative belonging of a document's content in a topic model space/
# adriana r.f.
# jan-2026

from bertopic import BERTopic
from ...config.settings import Settings
from typing import Tuple, Dict, Any, Union

class DocTopic:
    """Assignment of a topic from the topic model space for a given document."""
    
    def __init__(self, config : Settings):
        self.model = BERTopic.load(
            path=str(config.topic_model), 
            embedding_model=config.embedding_model)
        self.min_prob = config.min_topic_prob

    def get_topic(self, content: Union[str, Dict[str, Any]], k: int = 3) -> Tuple[bool, Dict[str, Any]]:
        """Assigns top-k topics to a given document's text sorted by confidence."""
        # a) passing metadata
        if isinstance(content, dict):
            metadata_fields = [
                content.get("title", ""),
                content.get("subtitle", ""),
                content.get("description", ""),
                content.get("topic", ""),
                content.get("theme", ""),
                " ".join(content.get("keywords", []))
            ]
            text = " ".join(part for part in metadata_fields if part).strip()
            
        # b) passing just the full text
        else:
            text = content
            
        if not text.strip():
            return False, {"diagnose": "no valid text for topic assignment"}

        topic_indices, similarities = self.model.find_topics(text, top_n=k)
        
        assigned_topics = []

        for topic_id, score in zip(topic_indices, similarities):
            probability = float(score)
            if topic_id == -1:
                # high-confidence OUTLIERS
                if score >= self.min_prob:
                    break
                else:
                # low-confidence OUTLIERS
                    continue
            

            if probability >= self.min_prob:
                info = self.model.get_topic_info(topic_id)
                if not info.empty:
                    topic_name = info.iloc[0]["CustomName"]
                    assigned_topics.append({
                        "topic_id": int(topic_id),
                        "topic_name": topic_name,
                        "probability": probability
                    })

        # if any topics assigned ()
        is_valid = len(assigned_topics) > 0

        semantics = {
            "topics": assigned_topics
        }

        # outlier / probability < min_prob
        if not is_valid:
            semantics["topics"] = [{
                "topic_id": -1,
                "topic_name": "OUTLIERS"
            }]

        return is_valid, semantics