from flask import Flask, render_template, jsonify, request, session, redirect
from dotenv import load_dotenv

load_dotenv()

import mysql.connector
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "kurnoolhub-secret-key"

# =========================
# MYSQL DATABASE CONNECTION
# =========================

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("MYSQLHOST"),
        port=int(os.environ.get("MYSQLPORT", 3306)),
        user=os.environ.get("MYSQLUSER"),
        password=os.environ.get("MYSQLPASSWORD"),
        database=os.environ.get("MYSQLDATABASE") or os.environ.get("MYSQL_DATABASE")
    )
# =========================
# HOME PAGE
# =========================

@app.route("/")
def home():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    user_id = session.get("user_id")


    # =========================
    # CATEGORIES
    # =========================

    cursor.execute("""
        SELECT
            id,
            name,
            description AS `desc`,
            icon AS image
        FROM categories
        ORDER BY id
    """)

    categories = cursor.fetchall()


    # =========================
    # BUSINESSES
    # FAVORITES + RATINGS
    # =========================

    cursor.execute("""
        SELECT
            b.id,
            b.name,

            COALESCE(
                GROUP_CONCAT(
                    DISTINCT c2.name
                    ORDER BY c2.name
                    SEPARATOR ', '
                ),
                c.name
            ) AS category,

            b.description,
            b.image,

            CASE
                WHEN %s IS NOT NULL
                AND EXISTS (
                    SELECT 1
                    FROM favorites f
                    WHERE f.business_id = b.id
                    AND f.user_id = %s
                )
                THEN 1
                ELSE 0
            END AS is_favorite,

            COALESCE(
                (
                    SELECT ROUND(AVG(r.rating), 1)
                    FROM reviews r
                    WHERE r.business_id = b.id
                ),
                b.rating,
                0
            ) AS rating,

            (
                SELECT COUNT(*)
                FROM reviews r2
                WHERE r2.business_id = b.id
            ) AS reviews

        FROM businesses b

        LEFT JOIN categories c
            ON b.category_id = c.id

        LEFT JOIN business_categories bc
            ON b.id = bc.business_id

        LEFT JOIN categories c2
            ON bc.category_id = c2.id

        GROUP BY
            b.id,
            b.name,
            b.description,
            b.image,
            b.rating,
            c.name

        ORDER BY b.name

        LIMIT 8

    """, (user_id, user_id))


    businesses = cursor.fetchall()


    # Popular tag

    for b in businesses:
        b["tag"] = "Popular"


    # =========================
    # PLACES
    # =========================

    cursor.execute("""
        SELECT
            id,
            name,
            description AS `desc`,
            location,
            image,
            'Places' AS type
        FROM places
        LIMIT 6
    """)

    places = cursor.fetchall()


    # =========================
    # EVENTS
    # =========================

    cursor.execute("""
        SELECT
            id,
            title,
            description,
            event_date,
            location,
            image
        FROM events
        ORDER BY event_date ASC
        LIMIT 1
    """)

    events = cursor.fetchall()


    # =========================
    # CLOSE DATABASE
    # =========================

    cursor.close()
    db.close()


    return render_template(
        "index.html",
        categories=categories,
        businesses=businesses,
        places=places,
        events=events
    )

# =========================
# EXPLORE PAGE
# =========================

@app.route("/explore")
def explore():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Categories
    cursor.execute("""
        SELECT
            id,
            name,
            description AS `desc`,
            icon AS image
        FROM categories
        ORDER BY id
    """)
    categories = cursor.fetchall()

    # Businesses
    cursor.execute("""
        SELECT
            b.id,
            b.name,

            COALESCE(
                GROUP_CONCAT(
                    DISTINCT c2.name
                    ORDER BY c2.name
                    SEPARATOR ', '
                ),
                c.name
            ) AS category,

            b.description,
            b.image

        FROM businesses b

        LEFT JOIN categories c
            ON b.category_id = c.id

        LEFT JOIN business_categories bc
            ON b.id = bc.business_id

        LEFT JOIN categories c2
            ON bc.category_id = c2.id

        GROUP BY
            b.id,
            b.name,
            b.description,
            b.image,
            c.name

        ORDER BY b.name

        LIMIT 20
    """)
    businesses = cursor.fetchall()

    for b in businesses:
        b["rating"] = "4.5"
        b["reviews"] = "0"
        b["tag"] = "Popular"

    cursor.close()
    db.close()

    return render_template(
        "explore.html",
        categories=categories,
        businesses=businesses
    )


