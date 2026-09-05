import sqlite3

from flask import Flask, send_from_directory, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False

DB_FILE = "cases.db"


def get_connection():
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT NOT NULL,
            category TEXT,
            stage TEXT,
            next_action TEXT,
            deadline TEXT,
            priority TEXT,
            status TEXT DEFAULT 'Входящие'
        )
    """)

    columns = [
        row["name"]
        for row in connection.execute("PRAGMA table_info(cases)").fetchall()
    ]

    if "status" not in columns:
        connection.execute(
            "ALTER TABLE cases ADD COLUMN status TEXT DEFAULT 'Входящие'"
        )

    connection.execute("""
        UPDATE cases
        SET status = 'Входящие'
        WHERE status IS NULL OR status = ''
    """)

    connection.commit()
    connection.close()

@app.route("/")
def home():
    return send_from_directory(".", "index.html")


@app.route("/api/cases", methods=["GET", "POST"])
def cases_api():

    if request.method == "GET":
        connection = get_connection()

        rows = connection.execute(
            "SELECT * FROM cases ORDER BY id"
        ).fetchall()

        connection.close()

        return jsonify([dict(row) for row in rows])

    new_case = request.get_json()

    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO cases (
            client,
            category,
            stage,
            next_action,
            deadline,
            priority
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            new_case.get("client"),
            new_case.get("category"),
            new_case.get("stage"),
            new_case.get("next_action"),
            new_case.get("deadline"),
            new_case.get("priority")
        )
    )

    connection.commit()

    new_case["id"] = cursor.lastrowid

    connection.close()

    return jsonify(new_case), 201


@app.route("/api/cases/<int:case_id>", methods=["DELETE"])
def delete_case(case_id):
    connection = get_connection()

    connection.execute(
        "DELETE FROM cases WHERE id = ?",
        (case_id,)
    )

    connection.commit()
    connection.close()

    return "", 204
@app.route("/api/cases/<int:case_id>", methods=["PUT"])
def update_case(case_id):
    updated_case = request.get_json()

    connection = get_connection()

    connection.execute(
        """
        UPDATE cases
        SET client = ?,
            category = ?,
            stage = ?,
            next_action = ?,
            deadline = ?,
            priority = ?
        WHERE id = ?
        """,
        (
            updated_case.get("client"),
            updated_case.get("category"),
            updated_case.get("stage"),
            updated_case.get("next_action"),
            updated_case.get("deadline"),
            updated_case.get("priority"),
            case_id
        )
    )

    connection.commit()
    connection.close()

    return jsonify(updated_case), 200

if __name__ == "__main__":
    init_db()
    app.run(debug=True)