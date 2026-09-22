from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import get_db_connection
from typing import Optional


app = FastAPI(
    title="Hidden India API",
    description="API for discovering lesser-known destinations across India",
    version="1.0.0"
)


# =========================================================
# CORS
# Allows the frontend website to communicate with this API
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================================================
# HOME / HEALTH CHECK
# =========================================================

@app.get("/")
def home():
    return {
        "message": "Welcome to Hidden India API",
        "status": "Backend is running"
    }


# =========================================================
# GET ALL DESTINATIONS
# =========================================================

@app.get("/destinations")
def get_destinations():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                id,
                slug,
                name,
                state,
                region,
                tagline,
                type,
                budget,
                budget_label,
                duration_days,
                best_season,
                difficulty,
                crowd,
                alternative_to,
                latitude,
                longitude
            FROM destinations
            ORDER BY name
        """)

        destinations = cursor.fetchall()

        return {
            "count": len(destinations),
            "destinations": destinations
        }

    finally:
        cursor.close()
        conn.close()


# =========================================================
# FILTER DESTINATIONS
#
# Supported filters:
# state
# max_budget
# duration
# difficulty
# type
# crowd
# season
# style
# activity
# =========================================================

@app.get("/destinations/filter")
def filter_destinations(
    state: Optional[str] = None,
    max_budget: Optional[int] = None,
    duration: Optional[int] = None,
    difficulty: Optional[str] = None,
    type: Optional[str] = None,
    crowd: Optional[str] = None,
    season: Optional[str] = None,
    style: Optional[str] = None,
    activity: Optional[str] = None
):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        query = """
            SELECT
                d.id,
                d.slug,
                d.name,
                d.state,
                d.region,
                d.tagline,
                d.type,
                d.budget,
                d.budget_label,
                d.duration_days,
                d.best_season,
                d.difficulty,
                d.crowd,
                d.alternative_to,
                d.latitude,
                d.longitude
            FROM destinations d
            WHERE 1 = 1
        """

        params = []


        # -------------------------------------------------
        # STATE FILTER
        # -------------------------------------------------

        if state:
            query += " AND d.state = %s"
            params.append(state)


        # -------------------------------------------------
        # MAXIMUM BUDGET FILTER
        # -------------------------------------------------

        if max_budget is not None:
            query += " AND d.budget <= %s"
            params.append(max_budget)


        # -------------------------------------------------
        # MAXIMUM DURATION FILTER
        # -------------------------------------------------

        if duration is not None:
            query += " AND d.duration_days <= %s"
            params.append(duration)


        # -------------------------------------------------
        # DIFFICULTY FILTER
        # -------------------------------------------------

        if difficulty:
            query += " AND d.difficulty = %s"
            params.append(difficulty)


        # -------------------------------------------------
        # DESTINATION TYPE FILTER
        # Example: Trek, Mountain, Island, Village
        # -------------------------------------------------

        if type:
            query += " AND d.type = %s"
            params.append(type)


        # -------------------------------------------------
        # CROWD FILTER
        # Example: Quiet, Moderate, Busy
        # -------------------------------------------------

        if crowd:
            query += " AND d.crowd = %s"
            params.append(crowd)


        # -------------------------------------------------
        # SEASON FILTER
        # Searches both best_season and season relationship
        # -------------------------------------------------

        if season:
            query += """
                AND (
                    d.best_season LIKE %s
                    OR EXISTS (
                        SELECT 1
                        FROM destination_seasons ds
                        JOIN seasons s
                            ON ds.season_id = s.season_id
                        WHERE ds.destination_id = d.id
                        AND s.season_name = %s
                    )
                )
            """

            params.append("%" + season + "%")
            params.append(season)


        # -------------------------------------------------
        # STYLE FILTER
        # Example: Adventure, Nature, Culture
        # -------------------------------------------------

        if style:
            query += """
                AND EXISTS (
                    SELECT 1
                    FROM destination_styles dst
                    JOIN styles st
                        ON dst.style_id = st.style_id
                    WHERE dst.destination_id = d.id
                    AND st.style_name = %s
                )
            """

            params.append(style)


        # -------------------------------------------------
        # ACTIVITY FILTER
        # Example: Trekking, Camping, Photography
        # -------------------------------------------------

        if activity:
            query += """
                AND EXISTS (
                    SELECT 1
                    FROM destination_activities da
                    JOIN activities a
                        ON da.activity_id = a.activity_id
                    WHERE da.destination_id = d.id
                    AND a.activity_name = %s
                )
            """

            params.append(activity)


        # -------------------------------------------------
        # SORT RESULTS
        # -------------------------------------------------

        query += " ORDER BY d.name"


        cursor.execute(query, params)

        destinations = cursor.fetchall()


        return {
            "count": len(destinations),
            "filters": {
                "state": state,
                "max_budget": max_budget,
                "duration": duration,
                "difficulty": difficulty,
                "type": type,
                "crowd": crowd,
                "season": season,
                "style": style,
                "activity": activity
            },
            "destinations": destinations
        }

    finally:
        cursor.close()
        conn.close()

# =========================================================
# RECOMMENDATION API
# =========================================================

@app.get("/recommendations")
def get_recommendations(
    state: Optional[str] = None,
    max_budget: Optional[int] = None,
    duration: Optional[int] = None,
    difficulty: Optional[str] = None,
    type: Optional[str] = None,
    crowd: Optional[str] = None,
    season: Optional[str] = None,
    style: Optional[str] = None,
    activity: Optional[str] = None
):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        query = """
            SELECT
                d.id,
                d.slug,
                d.name,
                d.state,
                d.region,
                d.tagline,
                d.type,
                d.budget,
                d.budget_label,
                d.duration_days,
                d.best_season,
                d.difficulty,
                d.crowd,
                d.alternative_to,
                d.latitude,
                d.longitude
            FROM destinations d
            WHERE 1 = 1
        """

        params = []

        # -------------------------------------------------
        # HARD FILTERS
        # -------------------------------------------------

        if state:
            query += " AND d.state = %s"
            params.append(state)

        if max_budget is not None:
            query += " AND d.budget <= %s"
            params.append(max_budget)

        if duration is not None:
            query += " AND d.duration_days <= %s"
            params.append(duration)

        if difficulty:
            query += " AND d.difficulty = %s"
            params.append(difficulty)

        if type:
            query += " AND d.type = %s"
            params.append(type)

        if crowd:
            query += " AND d.crowd = %s"
            params.append(crowd)

        # -------------------------------------------------
        # SEASON FILTER
        # -------------------------------------------------

        if season:
            query += """
                AND (
                    d.best_season LIKE %s
                    OR EXISTS (
                        SELECT 1
                        FROM destination_seasons ds
                        JOIN seasons s
                            ON ds.season_id = s.season_id
                        WHERE ds.destination_id = d.id
                        AND s.season_name = %s
                    )
                )
            """

            params.append("%" + season + "%")
            params.append(season)

        # -------------------------------------------------
        # STYLE FILTER
        # -------------------------------------------------

        if style:
            query += """
                AND EXISTS (
                    SELECT 1
                    FROM destination_styles dst
                    JOIN styles st
                        ON dst.style_id = st.style_id
                    WHERE dst.destination_id = d.id
                    AND st.style_name = %s
                )
            """

            params.append(style)

        # -------------------------------------------------
        # ACTIVITY FILTER
        # -------------------------------------------------

        if activity:
            query += """
                AND EXISTS (
                    SELECT 1
                    FROM destination_activities da
                    JOIN activities a
                        ON da.activity_id = a.activity_id
                    WHERE da.destination_id = d.id
                    AND a.activity_name = %s
                )
            """

            params.append(activity)

        query += " ORDER BY d.budget ASC, d.name ASC"

        cursor.execute(query, params)

        destinations = cursor.fetchall()

        # -------------------------------------------------
        # CALCULATE RECOMMENDATION SCORE
        # -------------------------------------------------

        recommendations = []

        for destination in destinations:

            score = 0

            if state and destination["state"].lower() == state.lower():
                score += 10

            if max_budget is not None:
                if destination["budget"] <= max_budget:
                    score += 15

            if duration is not None:
                if destination["duration_days"] <= duration:
                    score += 15

            if difficulty:
                if destination["difficulty"].lower() == difficulty.lower():
                    score += 10

            if type:
                if destination["type"].lower() == type.lower():
                    score += 10

            if crowd:
                if destination["crowd"].lower() == crowd.lower():
                    score += 10

            if season:
                best_season = destination["best_season"] or ""

                if season.lower() in best_season.lower():
                    score += 10

            if style:
                score += 5

            if activity:
                score += 5

            destination["recommendation_score"] = score

            recommendations.append(destination)

        # Highest score first
        recommendations.sort(
            key=lambda x: (
                x["recommendation_score"],
                -x["budget"]
            ),
            reverse=True
        )

        # Return top 20 recommendations
        recommendations = recommendations[:20]

        return {
            "count": len(recommendations),
            "recommendations": recommendations
        }

    finally:
        cursor.close()
        conn.close()
# =========================================================
# GET SINGLE DESTINATION
# =========================================================

@app.get("/destinations/{slug}")
def get_destination(slug: str):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # -------------------------------------------------
        # MAIN DESTINATION DETAILS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                slug,
                name,
                state,
                region,
                tagline,
                overview,
                why_visit,
                type,
                budget,
                budget_label,
                duration_days,
                best_season,
                difficulty,
                crowd,
                alternative_to,
                latitude,
                longitude
            FROM destinations
            WHERE slug = %s
        """, (slug,))

        destination = cursor.fetchone()


        if destination is None:
            raise HTTPException(
                status_code=404,
                detail="Destination not found"
            )


        destination_id = destination["id"]


        # -------------------------------------------------
        # STYLES
        # -------------------------------------------------

        cursor.execute("""
            SELECT s.style_name
            FROM destination_styles ds
            JOIN styles s
                ON ds.style_id = s.style_id
            WHERE ds.destination_id = %s
            ORDER BY s.style_name
        """, (destination_id,))

        styles = [
            row["style_name"]
            for row in cursor.fetchall()
        ]


        # -------------------------------------------------
        # SEASONS
        # -------------------------------------------------

        cursor.execute("""
            SELECT s.season_name
            FROM destination_seasons ds
            JOIN seasons s
                ON ds.season_id = s.season_id
            WHERE ds.destination_id = %s
            ORDER BY s.season_name
        """, (destination_id,))

        seasons = [
            row["season_name"]
            for row in cursor.fetchall()
        ]


        # -------------------------------------------------
        # ACTIVITIES
        # -------------------------------------------------

        cursor.execute("""
            SELECT a.activity_name
            FROM destination_activities da
            JOIN activities a
                ON da.activity_id = a.activity_id
            WHERE da.destination_id = %s
            ORDER BY a.activity_name
        """, (destination_id,))

        activities = [
            row["activity_name"]
            for row in cursor.fetchall()
        ]


        # -------------------------------------------------
        # FOOD
        # -------------------------------------------------

        cursor.execute("""
            SELECT food_name
            FROM foods
            WHERE destination_id = %s
            ORDER BY food_name
        """, (destination_id,))

        food = [
            row["food_name"]
            for row in cursor.fetchall()
        ]


        # -------------------------------------------------
        # CAFES
        # -------------------------------------------------

        cursor.execute("""
            SELECT cafe_name
            FROM cafes
            WHERE destination_id = %s
            ORDER BY cafe_name
        """, (destination_id,))

        cafes = [
            row["cafe_name"]
            for row in cursor.fetchall()
        ]


        # -------------------------------------------------
        # IMAGES
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                image_url,
                image_type
            FROM destination_images
            WHERE destination_id = %s
            ORDER BY image_id
        """, (destination_id,))

        images = cursor.fetchall()


        # -------------------------------------------------
        # PHOTO SPOTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT spot_name
            FROM photo_spots
            WHERE destination_id = %s
            ORDER BY photo_spot_id
        """, (destination_id,))

        photo_spots = [
            row["spot_name"]
            for row in cursor.fetchall()
        ]


        # -------------------------------------------------
        # NEARBY PLACES
        # -------------------------------------------------

        cursor.execute("""
            SELECT place_name
            FROM nearby_places
            WHERE destination_id = %s
            ORDER BY nearby_place_id
        """, (destination_id,))

        nearby_places = [
            row["place_name"]
            for row in cursor.fetchall()
        ]


        # -------------------------------------------------
        # NEARBY HIDDEN INDIA DESTINATIONS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                d.id,
                d.slug,
                d.name
            FROM nearby_destinations nd
            JOIN destinations d
                ON nd.nearby_destination_id = d.id
            WHERE nd.destination_id = %s
            ORDER BY d.name
        """, (destination_id,))

        nearby_destinations = cursor.fetchall()


        # -------------------------------------------------
        # ADD RELATED DATA TO DESTINATION
        # -------------------------------------------------

        destination["styles"] = styles
        destination["seasons"] = seasons
        destination["activities"] = activities
        destination["food"] = food
        destination["cafes"] = cafes
        destination["images"] = images
        destination["photo_spots"] = photo_spots
        destination["nearby_places"] = nearby_places
        destination["nearby_destinations"] = nearby_destinations


        return destination

    finally:
        cursor.close()
        conn.close()