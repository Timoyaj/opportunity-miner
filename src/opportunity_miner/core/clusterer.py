"""Incremental centroid-based clustering engine."""

from datetime import datetime
import uuid
import numpy as np
from sqlalchemy.orm import Session

from ..database.models import ExtractedProblem, ProblemCluster
from .vector_store import VectorStore


class IncrementalClusterer:
    """Assigns extracted problems to existing cluster centroids or seeds new clusters."""

    def __init__(self, vector_store: VectorStore, match_threshold: float = 0.82, new_cluster_threshold: float = 0.80, min_cluster_size: int = 3):
        self.vector_store = vector_store
        self.match_threshold = match_threshold
        self.new_cluster_threshold = new_cluster_threshold
        self.min_cluster_size = min_cluster_size

    def cluster_problem(self, problem: ExtractedProblem, db: Session) -> ProblemCluster:
        """Assign an extracted problem to an existing cluster or create/update clusters."""
        prob_vec = self.vector_store.bytes_to_vector(problem.embedding)

        # 1. Fetch active clusters
        active_clusters = db.query(ProblemCluster).all()

        best_cluster = None
        best_sim = -1.0

        for cluster in active_clusters:
            if cluster.centroid_embedding:
                c_vec = self.vector_store.bytes_to_vector(cluster.centroid_embedding)
                sim = self.vector_store.cosine_similarity(prob_vec, c_vec)
                if sim > best_sim:
                    best_sim = sim
                    best_cluster = cluster

        # 2. Check if it matches existing cluster centroid
        if best_cluster and best_sim >= self.match_threshold:
            # Update running centroid
            c_vec = self.vector_store.bytes_to_vector(best_cluster.centroid_embedding)
            n = best_cluster.mention_count
            updated_c_vec = (n * c_vec + prob_vec) / (n + 1)
            norm = np.linalg.norm(updated_c_vec)
            if norm > 1e-6:
                updated_c_vec = updated_c_vec / norm

            best_cluster.centroid_embedding = self.vector_store.vector_to_bytes(updated_c_vec)
            best_cluster.mention_count += 1
            best_cluster.last_seen_at = datetime.utcnow()

            # Update velocity
            days_active = max(1, (best_cluster.last_seen_at - best_cluster.first_seen_at).days)
            best_cluster.trend_velocity = round((best_cluster.mention_count / days_active) * 7, 2)

            problem.cluster_id = best_cluster.id
            db.commit()
            return best_cluster

        # 3. If no match, check unclustered problems pool
        unclustered = db.query(ExtractedProblem).filter(
            ExtractedProblem.cluster_id.is_(None),
            ExtractedProblem.id != problem.id
        ).all()

        similar_unclustered = []
        for other in unclustered:
            o_vec = self.vector_store.bytes_to_vector(other.embedding)
            sim = self.vector_store.cosine_similarity(prob_vec, o_vec)
            if sim >= self.new_cluster_threshold:
                similar_unclustered.append(other)

        # 4. If enough similar unclustered problems exist, form a new cluster
        if len(similar_unclustered) + 1 >= self.min_cluster_size:
            cluster_id = f"CL-{uuid.uuid4().hex[:6].upper()}"
            
            # Compute centroid of the group
            group_vectors = [prob_vec] + [self.vector_store.bytes_to_vector(o.embedding) for o in similar_unclustered]
            group_centroid = np.mean(group_vectors, axis=0)
            norm = np.linalg.norm(group_centroid)
            if norm > 1e-6:
                group_centroid = group_centroid / norm

            title = problem.problem_statement[:60]
            if len(problem.problem_statement) > 60:
                title += "..."

            new_cluster = ProblemCluster(
                id=cluster_id,
                title=f"Workflow: {title}",
                description=problem.underlying_problem,
                centroid_embedding=self.vector_store.vector_to_bytes(group_centroid),
                mention_count=len(group_vectors),
                unique_sources=len(set([problem.signal.source] + [o.signal.source for o in similar_unclustered if o.signal])),
                first_seen_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
                trend_velocity=float(len(group_vectors))
            )
            db.add(new_cluster)
            db.flush()

            problem.cluster_id = new_cluster.id
            for o in similar_unclustered:
                o.cluster_id = new_cluster.id

            db.commit()
            return new_cluster

        # 5. Otherwise create single-problem incubation cluster if needed
        cluster_id = f"CL-{uuid.uuid4().hex[:6].upper()}"
        title = problem.problem_statement[:60]
        if len(problem.problem_statement) > 60:
            title += "..."

        incubation_cluster = ProblemCluster(
            id=cluster_id,
            title=f"Workflow: {title}",
            description=problem.underlying_problem,
            centroid_embedding=self.vector_store.vector_to_bytes(prob_vec),
            mention_count=1,
            unique_sources=1,
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            trend_velocity=1.0
        )
        db.add(incubation_cluster)
        db.flush()
        problem.cluster_id = incubation_cluster.id
        db.commit()
        return incubation_cluster
