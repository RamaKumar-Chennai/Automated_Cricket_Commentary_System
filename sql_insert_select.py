# --- SQL Logging Functions (MySQL) ---
import mysql.connector
from mysql.connector import Error

def create_connection():
    try:
        
        connection = mysql.connector.connect(
            host=os.getenv("DATABASE_HOST"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
            database=os.getenv("DATABASE_NAME")
    )
        if connection.is_connected():
            print("✅ Connected to MySQL")
            return connection
    except Error as err:
        print(f"Error: {err}")
        return None


def truncate_table(conn):
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE deliveries")
    conn.commit()
    cursor.close()
    conn.close()

#insert_delivery(conn,team,year,stage, match_number, innings_index, over_part+1, legal_ball_count, ball_data)
# --- Insert Delivery Data into MySQL ---

def insert_delivery(conn, team, year, stage, match_id, innings_index, over_number, ball_number, ball_data):
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
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s,
            %s, %s, %s, %s, %s
        )
        """
        values = (
            year,
            stage,
            match_id,
            innings_index + 1,
            team,
            over_number,
            ball_number,
            ball_data["actual_delivery"],
            ball_data["bowler"],
            ball_data["batter"],
            ball_data["non_striker"],
            ball_data.get("runs_batter", 0),
            ball_data.get("runs_extras", 0),
            ball_data.get("runs_total", 0),
            ball_data.get("extras_type", ""),
            ball_data.get("boundary_4", 0),
            ball_data.get("boundary_6", 0),
            ball_data.get("wicket", 0),
            ball_data.get("wicket_kind", None),
            ball_data.get("player_out", None),
            ball_data.get("fielder", None),
            ball_data.get("score_after_ball", None)
        )
        cursor.execute(query, values)
        conn.commit()
        print(f"✅ Inserted delivery {ball_data['actual_delivery']} for team {team}")
    except Error as err:
        print(f"Error inserting delivery: {err}")
    finally:
        cursor.close()
        conn.close()


"""
def select_sql_record(query):
    import pandas as pd
    conn=create_connection()
    cursor = conn.cursor()
    cursor.execute(query)

   # Fetch all results from the executed query
    results = cursor.fetchall()
    print("data type of results is ",type(results))
    print(" results is ",results)
    
    
   
    print("The fiprrst two elements in resulsts are",results[0],results[1])
    print("the length of results is ",len(results))
    res_lst=[]
    for i in range(0,len(results)):
        res_lst.append(results[i][0])
    print("the res list is",res_lst)
    df = pd.DataFrame(res_lst, columns=[desc[0] for desc in cursor.description])
    
    cursor.close()  
    
    conn.close()
    return df



"""


import pandas as pd

def select_sql_record(query):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(query)

    # Fetch all results
    results = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    # Build DataFrame with full rows, not just the first element
    df = pd.DataFrame(results, columns=columns)

    cursor.close()
    conn.close()
    return df

