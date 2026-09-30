from __future__ import annotations

from typing import Any

import streamlit as st
from neo4j import GraphDatabase, RoutingControl

REGIONS = ["เหนือ", "กลาง", "อีสาน", "ตะวันออก", "ตะวันตก", "ใต้"]
CATEGORIES = [
    "ทะเล",
    "ภูเขา",
    "วัด",
    "น้ำตก",
    "เมือง",
    "คาเฟ่"
]
NONE_NAME = "ไม่ระบุผู้แนะนำ"


def _config() -> tuple[str, str, str, str]:
    cfg = st.secrets["neo4j"]
    return (cfg["uri"], cfg["username"], cfg["password"], cfg.get("database", "neo4j"))


@st.cache_resource(show_spinner=False)
def get_driver():
    """Create one thread-safe Neo4j Driver for the Streamlit process."""
    uri, username, password, _ = _config()
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    return driver


def query(cypher: str, parameters: dict[str, Any] | None = None, *, write: bool = False) -> list[dict[str, Any]]:
    """Execute parameterized Cypher and return rows as dictionaries."""
    _, _, _, database = _config()
    records, _, _ = get_driver().execute_query(
        cypher,
        parameters_=parameters or {},
        database_=database,
        routing_=RoutingControl.WRITE if write else RoutingControl.READ,
    )
    return [record.data() for record in records]


def ping() -> bool:
    rows = query("RETURN 1 AS ok")
    return bool(rows and rows[0]["ok"] == 1)


def create_schema() -> None:
    statements = [
        "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
        "CREATE CONSTRAINT place_id_unique IF NOT EXISTS FOR (p:Place) REQUIRE p.place_id IS UNIQUE",
        "CREATE CONSTRAINT category_name_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",
    ]
    for stmt in statements:
        query(stmt, write=True)


SEED_USERS = [
    {
        "user_id": "U001",
        "name": "สมชาย ใจดี",
        "avatar": "https://i.pravatar.cc/150?img=11",
        "bio": "นักเดินทางสายภูเขา",
        "joined": "2025-01-10"
    },
    {
        "user_id": "U002",
        "name": "มาลี รักทะเล",
        "avatar": "https://i.pravatar.cc/150?img=12",
        "bio": "หลงรักหาดทรายและเกาะ",
        "joined": "2025-02-11"
    },
    {
        "user_id": "U003",
        "name": "ธนกร วัดงาม",
        "avatar": "https://i.pravatar.cc/150?img=13",
        "bio": "ชอบเที่ยววัดและวัฒนธรรม",
        "joined": "2025-03-12"
    },
    {
        "user_id": "U004",
        "name": "พิมพ์ชนก คาเฟ่",
        "avatar": "https://i.pravatar.cc/150?img=14",
        "bio": "ตามล่าคาเฟ่สวย",
        "joined": "2025-04-13"
    },
    {
        "user_id": "U005",
        "name": "ประวิทย์ น้ำตก",
        "avatar": "https://i.pravatar.cc/150?img=15",
        "bio": "สายลุยป่า น้ำตก",
        "joined": "2025-05-14"
    },
    {
        "user_id": "U006",
        "name": "นภัสสร เมืองเก่า",
        "avatar": "https://i.pravatar.cc/150?img=16",
        "bio": "ชอบเดินเมืองเก่า",
        "joined": "2025-06-15"
    },
    {
        "user_id": "U007",
        "name": "วีระ แบ็คแพ็ก",
        "avatar": "https://i.pravatar.cc/150?img=17",
        "bio": "แบ็คแพ็กทั่วไทย",
        "joined": "2025-07-16"
    },
    {
        "user_id": "U008",
        "name": "กมลา สายชิล",
        "avatar": "https://i.pravatar.cc/150?img=18",
        "bio": "เที่ยวช้าๆ ชิลๆ",
        "joined": "2025-08-17"
    },
    {
        "user_id": "U009",
        "name": "อนุชา ช่างภาพ",
        "avatar": "https://i.pravatar.cc/150?img=19",
        "bio": "ถ่ายภาพท่องเที่ยว",
        "joined": "2025-09-18"
    },
    {
        "user_id": "U010",
        "name": "ศิริพร ครอบครัว",
        "avatar": "https://i.pravatar.cc/150?img=20",
        "bio": "เที่ยวกับครอบครัว",
        "joined": "2025-01-10"
    }
]

