import torch
from src.ontology.concept_space import ConceptSpace

class ConceptDecoder:
    # La Boca: Inactiva durante el pensamiento. Solo traduce a lenguaje si se le pide
    def __init__(self, space: ConceptSpace):
        self.space = space

    def translate_thought(self, vector: torch.Tensor, lang: str = "es") -> dict:
        name, certainty = self.space.find_nearest_concept(vector.cpu())
        human_text = self.space.verbalize(name, lang=lang)
        return {
            "concept": name,
            "certainty": round(certainty * 100, 2),
            "text": human_text,
            "lang": lang
        }
