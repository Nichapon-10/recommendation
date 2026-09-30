# TravelGraph Recommendation System

โปรเจ็คระบบแนะนำสถานที่ท่องเที่ยวในไทย ดัดแปลงจาก GraphBook (ระบบแนะนำหนังสือ)
พัฒนาด้วย **Streamlit + Neo4j Aura + Cypher** และ deploy ผ่าน **GitHub → Streamlit Community Cloud**

## 1. แนวคิดของระบบ

```text
(User)-[:FRIEND_OF]-(User)
(User)-[:RECOMMENDED {recommended_date}]->(Place)
(User)-[:INTERESTED_IN]->(Category)
(Place)-[:IN_CATEGORY]->(Category)
```

User 1 คนแนะนำได้หลายสถานที่ (one-to-many) แต่ละ Place ผูกกับผู้แนะนำ 1 คน
ถ้าลบ User สามารถเลือกลบสถานที่ของเขาด้วย หรือปล่อยเป็น "ไม่ระบุผู้แนะนำ" ได้

คำแนะนำอธิบายเหตุผลได้ (Explainable Recommendation) จาก
1. เพื่อนของผู้ใช้เคยแนะนำสถานที่นั้น
2. หมวดสถานที่ตรงกับความสนใจ
3. หมวดนั้นมีผู้สนใจมาก (popularity)
4. สถานที่มีเรตติ้งสูง

```text
score = friend_count*3 + interest_matches*2 + popularity*0.20 + rating*0.50
```

สูตรนี้เป็น heuristic เพื่อการเรียนการสอน

## 2. โครงสร้างไฟล์

```text
travel_graph_recommender/
├── app.py
├── neo4j_service.py
├── requirements.txt
├── .gitignore
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── cypher/
│   ├── schema.cypher
│   └── recommendation.cypher
└── docs/
    └── PROJECT_GUIDE_TH.md
```

## 3. สร้าง Neo4j Aura

1. สร้าง AuraDB instance
2. เก็บ Connection URI, username และ password
3. URI โดยทั่วไปอยู่ในรูป `neo4j+s://...databases.neo4j.io`
4. อย่านำ password ไปใส่ในไฟล์ที่ commit ขึ้น GitHub

## 4. รันในเครื่อง

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

ใส่ credential จริงใน `.streamlit/secrets.toml` แล้วรัน

```bash
streamlit run app.py
```

## 5. ครั้งแรกที่เปิดระบบ

1. เข้าเมนู **Admin / Setup**
2. กด **สร้าง Constraint + Demo Data** (10 users + 10 places, ใช้ `MERGE` กดซ้ำได้)
3. ทดลอง Dashboard, Recommendations, Place Search, Manage Places, Manage Users, Graph Explorer
4. ปุ่ม Reset ในหน้า Admin / Setup จะลบข้อมูลทั้งหมดแล้วสร้างข้อมูลตั้งต้นใหม่

## 6. Deploy GitHub → Streamlit Community Cloud

1. สร้าง GitHub repository ใหม่
2. push ไฟล์ทั้งหมด **ยกเว้น `.streamlit/secrets.toml`**
3. เข้า Streamlit Community Cloud → Create app เลือก repo, branch, entrypoint = `app.py`
4. Advanced settings → Secrets ใส่

```toml
[neo4j]
uri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"
username = "neo4j"
password = "YOUR_PASSWORD"
database = "neo4j"
```

5. Deploy

ข้อมูลอยู่ใน Neo4j Aura จึงไม่หายเมื่อ Streamlit Cloud reboot

## 7. ประเด็น Graph Database ที่ได้ฝึก

Node/Label/Property, Relationship, Constraint, `MATCH`/`MERGE`/`OPTIONAL MATCH`/`WITH`/`UNWIND`,
traversal ผ่านเพื่อน → สถานที่, aggregation (`count`, `avg`, `collect`), parameterized Cypher,
Python Driver, Streamlit UI, Secrets และ cloud deployment

## 8. ฟังก์ชันของระบบ

- CRUD ครบทั้ง User และ Place (เพิ่ม/แก้ไข/ลบ พร้อม confirm และ validation)
- ค้นหา, filter (ภาค/ประเภท/เรตติ้งขั้นต่ำ), เรียงลำดับ, แสดงเป็น card grid 3 คอลัมน์
- Dashboard: จำนวนสถานที่, ผู้ใช้, เรตติ้งเฉลี่ย, กราฟแท่งแยกตามภาค
- Export CSV/JSON และ Reset ข้อมูล
- รูปภาพ: ใช้ URL หรืออัปโหลดไฟล์ ถ้ารูปโหลดไม่ขึ้นจะแสดง placeholder

## 9. แนวทางต่อยอด

Login, Favorite/Wishlist, รีวิวและคะแนนจากผู้ใช้อื่น, collaborative filtering,
Graph Data Science, PageRank, community detection, Precision@K/Recall@K