SEED_PLACES = [
    {
        "place_id": "P001",
        "name": "ดอยอินทนนท์",
        "province": "เชียงใหม่",
        "region": "เหนือ",
        "category": "ภูเขา",
        "image": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=600&q=70",
        "description": "ยอดเขาสูงที่สุดในไทย อากาศเย็นตลอดปี",
        "rating": 4.8,
        "best_time": "พ.ย.-ก.พ.",
        "user_id": "U001",
        "created_at": "2026-08-01"
    },
    {
        "place_id": "P002",
        "name": "หาดไร่เลย์",
        "province": "กระบี่",
        "region": "ใต้",
        "category": "ทะเล",
        "image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&q=70",
        "description": "หาดสวยล้อมด้วยหน้าผาหินปูน",
        "rating": 4.7,
        "best_time": "พ.ย.-เม.ย.",
        "user_id": "U002",
        "created_at": "2026-08-02"
    },
    {
        "place_id": "P003",
        "name": "วัดร่องขุ่น",
        "province": "เชียงราย",
        "region": "เหนือ",
        "category": "วัด",
        "image": "https://images.unsplash.com/photo-1528181304800-259b08848526?w=600&q=70",
        "description": "วัดสีขาวงดงามสไตล์ร่วมสมัย",
        "rating": 4.6,
        "best_time": "ตลอดปี",
        "user_id": "U003",
        "created_at": "2026-08-03"
    },
    {
        "place_id": "P004",
        "name": "น้ำตกเอราวัณ",
        "province": "กาญจนบุรี",
        "region": "กลาง",
        "category": "น้ำตก",
        "image": "https://images.unsplash.com/photo-1432405972618-c60b0225b8f9?w=600&q=70",
        "description": "น้ำตกเจ็ดชั้นสีเขียวมรกต",
        "rating": 4.5,
        "best_time": "มิ.ย.-ต.ค.",
        "user_id": "U005",
        "created_at": "2026-08-04"
    },
    {
        "place_id": "P005",
        "name": "ย่านเมืองเก่าภูเก็ต",
        "province": "ภูเก็ต",
        "region": "ใต้",
        "category": "เมือง",
        "image": "https://images.unsplash.com/photo-1519451241324-20b4ea2c4220?w=600&q=70",
        "description": "ตึกชิโน-โปรตุกีสสีสันสดใส",
        "rating": 4.4,
        "best_time": "พ.ย.-มี.ค.",
        "user_id": "U006",
        "created_at": "2026-08-05"
    },
    {
        "place_id": "P006",
        "name": "คาเฟ่ริมน้ำเมืองน่าน",
        "province": "น่าน",
        "region": "เหนือ",
        "category": "คาเฟ่",
        "image": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=600&q=70",
        "description": "คาเฟ่วิวทุ่งนาและภูเขา",
        "rating": 4.3,
        "best_time": "ตลอดปี",
        "user_id": "U004",
        "created_at": "2026-08-06"
    },
    {
        "place_id": "P007",
        "name": "อยุธยาเมืองมรดกโลก",
        "province": "พระนครศรีอยุธยา",
        "region": "กลาง",
        "category": "วัด",
        "image": "https://images.unsplash.com/photo-1563492065599-3520f775eeed?w=600&q=70",
        "description": "โบราณสถานอายุหลายร้อยปี",
        "rating": 4.6,
        "best_time": "พ.ย.-ก.พ.",
        "user_id": "U007",
        "created_at": "2026-08-07"
    },
    {
        "place_id": "P008",
        "name": "เกาะเต่า",
        "province": "สุราษฎร์ธานี",
        "region": "ใต้",
        "category": "ทะเล",
        "image": "https://images.unsplash.com/photo-1506929562872-bb421503ef21?w=600&q=70",
        "description": "สวรรค์นักดำน้ำ น้ำใสมาก",
        "rating": 4.7,
        "best_time": "มี.ค.-ก.ย.",
        "user_id": "U008",
        "created_at": "2026-08-08"
    },
    {
        "place_id": "P009",
        "name": "ภูชี้ฟ้า",
        "province": "เชียงราย",
        "region": "เหนือ",
        "category": "ภูเขา",
        "image": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&q=70",
        "description": "ทะเลหมอกยามเช้า",
        "rating": 4.5,
        "best_time": "พ.ย.-ก.พ.",
        "user_id": "U009",
        "created_at": "2026-08-09"
    },
    {
        "place_id": "P010",
        "name": "อุทยานแห่งชาติเขาใหญ่",
        "province": "นครราชสีมา",
        "region": "อีสาน",
        "category": "น้ำตก",
        "image": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=600&q=70",
        "description": "ป่าดิบชื้นและน้ำตกเหวนรก",
        "rating": 4.4,
        "best_time": "มิ.ย.-ต.ค.",
        "user_id": "U010",
        "created_at": "2026-08-10"
    }
]

