import torch
from src.ontology.concept_space import ConceptSpace
from src.model.reasoner import LatentReasoner
from src.reasoning.rule_engine import Fact, RuleEngine


class ReasoningEngine:
    """Interfaz neuronal y simbolica del LCM."""
    def __init__(self, model: LatentReasoner, space: ConceptSpace, device: str = "cpu"):
        self.model = model.to(device)
        self.space = space
        self.device = device
        self.model.eval()
        self.rule_engine = RuleEngine()

    def think(self, premise_names: list, steps: int = 1) -> list:
        vectors = [self.space.get_vector(name) for name in premise_names]
        return self.think_vectors(vectors, steps=steps)

    def think_vectors(self, premise_vectors: list, steps: int = 1) -> list:
        if not premise_vectors:
            raise ValueError("Se necesita al menos una premisa.")
        if steps < 1:
            raise ValueError("steps debe ser >= 1.")
        history = []
        context = [torch.as_tensor(v, dtype=torch.float32).cpu() for v in premise_vectors]
        max_len = self.model.config.max_concept_seq
        with torch.no_grad():
            for _ in range(steps):
                selected = context[-max_len:]
                inp = torch.stack(selected).unsqueeze(0).to(self.device)
                mask = torch.ones(1, inp.shape[1], dtype=torch.bool, device=self.device)
                next_vec, _ = self.model(inp, attention_mask=mask)
                next_vec_cpu = next_vec.squeeze(0).cpu()
                history.append(next_vec_cpu)
                context.append(next_vec_cpu)
        return history

    def deduce(self, facts):
        """Cierre simbolico de hechos; util para pruebas y trazabilidad."""
        return self.rule_engine.infer(facts)