# =========================
# PLACES PAGE
# =========================

@app.route("/places")
def places_page():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            name,
            description AS `desc`,
            location,
            image,
            'Places' AS type
        FROM places
        ORDER BY name
    """)

    places = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "places.html",
        places=places
    )




# =========================
# PLACE DETAILS PAGE
# =========================

@app.route("/place/<int:place_id>")
def place_details(place_id):

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            name,
            description AS `desc`,
            location,
            image,
            'Places' AS type
        FROM places
        WHERE id = %s
    """, (place_id,))

    place = cursor.fetchone()

    cursor.close()
    db.close()

    if not place:
        return "Place not found", 404

    return render_template(
        "place_detail.html",
        place=place
    )
# =========================
# EVENTS PAGE
# =========================

@app.route("/events")
def events_page():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            title,
            description,
            event_date,
            location,
            image
        FROM events
        ORDER BY event_date ASC
    """)

    events = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "events.html",
        events=events
    )

# =========================
# OFFERS PAGE
# =========================

@app.route("/offers")
def offers_page():

    return render_template("offers.html")

# =========================
# NEWS PAGE
# =========================

@app.route("/news")
def news_page():

    return render_template("news.html")

# =========================
# LOGIN PAGE
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            return "Email and password are required.", 400

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, email, password
            FROM users
            WHERE email = %s
        """, (email,))

        user = cursor.fetchone()

        if not user:
            cursor.close()
            db.close()

            return """
            <script>
                alert("Invalid email or password.");
                window.location.href = "/login";
            </script>
            """

        if not check_password_hash(user["password"], password):
            cursor.close()
            db.close()

            return """
            <script>
                alert("Invalid email or password.");
                window.location.href = "/login";
            </script>
            """

        # =========================
        # SAVE LOGIN ACTIVITY
        # =========================

        cursor.execute("""
            INSERT INTO login_activity (user_id)
            VALUES (%s)
        """, (user["id"],))

        db.commit()

        cursor.close()
        db.close()

        # =========================
        # SAVE USER SESSION
        # =========================

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]

        return """
        <script>
            alert("Account login successfully!");
            window.location.href = "/";
        </script>
        """

    return render_template("login.html")

# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return """
    <script>
        alert("Logged out successfully!");
        window.location.href = "/";
    </script>
    """

# =========================
# REGISTER PAGE
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not name or not email or not password:
            return "All fields are required.", 400

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Check if email already exists
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            db.close()

            return "Email already registered. Please login.", 400

        # Hash password before saving
        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users
            (name, email, password)
            VALUES (%s, %s, %s)
        """, (
            name,
            email,
            hashed_password
        ))

        db.commit()

        cursor.close()
        db.close()

        return """
        <script>
            alert("Account created successfully! Please login.");
            window.location.href = "/login";
        </script>
        """

    return render_template("register.html")

# =========================
# FAVORITES
# =========================

@app.route("/api/favorite/<int:business_id>", methods=["POST"])
def toggle_favorite(business_id):

    # User must be logged in
    if not session.get("user_id"):
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    user_id = session["user_id"]

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Check if already favorite
    cursor.execute("""
        SELECT id
        FROM favorites
        WHERE user_id = %s
        AND business_id = %s
    """, (user_id, business_id))

    favorite = cursor.fetchone()

    if favorite:

        # Remove favorite
        cursor.execute("""
            DELETE FROM favorites
            WHERE user_id = %s
            AND business_id = %s
        """, (user_id, business_id))

        db.commit()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "favorite": False,
            "message": "Removed from favorites."
        })

    else:

        # Add favorite
        cursor.execute("""
            INSERT INTO favorites
            (user_id, business_id)
            VALUES (%s, %s)
        """, (user_id, business_id))

        db.commit()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "favorite": True,
            "message": "Added to favorites."
        })

# =========================
# FAVORITES PAGE
# =========================

