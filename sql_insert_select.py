import os
import psycopg2
from psycopg2 import Error
import pandas as pd

# --- Create Connection ---
def create_connection():
    try:
        connection = psycopg2.connect(
            host=os.getenv("DATABASE_HOST"),
            port=os.getenv("DATABASE_PORT"),
            dbname=os.getenv("DATABASE_NAME"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD")
        )
        print("✅ Connected to PostgreSQL")
        return connection
    except Error as err:
        print(f"❌ Error: {err}")
        return None

# --- Truncate Table ---
def truncate_table():
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE deliveries")
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Table truncated")

# --- Insert Delivery ---
def insert_delivery(team, year, stage, match_id, innings_index, over_number, ball_number, ball_data):
    conn = create_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        query = """
        INSERT INTO deliveries (
            year, stage, match_id, innings, team,
            over_number, ball_number, actual_delivery,
            bowler, batter, non_striker,
            runs_batter, runs_extras, runs_total, extras_type,
            boundary_4, boundary_6,
            wicket, wicket_kind, player_out, fielder, score_after_ball
        )
        VALUES (%s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s, %s)
        """
        values = (
            year, stage, match_id, innings_index + 1, team,
            over_number, ball_number, ball_data["actual_delivery"],
            ball_data["bowler"], ball_data["batter"], ball_data["non_striker"],
            ball_data.get("runs_batter", 0), ball_data.get("runs_extras", 0),
            ball_data.get("runs_total", 0), ball_data.get("extras_type", ""),
            ball_data.get("boundary_4", 0), ball_data.get("boundary_6", 0),
            ball_data.get("wicket", 0), ball_data.get("wicket_kind", None),
            ball_data.get("player_out", None), ball_data.get("fielder", None),
            ball_data.get("score_after_ball", None)
        )
        cursor.execute(query, values)
        conn.commit()
        print(f"✅ Inserted delivery {ball_data['actual_delivery']} for team {team}")
    except Error as err:
        print(f"❌ Error inserting delivery: {err}")
    finally:
        cursor.close()
        conn.close()

# --- Select Records ---
def select_sql_record(query):
    conn = create_connection()
    if not conn:
        return pd.DataFrame()
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(results, columns=columns)
    cursor.close()
    conn.close()
    return df

