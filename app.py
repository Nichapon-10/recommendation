from __future__ import annotations

import base64
import html
import json
from datetime import date

import pandas as pd
import streamlit as st

from neo4j_service import (
    CATEGORIES,
    NONE_NAME,
    REGIONS,
    add_place,
    add_user,
    delete_place,
    delete_user,
    get_dashboard_metrics,
    get_profile,
    get_users,
    graph_neighborhood,
    list_categories,
    ping,
    recommend_places,
    reset_data,
    search_places,
    seed_demo_data,
    update_place,
    update_user,
    validate_place,
    validate_user,
)

PLACEHOLDER = "https://placehold.co/600x400/0EA5E9/FFF7ED?text=No+Image"

st.set_page_config(
    page_title="TravelGraph Recommender",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"], button, input, textarea {font-family:'Kanit',sans-serif !important;}
      .block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
      .hero {
        padding: 1.4rem 1.6rem; border-radius: 22px;
        background: linear-gradient(120deg, #0EA5E9 0%, #F97316 100%);
        color: white; margin-bottom: 1rem;
      }
      .hero h1 {margin:0; font-size:2.15rem; color:white;}
      .hero p {opacity:.9; margin:.35rem 0 0 0;}
      .card {background:#fff; border-radius:16px; box-shadow:0 4px 14px rgba(0,0,0,.12);
             overflow:hidden; margin-bottom:1rem; transition:transform .2s;}
      .card:hover {transform:scale(1.03);}
      .card img {width:100%; height:180px; object-fit:cover; display:block;}
      .card .body {padding:.8rem 1rem;}
      .book-card {padding:1rem 1.1rem; border:1px solid rgba(128,128,128,.25);
                  border-radius:16px; margin-bottom:.75rem; background:#fff;}
      .score-pill, .badge {display:inline-block; padding:.2rem .6rem; border-radius:999px;
                  background:#F97316; color:white; font-size:.8rem; font-weight:700;}
      .rec-card {display:flex; gap:1rem; align-items:stretch; background:#fff; border-radius:16px;
                 box-shadow:0 4px 14px rgba(0,0,0,.12); overflow:hidden; margin-bottom:1rem;
                 transition:transform .2s;}
      .rec-card:hover {transform:scale(1.01);}
      .rec-card img {width:260px; min-height:170px; object-fit:cover; flex-shrink:0;}
      .rec-card .rec-body {padding:.9rem 1.1rem .4rem 0;}
      .stars {color:#F59E0B;}
      .muted {opacity:.72; font-size:.9rem;}
      .avatar {width:64px; height:64px; border-radius:50%; object-fit:cover;}
    </style>
    """,
    unsafe_allow_html=True,
)


def require_connection() -> None:
    try:
        if not ping():
            raise RuntimeError("Neo4j did not return a healthy response")
    except Exception as exc:
        st.error("ยังเชื่อมต่อ Neo4j Aura ไม่สำเร็จ")
        st.code(
            '[neo4j]\nuri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"\n'
            'username = "neo4j"\npassword = "YOUR_PASSWORD"\ndatabase = "neo4j"',
            language="toml",
        )
        st.caption("ให้นำค่าด้านบนไปใส่ใน Streamlit Secrets และห้าม commit password ลง GitHub")
        st.exception(exc)
        st.stop()


def flash(msg: str) -> None:
    """เก็บข้อความสำเร็จไว้แสดงหลัง rerun"""
    st.session_state.flash = msg
    st.rerun()


def user_selector(key: str = "user") -> str:
    users = get_users()
    if not users:
        st.info("ยังไม่มีข้อมูลผู้ใช้ กรุณาไปหน้า Admin / Setup แล้วสร้างข้อมูลตัวอย่าง")
        st.stop()
    labels = {f"{x['user_id']} — {x['name']}": x["user_id"] for x in users}
    chosen = st.selectbox("เลือกผู้ใช้", list(labels), key=key)
    return labels[chosen]


def img_tag(url: str, cls: str = "") -> str:
    return (f'<img class="{cls}" src="{html.escape(url or PLACEHOLDER)}" '
            f"onerror=\"this.onerror=null;this.src='{PLACEHOLDER}'\">")


def stars(r: float) -> str:
    n = int(round(r or 0))
    return "★" * n + "☆" * (5 - n)


def place_card(p: dict) -> str:
    e = html.escape
    return (f"<div class='card'>{img_tag(p['image'])}<div class='body'>"
            f"<b>{e(p['name'])}</b> <span class='badge'>{e(p.get('category') or '-')}</span><br>"
            f"📍 {e(p['province'])} ({e(p['region'])})<br>"
            f"<span class='stars'>{stars(p['rating'])}</span> {p['rating']:.1f}<br>"
            f"<small>🗓 {e(p['best_time'])} · 👤 {e(p['recommender'])}</small><br>"
            f"<small>{e(p['description'])}</small></div></div>")


def explain_reason(row: dict) -> str:
    parts = []
    if row.get("friend_count", 0):
        friends = ", ".join(row.get("friend_names") or [])
        parts.append(f"เพื่อน {row['friend_count']} คนเคยแนะนำ" + (f" ({friends})" if friends else ""))
    if row.get("interest_matches", 0):
        cats = ", ".join(row.get("matched_categories") or [])
        parts.append(f"ตรงกับความสนใจ {row['interest_matches']} หมวด" + (f" ({cats})" if cats else ""))
    if row.get("popularity", 0):
        parts.append(f"หมวดนี้มีผู้สนใจ {row['popularity']} คน")
    if row.get("rating", 0):
        parts.append(f"เรตติ้ง {row['rating']:.1f}/5")
    return " • ".join(parts) or "แนะนำจากข้อมูลพฤติกรรมโดยรวม"


def place_form(key: str, p: dict | None = None):
    """ฟอร์มสถานที่ (ใช้ทั้งเพิ่มและแก้ไข) คืนค่า (submitted, data)"""
    p = p or {}
    users = get_users()
    opts = [""] + [u["user_id"] for u in users]
    names = {u["user_id"]: u["name"] for u in users}
    cats = list_categories() or CATEGORIES
    with st.form(key, clear_on_submit=(p == {})):
        name = st.text_input("ชื่อสถานที่", p.get("name", ""))
        c1, c2, c3 = st.columns(3)
        prov = c1.text_input("จังหวัด", p.get("province", ""))
        reg = c2.selectbox("ภาค", REGIONS, index=REGIONS.index(p["region"]) if p.get("region") in REGIONS else 0)
        cat = c3.selectbox("ประเภท", cats, index=cats.index(p["category"]) if p.get("category") in cats else 0)
        url = st.text_input("URL รูปภาพ", p.get("image", ""))
        up = st.file_uploader("หรืออัปโหลดรูป (ไม่เกิน 300 KB ถ้าเลือกจะใช้แทน URL)", type=["png", "jpg", "jpeg", "webp"])
        desc = st.text_area("คำบรรยาย", p.get("description", ""))
        c4, c5, c6 = st.columns(3)
        rating = c4.number_input("เรตติ้ง (1-5)", 0.0, 10.0, float(p.get("rating", 4.0)), 0.1)
        best = c5.text_input("ช่วงเวลาที่แนะนำ", p.get("best_time", ""))
        uid = c6.selectbox("ผู้แนะนำ", opts, format_func=lambda i: NONE_NAME if i == "" else names[i],
                           index=opts.index(p["user_id"]) if p.get("user_id") in opts else 0)
        ok = st.form_submit_button("💾 บันทึก")
    image = url.strip()
    if up:
        if up.size > 300_000:
            st.error("ไฟล์รูปใหญ่เกิน 300 KB")
            ok = False
        else:
            image = f"data:{up.type};base64,{base64.b64encode(up.getvalue()).decode()}"
    return ok, dict(name=name.strip(), province=prov.strip(), region=reg, category=cat, image=image,
                    description=desc.strip(), rating=float(rating), best_time=best.strip(), user_id=uid or None)


require_connection()

if "flash" in st.session_state:
    _msg = st.session_state.pop("flash")
    st.toast(_msg, icon="✅")
    st.success(_msg)

with st.sidebar:
    st.markdown("## 🌴 TravelGraph")
    st.caption("Neo4j Aura + Streamlit")
    page = st.radio(
        "เมนู",
        ["Dashboard", "Recommendations", "Place Search", "Manage Places",
         "Manage Users", "Graph Explorer", "Admin / Setup"],
    )
    st.divider()
    st.caption("Bachelor-level Graph Database Project")

st.markdown(
    """
    <div class="hero">
      <h1>🌴 TravelGraph Recommendation System</h1>
      <p>ระบบแนะนำสถานที่ท่องเที่ยวในไทยด้วย Graph Database ที่อธิบายเหตุผลของคำแนะนำได้</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if page == "Dashboard":
    st.subheader("ภาพรวมระบบ")
    m = get_dashboard_metrics()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Users", m.get("users", 0))
    c2.metric("Places", m.get("places", 0))
    c3.metric("Average rating", f"{m.get('avg_rating', 0):.2f}")
    c4.metric("Recommended relationships", m.get("recommends", 0))
    c5.metric("Friend relationships", m.get("friendships", 0))
    st.markdown("**จำนวนสถานที่แยกตามภาค**")
    st.bar_chart(pd.Series(m["by_region"]), color="#0EA5E9")

    st.divider()
    user_id = user_selector("dash_user")
    profile = get_profile(user_id)
    if profile:
        left, right = st.columns([1, 2])
        with left:
            st.markdown(img_tag(profile["avatar"], "avatar"), unsafe_allow_html=True)
            st.markdown(f"### {profile['name']}")
            st.write(f"**รหัส:** {profile['user_id']}")
            st.write(f"**สมัครเมื่อ:** {profile['joined']}")
            st.write(f"**bio:** {profile['bio']}")
            st.write("**ความสนใจ:** " + (", ".join(profile["interests"]) or "ยังไม่มี"))
        with right:
            st.markdown("### สถานที่ที่เคยแนะนำ")
            if profile["recommended"]:
                st.dataframe(pd.DataFrame(profile["recommended"]), use_container_width=True, hide_index=True)
            else:
                st.info("ยังไม่เคยแนะนำสถานที่")

elif page == "Recommendations":
    st.subheader("✨ สถานที่ที่แนะนำ")
    user_id = user_selector("rec_user")
    top_n = st.slider("จำนวนคำแนะนำ", 3, 12, 6)
    rows = recommend_places(user_id, top_n)

    st.caption("คะแนนตัวอย่าง = เพื่อน × 3 + หมวดความสนใจ × 2 + ความนิยม × 0.20 + rating × 0.50")
    if not rows:
        st.info("ยังไม่มีคำแนะนำสำหรับผู้ใช้นี้")
    for i, row in enumerate(rows, start=1):
        recs = ", ".join(row.get("recommenders") or []) or NONE_NAME
        categories = ", ".join(row.get("categories") or []) or "ไม่ระบุหมวด"
        st.markdown(
            f"""
            <div class="rec-card">
              {img_tag(row.get('image'))}
              <div class="rec-body">
                <span class="score-pill">#{i} · score {row['score']:.2f}</span>
                <h3 style="margin:.55rem 0 .2rem 0">{html.escape(row['name'])}</h3>
                <div class="muted">{row['place_id']} · {html.escape(row['province'])} ({row['region']}) · {categories} · แนะนำโดย {html.escape(recs)}</div>
                <div><span class="stars">{stars(row['rating'])}</span> {row['rating']:.1f} · 🗓 {html.escape(row.get('best_time') or '-')}</div>
                <small>{html.escape(row.get('description') or '')}</small>
                <p><b>เหตุผล:</b> {explain_reason(row)}</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

elif page == "Place Search":
    st.subheader("🔎 ค้นหาสถานที่")
    c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
    keyword = c1.text_input("ชื่อสถานที่หรือจังหวัด", placeholder="เช่น เชียงใหม่, กระบี่")
    region = c2.selectbox("ภาค", [""] + REGIONS, format_func=lambda x: "ทุกภาค" if x == "" else x)
    category = c3.selectbox("ประเภท", [""] + list_categories(), format_func=lambda x: "ทุกประเภท" if x == "" else x)
    min_rating = c4.slider("เรตติ้งขั้นต่ำ", 1.0, 5.0, 1.0, 0.1)
    sort = c5.selectbox("เรียงตาม", ["เรตติ้งสูงสุด", "ชื่อ A-Z", "ใหม่สุด"])
    rows = search_places(keyword, region, category, min_rating, sort)
    st.write(f"พบ {len(rows)} รายการ")
    if not rows:
        st.info("ไม่พบสถานที่ที่ตรงเงื่อนไข")
    for i in range(0, len(rows), 3):
        for col, p in zip(st.columns(3), rows[i:i + 3]):
            col.markdown(place_card(p), unsafe_allow_html=True)

elif page == "Manage Places":
    st.subheader("📝 เพิ่ม / แก้ไข / ลบสถานที่")
    t1, t2, t3 = st.tabs(["➕ เพิ่ม", "✏️ แก้ไข", "🗑️ ลบ"])
    places = search_places()
    with t1:
        ok, d = place_form("add_place")
        if ok:
            err = validate_place(d["name"], d["rating"])
            if err:
                st.error(err)
            else:
                add_place(d)
                flash(f"เพิ่มสถานที่ '{d['name']}' แล้ว")
    with t2:
        if not places:
            st.info("ยังไม่มีสถานที่")
        else:
            labels = {f"{p['place_id']} — {p['name']}": p for p in places}
            sel = labels[st.selectbox("เลือกสถานที่", list(labels), key="edit_place_sel")]
            ok, d = place_form(f"edit_place_{sel['place_id']}", sel)
            if ok:
                err = validate_place(d["name"], d["rating"])
                if err:
                    st.error(err)
                else:
                    update_place(sel["place_id"], d)
                    flash(f"แก้ไข '{d['name']}' แล้ว")
    with t3:
        if not places:
            st.info("ยังไม่มีสถานที่")
        else:
            labels = {f"{p['place_id']} — {p['name']}": p for p in places}
            sel = labels[st.selectbox("เลือกสถานที่ที่จะลบ", list(labels), key="del_place_sel")]
            conf = st.checkbox("ยืนยันการลบสถานที่นี้", key=f"cp_{sel['place_id']}")
            if st.button("🗑️ ลบสถานที่", disabled=not conf):
                delete_place(sel["place_id"])
                flash(f"ลบ '{sel['name']}' แล้ว")

elif page == "Manage Users":
    st.subheader("👥 เพิ่ม / แก้ไข / ลบผู้ใช้")
    t1, t2, t3, t4 = st.tabs(["📋 รายชื่อ", "➕ เพิ่ม", "✏️ แก้ไข", "🗑️ ลบ"])
    users = get_users()
    cats = list_categories() or CATEGORIES
    with t1:
        for u in users:
            c1, c2 = st.columns([1, 8])
            c1.markdown(img_tag(u["avatar"], "avatar"), unsafe_allow_html=True)
            c2.markdown(f"**{u['name']}** · แนะนำ {u['place_count']} แห่ง · สมัคร {u['joined']}  \n{u['bio']}")
    with t2:
        with st.form("add_user", clear_on_submit=True):
            name = st.text_input("ชื่อ")
            av = st.text_input("URL รูปโปรไฟล์")
            bio = st.text_area("bio สั้นๆ")
            interests = st.multiselect("ความสนใจ", cats)
            ok = st.form_submit_button("💾 บันทึก")
        if ok:
            err = validate_user(name)
            if err:
                st.error(err)
            else:
                add_user(name, av, bio, str(date.today()), interests)
                flash(f"เพิ่มผู้ใช้ '{name.strip()}' แล้ว")
    with t3:
        if users:
            labels = {f"{u['user_id']} — {u['name']}": u["user_id"] for u in users}
            uid = labels[st.selectbox("เลือกผู้ใช้", list(labels), key="edit_user_sel")]
            u = get_profile(uid)
            with st.form(f"edit_user_{uid}"):
                name = st.text_input("ชื่อ", u["name"])
                av = st.text_input("URL รูปโปรไฟล์", u["avatar"] or "")
                bio = st.text_area("bio", u["bio"] or "")
                interests = st.multiselect("ความสนใจ", cats, default=[c for c in u["interests"] if c in cats])
                ok = st.form_submit_button("💾 บันทึกการแก้ไข")
            if ok:
                err = validate_user(name, uid)
                if err:
                    st.error(err)
                else:
                    update_user(uid, name, av, bio, interests)
                    flash(f"แก้ไขผู้ใช้ '{name.strip()}' แล้ว")
    with t4:
        if users:
            labels = {f"{u['user_id']} — {u['name']}": u for u in users}
            u = labels[st.selectbox("เลือกผู้ใช้ที่จะลบ", list(labels), key="del_user_sel")]
            st.write(f"ผู้ใช้นี้แนะนำสถานที่ {u['place_count']} แห่ง")
            mode = st.radio("เมื่อลบผู้ใช้ ให้จัดการสถานที่อย่างไร?",
                            [f"ย้ายไป '{NONE_NAME}'", "ลบสถานที่ของเขาด้วย"], key=f"mode_{u['user_id']}")
            conf = st.checkbox("ยืนยันการลบผู้ใช้นี้", key=f"cu_{u['user_id']}")
            if st.button("🗑️ ลบผู้ใช้", disabled=not conf):
                delete_user(u["user_id"], mode.startswith("ลบ"))
                flash(f"ลบผู้ใช้ '{u['name']}' แล้ว")

elif page == "Graph Explorer":
    st.subheader("🕸️ Graph Explorer")
    user_id = user_selector("graph_user")
    rows = graph_neighborhood(user_id)
    if not rows:
        st.info("ยังไม่มี neighborhood graph")
    else:
        dot = ["digraph G {", 'rankdir="LR";', 'node [shape=box, style="rounded,filled", fillcolor="#FFF7ED"];']
        seen_nodes = set()
        for r in rows:
            for nid, label, name in [
                (r["source_id"], r["source_label"], r["source_name"]),
                (r["target_id"], r["target_label"], r["target_name"]),
            ]:
                if nid not in seen_nodes:
                    safe_name = str(name).replace('"', "'")
                    dot.append(f'"{nid}" [label="{safe_name}\\n:{label}"];')
                    seen_nodes.add(nid)
            dot.append(f'"{r["source_id"]}" -> "{r["target_id"]}" [label="{r["relationship"]}"];')
        dot.append("}")
        st.graphviz_chart("\n".join(dot), use_container_width=True)
        with st.expander("ดูข้อมูล edge ที่ใช้วาดกราฟ"):
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == "Admin / Setup":
    st.subheader("⚙️ Setup ข้อมูลตัวอย่าง")
    st.warning("ปุ่มสร้างข้อมูลไม่ลบข้อมูลเดิม และใช้ MERGE จึงสามารถกดซ้ำได้")
    st.markdown(
        """
        **Graph schema**
        - `(:User)-[:FRIEND_OF]-(:User)`
        - `(:User)-[:RECOMMENDED {recommended_date}]->(:Place)`
        - `(:User)-[:INTERESTED_IN]->(:Category)`
        - `(:Place)-[:IN_CATEGORY]->(:Category)`
        """
    )
    if st.button("สร้าง Constraint + Demo Data", type="primary", use_container_width=True):
        with st.spinner("กำลังสร้างข้อมูล..."):
            seed_demo_data()
        flash("สร้างข้อมูลตัวอย่างเรียบร้อยแล้ว")

    st.divider()
    st.markdown("**Export ข้อมูล**")
    users_all, places_all = get_users(), search_places()
    a, b, c, d = st.columns(4)
    a.download_button("places.csv", pd.DataFrame(places_all).to_csv(index=False).encode("utf-8-sig"), "places.csv")
    b.download_button("users.csv", pd.DataFrame(users_all).to_csv(index=False).encode("utf-8-sig"), "users.csv")
    c.download_button("places.json", json.dumps(places_all, ensure_ascii=False, indent=2), "places.json")
    d.download_button("users.json", json.dumps(users_all, ensure_ascii=False, indent=2), "users.json")

    st.divider()
    st.error("Reset จะลบ node และ relationship ทั้งหมดใน database แล้วสร้างข้อมูลตัวอย่างใหม่")
    conf = st.checkbox("ยืนยันการ Reset ข้อมูลทั้งหมด")
    if st.button("Reset กลับข้อมูลตั้งต้น", disabled=not conf):
        with st.spinner("กำลังรีเซ็ต..."):
            reset_data()
        flash("รีเซ็ตข้อมูลเรียบร้อย")