@app.route("/favorites")
def favorites_page():

    if not session.get("user_id"):
        return """
        <script>
            alert("Please login first.");
            window.location.href = "/login";
        </script>
        """

    user_id = session["user_id"]

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            b.id,
            b.name,
            b.description,
            b.image,
            b.rating,
            c.name AS category
        FROM favorites f
        INNER JOIN businesses b
            ON f.business_id = b.id
        LEFT JOIN categories c
            ON b.category_id = c.id
        WHERE f.user_id = %s
        ORDER BY f.created_at DESC
    """, (user_id,))

    favorites = cursor.fetchall()

    for b in favorites:
        b["reviews"] = "0"

    cursor.close()
    db.close()

    return render_template(
        "favorites.html",
        favorites=favorites
    )

# =========================
# PROFILE PAGE
# =========================

@app.route("/profile")
def profile():

    if not session.get("user_id"):
        return """
        <script>
            alert("Please login first.");
            window.location.href = "/login";
        </script>
        """

    user_id = session["user_id"]

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, name, email
        FROM users
        WHERE id = %s
    """, (user_id,))

    user = cursor.fetchone()

    cursor.close()
    db.close()

    if not user:
        session.clear()

        return """
        <script>
            alert("User account not found.");
            window.location.href = "/login";
        </script>
        """

    return render_template(
        "profile.html",
        user=user
    )

# =========================
# BUSINESSES PAGE + SEARCH
# =========================


