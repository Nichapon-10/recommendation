// Explainable Hybrid Place Recommendation
// Parameters: $user_id, $limit
MATCH (u:User {user_id:$user_id})
MATCH (p:Place)
WHERE NOT (u)-[:RECOMMENDED]->(p)

// 1) Social signal: places recommended by friends
OPTIONAL MATCH (u)-[:FRIEND_OF]-(f:User)-[:RECOMMENDED]->(p)
WITH u, p,
     count(DISTINCT f) AS friend_count,
     [x IN collect(DISTINCT f.name) WHERE x IS NOT NULL][0..3] AS friend_names

// 2) Content signal: categories matching the user's interests
OPTIONAL MATCH (u)-[:INTERESTED_IN]->(c:Category)<-[:IN_CATEGORY]-(p)
WITH p, friend_count, friend_names,
     count(DISTINCT c) AS interest_matches,
     [x IN collect(DISTINCT c.name) WHERE x IS NOT NULL] AS matched_categories

// 3) Popularity signal: users interested in the place's category
OPTIONAL MATCH (fan:User)-[:INTERESTED_IN]->(:Category)<-[:IN_CATEGORY]-(p)
WITH p, friend_count, friend_names, interest_matches, matched_categories,
     count(fan) AS popularity

// 4) Teaching-friendly heuristic score (rating is a Place property)
WITH p, friend_count, friend_names, interest_matches, matched_categories,
     popularity, coalesce(p.rating, 0.0) AS rating,
     (friend_count * 3.0) +
     (interest_matches * 2.0) +
     (popularity * 0.20) +
     (coalesce(p.rating, 0.0) * 0.50) AS score
WHERE friend_count > 0 OR interest_matches > 0 OR popularity > 0

OPTIONAL MATCH (r:User)-[:RECOMMENDED]->(p)
OPTIONAL MATCH (p)-[:IN_CATEGORY]->(allc:Category)
RETURN p.place_id AS place_id,
       p.name AS name,
       p.image AS image,
       p.description AS description,
       p.best_time AS best_time,
       collect(DISTINCT r.name) AS recommenders,
       collect(DISTINCT allc.name) AS categories,
       friend_count,
       friend_names,
       interest_matches,
       matched_categories,
       popularity,
       rating,
       round(score * 100) / 100.0 AS score
ORDER BY score DESC, p.name
LIMIT $limit;
