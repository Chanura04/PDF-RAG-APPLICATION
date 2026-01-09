from qdrant_client import QdrantClient

from qdrant_client.models import VectorParams, Distance, PointStruct


class QdrantStorage:
    def __init__(self, url="http://localhost:6333", collection="docs", dim=1024):
        self.client = QdrantClient(url=url, timeout=30)
        self.collection = collection
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=dim,  # Use the dim parameter
                    distance=Distance.COSINE
                )
            )

    def upsert(self, ids, vectors, payloads):
        points = [PointStruct(id=ids[i], vector=vectors[i], payload=payloads[i]) for i in range(len(ids))]
        self.client.upsert(self.collection, points=points)

    def search(self, query_vec, top_k, source_id=None):
        search_filter = None
        if source_id:
            search_filter = {
                "must": [
                    {
                        "key": "source",
                        "match": {"value": source_id}
                    }
                ]
            }
        results = self.client.query_points(
            collection_name=self.collection,
            prefetch=[],
            query=query_vec,
            with_payload=True,
            limit=top_k,
            query_filter=search_filter

        ).points
        context = []
        sources = set()

        for r in results:
            payload = getattr(r, "payload", None) or {}
            text = payload.get("text", None)
            source = payload.get("source", None)
            if text:
                context.append(text)
                sources.add(source)

        return {
            "contexts": context,
            "sources": list(sources)
        }
    # def search(self, query_vec, top_k, source_id=None):
    #     search_filter = None
    #     if source_id:
    #         search_filter = {
    #             "must": [
    #                 {
    #                     "key": "source",
    #                     "match": {"value": source_id}
    #                 }
    #             ]
    #         }
    #
    #     hits = self.client.search(
    #         collection_name="docs",
    #         query_vector=query_vec,
    #         limit=top_k,
    #         with_payload=True,
    #         query_filter=search_filter
    #     )
    #
    #     contexts = [h.payload["text"] for h in hits]
    #     sources = list({h.payload["source"] for h in hits})
    #     return {"contexts": contexts, "sources": sources}
    #