SEED_FRIENDS = [
    [
        "U001",
        "U002"
    ],
    [
        "U001",
        "U003"
    ],
    [
        "U002",
        "U004"
    ],
    [
        "U003",
        "U005"
    ],
    [
        "U004",
        "U006"
    ],
    [
        "U005",
        "U007"
    ],
    [
        "U006",
        "U008"
    ],
    [
        "U007",
        "U009"
    ],
    [
        "U008",
        "U010"
    ],
    [
        "U009",
        "U001"
    ]
]

SEED_INTERESTS = [
    [
        "U001",
        "ทะเล"
    ],
    [
        "U002",
        "ภูเขา"
    ],
    [
        "U003",
        "วัด"
    ],
    [
        "U004",
        "น้ำตก"
    ],
    [
        "U005",
        "เมือง"
    ],
    [
        "U006",
        "คาเฟ่"
    ],
    [
        "U007",
        "ทะเล"
    ],
    [
        "U008",
        "ภูเขา"
    ],
    [
        "U009",
        "วัด"
    ],
    [
        "U010",
        "น้ำตก"
    ],
    [
        "U001",
        "วัด"
    ],
    [
        "U002",
        "น้ำตก"
    ],
    [
        "U003",
        "เมือง"
    ],
    [
        "U004",
        "คาเฟ่"
    ],
    [
        "U005",
        "ทะเล"
    ],
    [
        "U006",
        "ภูเขา"
    ],
    [
        "U007",
        "วัด"
    ],
    [
        "U008",
        "น้ำตก"
    ],
    [
        "U009",
        "เมือง"
    ],
    [
        "U010",
        "คาเฟ่"
    ]
]


def seed_demo_data() -> None:
    """Idempotent sample dataset (10 users, 10 places): safe to run more than once."""
    create_schema()
    query(
        """
        UNWIND $rows AS row
        MERGE (u:User {user_id: row.user_id})
        SET u.name = row.name, u.avatar = row.avatar, u.bio = row.bio, u.joined = date(row.joined)
        """,
        {"rows": SEED_USERS}, write=True,
    )
    query("UNWIND $rows AS name MERGE (:Category {name:name})", {"rows": CATEGORIES}, write=True)
    query(
        """
        UNWIND $rows AS row
        MERGE (p:Place {place_id: row.place_id})
        SET p.name = row.name, p.province = row.province, p.region = row.region,
            p.image = row.image, p.description = row.description, p.rating = row.rating,
            p.best_time = row.best_time, p.created_at = date(row.created_at)
        WITH p, row
        MATCH (c:Category {name: row.category}) MERGE (p)-[:IN_CATEGORY]->(c)
        WITH p, row
        MATCH (u:User {user_id: row.user_id}) MERGE (u)-[r:RECOMMENDED]->(p)
        SET r.recommended_date = date(row.created_at)
        """,
        {"rows": SEED_PLACES}, write=True,
    )
    query(
        """
        UNWIND $rows AS row
        MATCH (a:User {user_id: row[0]}), (b:User {user_id: row[1]})
        MERGE (a)-[:FRIEND_OF]->(b)
        """,
        {"rows": SEED_FRIENDS}, write=True,
    )
    query(
        """
        UNWIND $rows AS row
        MATCH (u:User {user_id: row[0]}), (c:Category {name: row[1]})
        MERGE (u)-[:INTERESTED_IN]->(c)
        """,
        {"rows": SEED_INTERESTS}, write=True,
    )