@app.route("/businesses")
def businesses_page():

    search = request.args.get("search", "").strip()
    category_id = request.args.get("category_id", "").strip()

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    user_id = session.get("user_id")

    conditions = []
    params = [user_id, user_id]

    # CATEGORY FILTER
    if category_id:
        conditions.append("""
            (
                b.category_id = %s
                OR EXISTS (
                    SELECT 1
                    FROM business_categories bc_filter
                    WHERE bc_filter.business_id = b.id
                    AND bc_filter.category_id = %s
                )
            )
        """)
        params.extend([int(category_id), int(category_id)])

    # SEARCH FILTER
    if search:
        keyword = f"%{search}%"

        conditions.append("""
            (
                LOWER(b.name) LIKE LOWER(%s)
                OR LOWER(b.description) LIKE LOWER(%s)
                OR LOWER(c.name) LIKE LOWER(%s)
                OR EXISTS (
                    SELECT 1
                    FROM business_categories bc_search
                    INNER JOIN categories c_search
                        ON bc_search.category_id = c_search.id
                    WHERE bc_search.business_id = b.id
                    AND LOWER(c_search.name) LIKE LOWER(%s)
                )
            )
        """)

        params.extend([
            keyword,
            keyword,
            keyword,
            keyword
        ])

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT
            b.id,
            b.name,

            COALESCE(
                GROUP_CONCAT(
                    DISTINCT c2.name
                    ORDER BY c2.name
                    SEPARATOR ', '
                ),
                c.name
            ) AS category,

            b.description,
            b.image,

            CASE
                WHEN %s IS NOT NULL
                AND EXISTS (
                    SELECT 1
                    FROM favorites f
                    WHERE f.business_id = b.id
                    AND f.user_id = %s
                )
                THEN 1
                ELSE 0
            END AS is_favorite,

            COALESCE(
                (
                    SELECT ROUND(AVG(r.rating), 1)
                    FROM reviews r
                    WHERE r.business_id = b.id
                ),
                b.rating,
                0
            ) AS rating,

            (
                SELECT COUNT(*)
                FROM reviews r2
                WHERE r2.business_id = b.id
            ) AS reviews

        FROM businesses b

        LEFT JOIN categories c
            ON b.category_id = c.id

        LEFT JOIN business_categories bc
            ON b.id = bc.business_id

        LEFT JOIN categories c2
            ON bc.category_id = c2.id

        {where_clause}

        GROUP BY
            b.id,
            b.name,
            b.description,
            b.image,
            b.rating,
            c.name

        ORDER BY b.name
    """

    cursor.execute(query, params)

    businesses = cursor.fetchall()

    for b in businesses:
        b["tag"] = "Popular"

    cursor.close()
    db.close()

    return render_template(
        "businesses.html",
        businesses=businesses,
        search=search,
        category_id=category_id
    )
# =========================
# BUSINESS DETAILS PAGE
# =========================

# =========================
# BUSINESS DETAIL PAGE
# =========================

@app.route("/business/<int:business_id>")
def business_details(business_id):

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Business details
    cursor.execute("""
        SELECT
            b.id,
            b.name,

            COALESCE(
                GROUP_CONCAT(
                    DISTINCT c2.name
                    ORDER BY c2.name
                    SEPARATOR ', '
                ),
                c.name
            ) AS category,

            b.description,
            b.address,
            b.phone,
            b.rating,
            b.image,
            b.created_at

        FROM businesses b

        LEFT JOIN categories c
            ON b.category_id = c.id

        LEFT JOIN business_categories bc
            ON b.id = bc.business_id

        LEFT JOIN categories c2
            ON bc.category_id = c2.id

        WHERE b.id = %s

        GROUP BY
            b.id,
            b.name,
            b.description,
            b.address,
            b.phone,
            b.rating,
            b.image,
            b.created_at,
            c.name

    """, (business_id,))

    business = cursor.fetchone()

    if not business:
        cursor.close()
        db.close()
        return "Business not found", 404


    # =========================
    # REVIEWS
    # =========================

    cursor.execute("""
        SELECT
            r.id,
            r.rating,
            r.comment,
            r.created_at,
            u.name AS user_name
        FROM reviews r
        INNER JOIN users u
            ON r.user_id = u.id
        WHERE r.business_id = %s
        ORDER BY r.created_at DESC
    """, (business_id,))

    reviews = cursor.fetchall()


    # Number of reviews
    business["reviews"] = len(reviews)


    cursor.close()
    db.close()


    return render_template(
        "business_detail.html",
        business=business,
        reviews=reviews
    )

# =========================
# SUBMIT REVIEW
# =========================

@app.route("/business/<int:business_id>/review", methods=["POST"])
def submit_review(business_id):

    # Login check
    if not session.get("user_id"):
        return """
        <script>
            alert("Please login to write a review.");
            window.location.href = "/login";
        </script>
        """


    rating = request.form.get("rating")
    comment = request.form.get("review")
    user_id = session.get("user_id")


    # Basic validation
    if not rating or not comment:
        return """
        <script>
            alert("Please provide both rating and review.");
            history.back();
        </script>
        """


    db = get_db_connection()
    cursor = db.cursor()


    # Save review
    cursor.execute("""
        INSERT INTO reviews
            (business_id, user_id, rating, comment)
        VALUES
            (%s, %s, %s, %s)
    """, (
        business_id,
        user_id,
        int(rating),
        comment.strip()
    ))


    # Update business average rating
    cursor.execute("""
        UPDATE businesses
        SET rating = (
            SELECT AVG(rating)
            FROM reviews
            WHERE business_id = %s
        )
        WHERE id = %s
    """, (
        business_id,
        business_id
    ))


    db.commit()

    cursor.close()
    db.close()


    return """
    <script>
        alert("Review submitted successfully!");
        window.location.href = "/business/%s";
    </script>
    """ % business_id


# =========================
# LIST YOUR BUSINESS
# =========================

@app.route("/list-business", methods=["GET", "POST"])
def list_business():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Get all categories for the form
    cursor.execute("""
        SELECT
            id,
            name
        FROM categories
        ORDER BY name
    """)

    categories = cursor.fetchall()

    # Handle form submission
    if request.method == "POST":

        name = request.form.get("name", "").strip()
        category_id = request.form.get("category_id", "").strip()
        description = request.form.get("description", "").strip()
        address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()
        image = request.form.get("image", "").strip()

        if not name or not category_id:
            cursor.close()
            db.close()
            return "Business name and category are required.", 400

        cursor.execute("""
            INSERT INTO businesses
            (
                name,
                category_id,
                description,
                address,
                phone,
                rating,
                image
            )
            VALUES
            (%s, %s, %s, %s, %s, %s, %s)
        """, (
            name,
            int(category_id),
            description,
            address,
            phone,
            0,
            image
        ))

        db.commit()

        cursor.close()
        db.close()

        return """
        <script>
            alert("Business submitted successfully!");
            window.location.href = "/businesses";
        </script>
        """

    cursor.close()
    db.close()

    return render_template(
        "list_business.html",
        categories=categories
    )


# =========================
# DATABASE TEST
# =========================

@app.route("/api/database-test")
def database_test():

    try:

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SELECT DATABASE()")
        result = cursor.fetchone()

        cursor.close()
        db.close()

        return jsonify({
            "status": "success",
            "database": result[0]
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        })


# =========================
# SEARCH API
# =========================

@app.route("/api/search")
def api_search():

    search = request.args.get("q", "").strip()

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if search:

        keyword = f"%{search}%"

        cursor.execute("""
            SELECT
                b.id,
                b.name,

                COALESCE(
                    GROUP_CONCAT(
                        DISTINCT c2.name
                        ORDER BY c2.name
                        SEPARATOR ', '
                    ),
                    c.name
                ) AS category,

                b.description,
                b.image

            FROM businesses b

            LEFT JOIN categories c
                ON b.category_id = c.id

            LEFT JOIN business_categories bc
                ON b.id = bc.business_id

            LEFT JOIN categories c2
                ON bc.category_id = c2.id

            WHERE
                LOWER(b.name) LIKE LOWER(%s)
                OR LOWER(b.description) LIKE LOWER(%s)
                OR LOWER(c.name) LIKE LOWER(%s)
                OR EXISTS (
                    SELECT 1
                    FROM business_categories bc2
                    INNER JOIN categories c3
                        ON bc2.category_id = c3.id
                    WHERE
                        bc2.business_id = b.id
                        AND LOWER(c3.name) LIKE LOWER(%s)
                )

            GROUP BY
                b.id,
                b.name,
                b.description,
                b.image,
                c.name

            ORDER BY b.name

        """, (keyword, keyword, keyword, keyword))

    else:

        cursor.execute("""
            SELECT
                b.id,
                b.name,

                COALESCE(
                    GROUP_CONCAT(
                        DISTINCT c2.name
                        ORDER BY c2.name
                        SEPARATOR ', '
                    ),
                    c.name
                ) AS category,

                b.description,
                b.image

            FROM businesses b

            LEFT JOIN categories c
                ON b.category_id = c.id

            LEFT JOIN business_categories bc
                ON b.id = bc.business_id

            LEFT JOIN categories c2
                ON bc.category_id = c2.id

            GROUP BY
                b.id,
                b.name,
                b.description,
                b.image,
                c.name

            ORDER BY b.name
        """)

    businesses = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(businesses)
# =========================
# ADMIN LOGIN
# =========================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            return "Email and password are required.", 400

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, email, password
            FROM admins
            WHERE email = %s
        """, (email,))

        admin = cursor.fetchone()

        cursor.close()
        db.close()

        if not admin:
            return """
            <script>
                alert("Invalid admin email or password.");
                window.location.href = "/admin/login";
            </script>
            """

        if not check_password_hash(admin["password"], password):
            return """
            <script>
                alert("Invalid admin email or password.");
                window.location.href = "/admin/login";
            </script>
            """

        session["admin_id"] = admin["id"]
        session["admin_name"] = admin["name"]
        session["admin_email"] = admin["email"]

        return redirect("/admin")

    return render_template("admin_login.html")


