from pymilvus import connections, Collection, utility

connections.connect(host="localhost", port="19530")

collection_name = "papers"

if not utility.has_collection(collection_name):
    print(f"❌ Collection '{collection_name}' 없음")
    exit(1)

collection = Collection(collection_name)
collection.load()

# 통계
count = collection.num_entities
print(f"✅ Collection: {collection_name}")
print(f"   총 청크 수: {count}")

# 스키마
print(f"\n스키마:")
for field in collection.schema.fields:
    print(f"   - {field.name} ({field.dtype.name})")

# 문서별 청크 수
print(f"\n문서별 청크 분포:")
results = collection.query(
    expr="id > 0",
    output_fields=["doc_name"],
    limit=10000,
)

from collections import Counter
doc_counts = Counter(r["doc_name"] for r in results)
for doc, cnt in sorted(doc_counts.items()):
    print(f"   {doc}: {cnt} chunks")