def reset_data() -> None:
    """Delete every node/relationship, then seed the demo data again."""
    query("MATCH (n) DETACH DELETE n", write=True)
    seed_demo_data()


# ---------- Users ----------
def get_users() -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User)
        OPTIONAL MATCH (u)-[:RECOMMENDED]->(p:Place)
        RETURN u.user_id AS user_id, u.name AS name, u.avatar AS avatar, u.bio AS bio,
               toString(u.joined) AS joined, count(p) AS place_count
        ORDER BY u.user_id
        """
    )


def _next_id(label: str, prop: str, prefix: str) -> str:
    rows = query(f"MATCH (n:{label}) RETURN coalesce(max(toInteger(substring(n.{prop}, 1))), 0) AS m")
    return f"{prefix}{rows[0]['m'] + 1:03d}"


def _name_taken(name: str, user_id: str = "") -> bool:
    rows = query(
        "MATCH (u:User) WHERE toLower(trim(u.name)) = toLower(trim($name)) AND u.user_id <> $uid "
        "RETURN count(u) AS n",
        {"name": name, "uid": user_id},
    )
    return rows[0]["n"] > 0


def validate_user(name: str, user_id: str = "") -> str | None:
    if not name.strip():
        return "ห้ามเว้นชื่อว่าง"
    if _name_taken(name, user_id):
        return "ชื่อผู้ใช้นี้ซ้ำแล้ว"
    return None


def _set_interests(user_id: str, interests: list[str]) -> None:
    query(
        """
        MATCH (u:User {user_id:$uid})
        OPTIONAL MATCH (u)-[old:INTERESTED_IN]->(:Category) DELETE old
        WITH DISTINCT u
        UNWIND $cats AS name
        MATCH (c:Category {name:name}) MERGE (u)-[:INTERESTED_IN]->(c)
        """,
        {"uid": user_id, "cats": interests}, write=True,
    )


def add_user(name: str, avatar: str, bio: str, joined: str, interests: list[str]) -> None:
    uid = _next_id("User", "user_id", "U")
    query(
        "CREATE (:User {user_id:$uid, name:$name, avatar:$avatar, bio:$bio, joined:date($joined)})",
        {"uid": uid, "name": name.strip(), "avatar": avatar.strip(), "bio": bio.strip(), "joined": joined},
        write=True,
    )
    if interests:
        _set_interests(uid, interests)


def update_user(user_id: str, name: str, avatar: str, bio: str, interests: list[str]) -> None:
    query(
        "MATCH (u:User {user_id:$uid}) SET u.name=$name, u.avatar=$avatar, u.bio=$bio",
        {"uid": user_id, "name": name.strip(), "avatar": avatar.strip(), "bio": bio.strip()}, write=True,
    )
    _set_interests(user_id, interests)


def delete_user(user_id: str, delete_places: bool) -> None:
    """Delete a user; optionally delete their places (otherwise places become 'unspecified')."""
    if delete_places:
        query("MATCH (:User {user_id:$uid})-[:RECOMMENDED]->(p:Place) DETACH DELETE p",
              {"uid": user_id}, write=True)
    query("MATCH (u:User {user_id:$uid}) DETACH DELETE u", {"uid": user_id}, write=True)


def get_dashboard_metrics() -> dict[str, Any]:
    rows = query(
        """
        MATCH (u:User) WITH count(u) AS users
        MATCH (p:Place) WITH users, count(p) AS places, coalesce(avg(p.rating), 0.0) AS avg_rating
        OPTIONAL MATCH ()-[r:RECOMMENDED]->() WITH users, places, avg_rating, count(r) AS recommends
        OPTIONAL MATCH ()-[f:FRIEND_OF]->()
        RETURN users, places, avg_rating, recommends, count(f) AS friendships
        """
    )
    m = rows[0] if rows else {"users": 0, "places": 0, "avg_rating": 0.0, "recommends": 0, "friendships": 0}
    by_region = query("MATCH (p:Place) RETURN p.region AS region, count(p) AS n")
    m["by_region"] = {r: 0 for r in REGIONS} | {x["region"]: x["n"] for x in by_region}
    return m


def get_profile(user_id: str) -> dict[str, Any] | None:
    rows = query(
        """
        MATCH (u:User {user_id:$user_id})
        OPTIONAL MATCH (u)-[:INTERESTED_IN]->(c:Category)
        OPTIONAL MATCH (u)-[:RECOMMENDED]->(p:Place)
        RETURN u.user_id AS user_id, u.name AS name, u.avatar AS avatar, u.bio AS bio,
               toString(u.joined) AS joined,
               collect(DISTINCT c.name) AS interests,
               collect(DISTINCT {place_id:p.place_id, name:p.name, province:p.province, rating:p.rating}) AS recommended
        """,
        {"user_id": user_id},
    )
    if not rows:
        return None
    row = rows[0]
    row["recommended"] = [x for x in row["recommended"] if x.get("place_id")]
    return row


# ---------- Places ----------
def recommend_places(user_id: str, limit: int = 6) -> list[dict[str, Any]]:
    """Explainable hybrid score: social + interests + popularity + rating."""
    return query(
        """
        MATCH (u:User {user_id:$user_id})
        MATCH (p:Place)
        WHERE NOT (u)-[:RECOMMENDED]->(p)

        OPTIONAL MATCH (u)-[:FRIEND_OF]-(f:User)-[:RECOMMENDED]->(p)
        WITH u, p, count(DISTINCT f) AS friend_count,
             [x IN collect(DISTINCT f.name) WHERE x IS NOT NULL][0..3] AS friend_names

        OPTIONAL MATCH (u)-[:INTERESTED_IN]->(c:Category)<-[:IN_CATEGORY]-(p)
        WITH p, friend_count, friend_names,
             count(DISTINCT c) AS interest_matches,
             [x IN collect(DISTINCT c.name) WHERE x IS NOT NULL] AS matched_categories

        OPTIONAL MATCH (fan:User)-[:INTERESTED_IN]->(:Category)<-[:IN_CATEGORY]-(p)
        WITH p, friend_count, friend_names, interest_matches, matched_categories,
             count(fan) AS popularity

        WITH p, friend_count, friend_names, interest_matches, matched_categories, popularity,
             coalesce(p.rating, 0.0) AS rating,
             (friend_count * 3.0) + (interest_matches * 2.0) +
             (popularity * 0.20) + (coalesce(p.rating, 0.0) * 0.50) AS score
        WHERE friend_count > 0 OR interest_matches > 0 OR popularity > 0

        OPTIONAL MATCH (r:User)-[:RECOMMENDED]->(p)
        OPTIONAL MATCH (p)-[:IN_CATEGORY]->(allc:Category)
        RETURN p.place_id AS place_id, p.name AS name, p.province AS province, p.region AS region,
               p.image AS image, p.description AS description, p.best_time AS best_time,
               collect(DISTINCT r.name) AS recommenders,
               collect(DISTINCT allc.name) AS categories,
               friend_count, friend_names, interest_matches, matched_categories,
               popularity, rating,
               round(score * 100) / 100.0 AS score
        ORDER BY score DESC, p.name
        LIMIT $limit
        """,
        {"user_id": user_id, "limit": int(limit)},
    )


_SORTS = {"เรตติ้งสูงสุด": "p.rating DESC, p.name", "ชื่อ A-Z": "p.name", "ใหม่สุด": "p.created_at DESC, p.place_id DESC"}


def search_places(keyword: str = "", region: str = "", category: str = "",
                  min_rating: float = 1.0, sort: str = "เรตติ้งสูงสุด") -> list[dict[str, Any]]:
    return query(
        f"""
        MATCH (p:Place)
        OPTIONAL MATCH (p)-[:IN_CATEGORY]->(c:Category)
        OPTIONAL MATCH (u:User)-[:RECOMMENDED]->(p)
        WITH p, head(collect(DISTINCT c.name)) AS category, head(collect(DISTINCT u)) AS rec
        WHERE ($keyword = '' OR toLower(p.name) CONTAINS toLower($keyword)
               OR toLower(p.province) CONTAINS toLower($keyword))
          AND ($region = '' OR p.region = $region)
          AND ($category = '' OR category = $category)
          AND p.rating >= $min_rating
        RETURN p.place_id AS place_id, p.name AS name, p.province AS province, p.region AS region,
               category, p.image AS image, p.description AS description, p.rating AS rating,
               p.best_time AS best_time, rec.user_id AS user_id,
               coalesce(rec.name, $none) AS recommender, toString(p.created_at) AS created_at
        ORDER BY {_SORTS.get(sort, _SORTS["เรตติ้งสูงสุด"])}
        """,
        {"keyword": keyword.strip(), "region": region or "", "category": category or "",
         "min_rating": float(min_rating), "none": NONE_NAME},
    )


def list_categories() -> list[str]:
    return [row["name"] for row in query("MATCH (c:Category) RETURN c.name AS name ORDER BY c.name")]


def validate_place(name: str, rating: float) -> str | None:
    if not name.strip():
        return "ห้ามเว้นชื่อสถานที่ว่าง"
    if not 1 <= rating <= 5:
        return "เรตติ้งต้องอยู่ระหว่าง 1-5"
    return None


def _link_place(place_id: str, category: str, user_id: str | None, when: str | None = None) -> None:
    query(
        """
        MATCH (p:Place {place_id:$pid})
        OPTIONAL MATCH (p)-[old:IN_CATEGORY]->(:Category) DELETE old
        OPTIONAL MATCH (:User)-[old2:RECOMMENDED]->(p) DELETE old2
        WITH DISTINCT p
        MERGE (c:Category {name:$cat}) MERGE (p)-[:IN_CATEGORY]->(c)
        """,
        {"pid": place_id, "cat": category}, write=True,
    )
    if user_id:
        query(
            """
            MATCH (u:User {user_id:$uid}), (p:Place {place_id:$pid})
            MERGE (u)-[r:RECOMMENDED]->(p) SET r.recommended_date = coalesce(date($when), date())
            """,
            {"uid": user_id, "pid": place_id, "when": when}, write=True,
        )


def add_place(d: dict[str, Any]) -> None:
    pid = _next_id("Place", "place_id", "P")
    query(
        """
        CREATE (:Place {place_id:$pid, name:$name, province:$province, region:$region, image:$image,
                        description:$description, rating:$rating, best_time:$best_time,
                        created_at:date()})
        """,
        {"pid": pid, **{k: d[k] for k in ("name", "province", "region", "image", "description", "rating", "best_time")}},
        write=True,
    )
    _link_place(pid, d["category"], d["user_id"])


def update_place(place_id: str, d: dict[str, Any]) -> None:
    query(
        """
        MATCH (p:Place {place_id:$pid})
        SET p.name=$name, p.province=$province, p.region=$region, p.image=$image,
            p.description=$description, p.rating=$rating, p.best_time=$best_time
        """,
        {"pid": place_id, **{k: d[k] for k in ("name", "province", "region", "image", "description", "rating", "best_time")}},
        write=True,
    )
    _link_place(place_id, d["category"], d["user_id"])


def delete_place(place_id: str) -> None:
    query("MATCH (p:Place {place_id:$pid}) DETACH DELETE p", {"pid": place_id}, write=True)


def graph_neighborhood(user_id: str, limit: int = 40) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User {user_id:$user_id})
        OPTIONAL MATCH p=(u)-[:FRIEND_OF|RECOMMENDED|INTERESTED_IN|IN_CATEGORY*1..2]-(x)
        WITH u, collect(p)[0..$limit] AS paths
        UNWIND paths AS p
        UNWIND relationships(p) AS r
        WITH DISTINCT startNode(r) AS s, r, endNode(r) AS t
        RETURN elementId(s) AS source_id, labels(s)[0] AS source_label,
               coalesce(s.name, s.user_id, s.place_id) AS source_name,
               type(r) AS relationship,
               elementId(t) AS target_id, labels(t)[0] AS target_label,
               coalesce(t.name, t.user_id, t.place_id) AS target_name
        LIMIT $limit
        """,
        {"user_id": user_id, "limit": int(limit)},
    )
