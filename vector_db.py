from kivy.tools.benchmark import payload
from qdrant_client import QdrantClient
from qdrant_models import VectorParams, Distance, PointStruct

class QdrantStorage:
    def __init__(self,url="http://localhost:6333",collection="docs",dim=3072):
        self.client = QdrantClient(url=url,timeout=30)
        self.collection = collection
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                self.collection,
                VectorParams(dim=dim, distance=Distance.COSINE)
            )

    #     insert and update
    def upsert(self,ids,vectors,payloads):
        points=[PointStruct(id=ids[i],vector=vectors[i],payload=payloads[i] for i in range(len(ids)))]
        self.client.upsert(self.collection, points=points)

    def search(self,query_vectors,top_k:int= 5):
        result= self.client.search(
            collection_name= self.collection,
            query_vector= query_vectors,
            top_k=top_k,
            with_payloads=True
        )
        context=[]
        sources=set()

        for r in results:
            payload=getattr(r,"payload",None) or {}
            text=payload.get("text",None)
            source=payload.get("source",None)
            if text:
                context.append(text)
                sources.add(source)

        return {"context":context,"sources":list(sources)}