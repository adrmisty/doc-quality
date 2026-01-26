# llm.py
# /LLM setup for generation of custom topic labels/
# adriana r.f.
# jan-2026

import torch
import re
from transformers import pipeline
from bertopic.representation import TextGeneration
from ...config.settings import Settings

class TopicLLM:
    """LLM set-up for generation of custom labels in BERTopic representation."""
    
    def __init__(self, config: Settings):
        self.config = config
        self.targets = self.config.topic_targets
        self.model_name = self.config.llm_model

    def text_generation(self) -> TextGeneration:
        """Initializes and returns the TextGeneration representation model."""
        
        print(f"> [Topic modeling] Setting up LLM [{self.model_name}] for label generation")
        
        if not torch.cuda.is_available():
            print("    > Warning: No GPU detected :( this step could be slow or fail!")

        # HuggingFace text gen
        generator = pipeline(
            "text-generation",
            model=self.model_name,
            model_kwargs={"dtype": torch.float16 if torch.cuda.is_available() else torch.float32},
            device_map="auto",
            max_new_tokens=50,
            return_full_text=False,
            trust_remote_code=True
        )

        prompt = self._get_prompt()
        return _CleanedTextGen(generator, prompt=prompt, targets=self.targets)

    def _get_prompt(self) -> str:
        """Builds the prompt enforcing strict target matching."""
        targs = ', '.join(self.targets)
        return f"""Choose ONE category for these documents: {targs}. Output only the word. Documents: [DOCUMENTS]. Category:"""


class _CleanedTextGen(TextGeneration):
    """Custom representation model to enforce clean label output based on taxonomy."""
    
    def __init__(self, model, prompt, targets):
        self.targets = targets
        super().__init__(
            model,
            prompt=prompt,
            doc_length=150,
            tokenizer="whitespace"
        )

    def extract_label(self, output_text):
        """Clean LLM output to avoid artifacts and ugly stuff."""
        return self._clean_label(output_text)    
    
    def __call__(self, topic_model, docs, topics, embeddings):
        """Override to apply extraction to all topics."""
        raw_outputs = super().__call__(topic_model, docs, topics, embeddings)
        return {
            t_id: [self.extract_label(text) for text in texts]
            for t_id, texts in raw_outputs.items()
        }
        
    def _clean_label(self, text: str) -> str:    
        """Matches output text against the specific targets."""
        clean_text = re.sub(r'[^a-zA-Z\s]', ' ', text.lower())
        for target in self.targets:
            if re.search(rf"\b{target.lower()}\b", clean_text):
                return target.upper()
        return "OUTLIERS"