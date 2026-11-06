"""Ontologia conceptual con rasgos explicitos y proposiciones componibles.

Importante: los vectores ya no son identificadores aleatorios independientes.
Cada concepto se representa como una combinacion ponderada de rasgos
semanticos declarados. Las matrices de rol distinguen sujeto, predicado y
objeto al construir proposiciones.

Esta ontologia es explicita y auditable; no equivale por si sola a una
representacion semantica universal aprendida de grandes corpus.
"""
from __future__ import annotations

import hashlib
from typing import Dict, Iterable, Mapping, Optional, Tuple
import torch
import torch.nn.functional as F


class ConceptSpace:
    def __init__(self, d_concept: int = 128):
        if d_concept < 16:
            raise ValueError("d_concept debe ser >= 16 para una ontologia util.")
        self.d_concept = int(d_concept)
        self.concept_to_id: Dict[str, int] = {}
        self.id_to_concept: Dict[int, str] = {}
        self.translations: Dict[str, Dict[str, str]] = {}
        self.metadata: Dict[str, dict] = {}
        self.relations = []
        self.embeddings: Optional[torch.Tensor] = None
        self.feature_to_vector: Dict[str, torch.Tensor] = {}
        self.role_matrices: Dict[str, torch.Tensor] = {}
        self.proposition_vectors: Dict[str, torch.Tensor] = {}
        self.proposition_parts: Dict[str, Tuple[str, str, str]] = {}
        self.seed = 42

    @staticmethod
    def _normalise_features(features) -> Dict[str, float]:
        if features is None:
            return {}
        if isinstance(features, Mapping):
            result = {str(k): float(v) for k, v in features.items() if float(v) != 0.0}
        else:
            result = {str(k): 1.0 for k in features}
        if any(not torch.isfinite(torch.tensor(v)) for v in result.values()):
            raise ValueError("Los pesos de los rasgos deben ser finitos.")
        return result

    def register_concept(
        self,
        name: str,
        es_text: str = "",
        en_text: str = "",
        features=None,
        kind: str = "concept",
    ) -> None:
        name = str(name).strip().upper()
        if not name:
            raise ValueError("El nombre de un concepto no puede estar vacio.")
        feats = self._normalise_features(features)
        if not feats:
            # Compatibilidad con llamadas antiguas: no se inventa semantica
            # a partir del idioma; se conserva al menos una identidad estable.
            feats = {f"identity:{name}": 1.0}
        if name in self.concept_to_id:
            cid = self.concept_to_id[name]
            previous = self.metadata[name]["features"]
            if previous != feats:
                raise ValueError(f"El concepto {name} ya existe con otros rasgos.")
            if es_text:
                self.translations[name]["es"] = es_text
            if en_text:
                self.translations[name]["en"] = en_text
            return
        if self.embeddings is not None:
            raise RuntimeError("Registra todos los conceptos antes de build_space().")
        cid = len(self.concept_to_id)
        self.concept_to_id[name] = cid
        self.id_to_concept[cid] = name
        self.translations[name] = {"es": es_text or name, "en": en_text or name}
        self.metadata[name] = {"features": feats, "kind": str(kind)}

    def register_relation(self, subject: str, predicate: str, obj: str) -> None:
        """Registra una relacion simbolica (no crea automaticamente sus nodos)."""
        self.relations.append((str(subject).upper(), str(predicate).upper(), str(obj).upper()))

    def build_space(self, seed: int = 42) -> None:
        if not self.concept_to_id:
            raise RuntimeError("No hay conceptos registrados.")
        self.seed = int(seed)
        generator = torch.Generator(device="cpu")
        generator.manual_seed(self.seed)

        feature_names = sorted({
            feature
            for meta in self.metadata.values()
            for feature in meta["features"]
        })
        # Cada rasgo recibe un vector determinista que depende SOLO de su nombre y de
        # la semilla (parche-12). Asi se pueden anadir conceptos despues de entrenar
        # sin alterar los vectores de los ya existentes.
        self.feature_to_vector = {name: self._feature_vector(name) for name in feature_names}

        rows = []
        for cid in range(len(self.id_to_concept)):
            name = self.id_to_concept[cid]
            feats = self.metadata[name]["features"]
            vector = torch.zeros(self.d_concept)
            for feature, weight in feats.items():
                vector += float(weight) * self.feature_to_vector[feature]
            rows.append(F.normalize(vector, p=2, dim=-1))
        self.embeddings = torch.stack(rows)

        # Transformaciones ortogonales deterministas para codificar los roles.
        role_generator = torch.Generator(device="cpu")
        role_generator.manual_seed(self.seed + 104729)
        self.role_matrices = {}
        for role in ("subject", "predicate", "object"):
            raw = torch.randn(self.d_concept, self.d_concept, generator=role_generator)
            q, _ = torch.linalg.qr(raw)
            self.role_matrices[role] = q.contiguous()

        self.proposition_vectors = {}
        self.proposition_parts = {}

    def _feature_vector(self, feature: str) -> torch.Tensor:
        digest = hashlib.sha256(f"{self.seed}:{feature}".encode("utf-8")).hexdigest()
        generator = torch.Generator(device="cpu")
        generator.manual_seed(int(digest[:12], 16))
        return F.normalize(torch.randn(self.d_concept, generator=generator), p=2, dim=-1)

    def add_concept(self, name: str, es_text: str = "", en_text: str = "", features=None,
                    kind: str = "concept") -> int:
        """Anade un concepto NUEVO a un espacio ya construido (catalogo abierto).

        Los vectores existentes no cambian. Despues hay que llamar a
        model.set_space(space) para que el lector de ranuras conozca el concepto."""
        if self.embeddings is None:
            raise RuntimeError("Ejecuta build_space() antes de add_concept().")
        name = str(name).strip().upper()
        if not name:
            raise ValueError("El nombre de un concepto no puede estar vacio.")
        if name in self.concept_to_id:
            return self.concept_to_id[name]
        feats = self._normalise_features(features) or {f"identity:{name}": 1.0}
        vector = torch.zeros(self.d_concept)
        for feature, weight in feats.items():
            if feature not in self.feature_to_vector:
                self.feature_to_vector[feature] = self._feature_vector(feature)
            vector += float(weight) * self.feature_to_vector[feature]
        cid = len(self.concept_to_id)
        self.concept_to_id[name] = cid
        self.id_to_concept[cid] = name
        self.translations[name] = {"es": es_text or name, "en": en_text or name}
        self.metadata[name] = {"features": feats, "kind": str(kind)}
        self.embeddings = torch.cat([self.embeddings, F.normalize(vector, p=2, dim=-1).unsqueeze(0)], dim=0)
        return cid

    def get_vector(self, name: str) -> torch.Tensor:
        name = str(name).strip().upper()
        if name in self.concept_to_id:
            if self.embeddings is None:
                raise RuntimeError("Ejecuta build_space() antes de solicitar vectores.")
            return self.embeddings[self.concept_to_id[name]].clone()
        if name in self.proposition_vectors:
            return self.proposition_vectors[name].clone()
        raise KeyError(f"Concepto o proposicion no registrado: {name}")

    @staticmethod
    def proposition_label(subject: str, predicate: str, obj: str) -> str:
        return f"{subject.upper()}::{predicate.upper()}::{obj.upper()}"

    def encode_proposition(self, subject: str, predicate: str, obj: str) -> torch.Tensor:
        """Compone (sujeto, predicado, objeto) en un vector con roles."""
        if self.embeddings is None or not self.role_matrices:
            raise RuntimeError("Ejecuta build_space() antes de codificar proposiciones.")
        s, p, o = subject.upper(), predicate.upper(), obj.upper()
        label = self.proposition_label(s, p, o)
        if label not in self.proposition_vectors:
            vector = (
                self.role_matrices["subject"] @ self.get_vector(s)
                + self.role_matrices["predicate"] @ self.get_vector(p)
                + self.role_matrices["object"] @ self.get_vector(o)
            )
            self.proposition_vectors[label] = F.normalize(vector, p=2, dim=-1).cpu()
            self.proposition_parts[label] = (s, p, o)
        return self.proposition_vectors[label].clone()

    def find_nearest_concept(self, vector: torch.Tensor) -> tuple:
        """Devuelve la etiqueta mas proxima y su similitud coseno.

        El segundo valor es similitud geometrica, NO una probabilidad ni una
        certeza calibrada.
        """
        if self.embeddings is None:
            raise RuntimeError("Ejecuta build_space() antes de buscar conceptos.")
        query = F.normalize(vector.detach().view(1, -1).float().cpu(), p=2, dim=-1)
        candidates = [self.embeddings]
        labels = [self.id_to_concept[i] for i in range(len(self.id_to_concept))]
        if self.proposition_vectors:
            prop_labels = sorted(self.proposition_vectors)
            candidates.append(torch.stack([self.proposition_vectors[k] for k in prop_labels]))
            labels.extend(prop_labels)
        matrix = torch.cat(candidates, dim=0)
        similarities = query @ matrix.t()
        best_id = int(torch.argmax(similarities, dim=-1).item())
        return labels[best_id], float(similarities[0, best_id].item())

    def verbalize(self, name: str, lang: str = "es") -> str:
        name = str(name).upper()
        if name in self.proposition_parts:
            s, p, o = self.proposition_parts[name]
            if lang == "en":
                return f"{s} {p} {o}"
            return f"{s} {p} {o}"
        return self.translations.get(name, {}).get(lang, f"[{name}]")

    def list_concepts(self, limit: Optional[int] = None):
        names = list(self.concept_to_id)
        return names if limit is None else names[:limit]