# =========================
# ADMIN LOGOUT
# =========================

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin_id", None)
    session.pop("admin_name", None)
    session.pop("admin_email", None)

    return redirect("/admin/login")

# =========================
# ADMIN PASSWORD TEST
# =========================

@app.route("/admin/password-test")
def admin_password_test():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT password
        FROM admins
        WHERE email = %s
    """, ("admin@kurnoolhub.com",))

    admin = cursor.fetchone()

    cursor.close()
    db.close()

    if not admin:
        return "Admin not found"

    return jsonify({
        "admin_found": True,
        "hash_length": len(admin["password"])
    })

# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin")
def admin_dashboard():

    if not session.get("admin_id"):
        return redirect("/admin/login")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM users")
    total_users = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM businesses")
    total_businesses = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM reviews")
    total_reviews = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM favorites")
    total_favorites = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT
            u.name,
            u.email,
            u.created_at
        FROM users u
        ORDER BY u.id DESC
        LIMIT 10
    """)

    recent_users = cursor.fetchall()

    cursor.execute("""
        SELECT
            u.name,
            u.email,
            l.login_time
        FROM login_activity l
        INNER JOIN users u
            ON l.user_id = u.id
        ORDER BY l.login_time DESC
        LIMIT 10
    """)

    recent_logins = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_businesses=total_businesses,
        total_reviews=total_reviews,
        total_favorites=total_favorites,
        recent_users=recent_users,
        recent_logins=recent_logins
    )


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
