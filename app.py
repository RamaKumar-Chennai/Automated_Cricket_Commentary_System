import gradio as gr
import json
import time
from datetime import datetime
import os
from sql_insert_select import create_connection, insert_delivery, truncate_table, select_sql_record

# --- Load match JSON ---
with open("match.json", encoding="utf-8") as f:
    match_data = json.load(f)

info = match_data["info"]
teams = info["teams"]
innings = match_data["innings"]

first_batting_team = innings[0]["team"]
second_batting_team = innings[1]["team"]

match_date = info["dates"][0]
year = datetime.strptime(match_date, "%Y-%m-%d").year
match_number = info["event"]["match_number"]
event_name = info["event"]["name"]
stage = info["event"].get("stage", "League")

# --- Replay function ---
def replay():
    truncate_table()   # clear table at the start of replay
    balls_per_over = info["balls_per_over"]
    first_innings_total = sum(
        d["runs"]["total"]
        for over in match_data["innings"][0]["overs"]
        for d in over["deliveries"]
    )
    target = first_innings_total + 1

    for innings_index, innings in enumerate(match_data["innings"]):
        team = innings["team"]
        total_runs = 0
        wickets = 0

        for over in innings["overs"]:
            legal_ball_count = 0
            seen_deliveries = {}

            for delivery in over["deliveries"]:
                over_part = int(over["over"])
                runs_batter = delivery["runs"]["batter"]
                runs_extras = delivery["runs"]["extras"]
                runs_total = delivery["runs"]["total"]

                extras_detail = ""
                extras_type = None
                is_extra_ball = False
                if "extras" in delivery and delivery["extras"]:
                    for k, v in delivery["extras"].items():
                        extras_detail = f"<b>Extras:</b> {k.capitalize()} +{v}"
                        extras_type = k
                        if k in ["wides", "noballs"]:
                            is_extra_ball = True

                json_delivery = delivery["actual_delivery"]
                seen_deliveries[json_delivery] = seen_deliveries.get(json_delivery, 0) + 1

                if is_extra_ball:
                    ball_display = f"{over_part+1}.{legal_ball_count+1} (extra)"
                else:
                    legal_ball_count += 1
                    ball_display = f"{over_part+1}.{legal_ball_count}"
                    if seen_deliveries[json_delivery] > 1:
                        ball_display += " (rebowled)"

                batter = delivery["batter"]
                bowler = delivery["bowler"]
                non_striker = delivery.get("non_striker", "")

                dismissal_msg = ""
                wicket_kind = None
                player_out = None
                fielder = None
                if "wickets" in delivery:
                    for w in delivery["wickets"]:
                        wickets += 1
                        wicket_kind = w["kind"]
                        player_out = w["player_out"]
                        if "fielders" in w and w["fielders"]:
                            fielder = w["fielders"][0]["name"]
                            dismissal_msg = f"{player_out} {w['kind'].upper()} by {fielder}"
                        else:
                            dismissal_msg = f"{player_out} {w['kind'].upper()}"

                total_runs += runs_total
                overs_fraction = over_part + (legal_ball_count / balls_per_over)
                current_rr = round(total_runs / overs_fraction, 2) if overs_fraction > 0 else 0

                boundary_4 = 1 if runs_batter == 4 and not delivery.get("extras") else 0
                boundary_6 = 1 if runs_batter == 6 and not delivery.get("extras") else 0

                ball_data = {
                    "json_delivery": json_delivery,
                    "actual_delivery": ball_display,
                    "bowler": bowler,
                    "batter": batter,
                    "non_striker": non_striker,
                    "runs_batter": runs_batter,
                    "runs_extras": runs_extras,
                    "runs_total": runs_total,
                    "extras_type": extras_type,
                    "boundary_4": boundary_4,
                    "boundary_6": boundary_6,
                    "wicket": 1 if dismissal_msg else 0,
                    "wicket_kind": wicket_kind,
                    "player_out": player_out,
                    "fielder": fielder,
                    "score_after_ball": f"{total_runs}/{wickets}"
                }

                block_html = f"""
                <div style='background:#e3f2fd;padding:12px;border-radius:10px;'>
                  <div>
                    <b>{team}</b> &nbsp;&nbsp;
                    <b>Ball:</b> {ball_display} &nbsp;&nbsp;
                    <b>Runs:</b> {runs_total} &nbsp;&nbsp;&nbsp;&nbsp; {extras_detail}
                  </div>
                  <div style='display:flex;justify-content:space-between;'>
                    <div>
                      <b>Score:</b> {total_runs}/{wickets} &nbsp;&nbsp;&nbsp; in <b>Overs:</b> {ball_display}
                    </div>
                    <div>
                      ⚡ <b>Current RR:</b> {current_rr} &nbsp;&nbsp;
                      <b>INNINGS:</b> {innings_index+1}
                    </div>
                  </div>
                </div>
                """

                yield block_html

                # Insert into DB
                insert_delivery(team, year, stage, match_number, innings_index, over_part+1, legal_ball_count, ball_data)

                time.sleep(0.1)

# --- Check DB Rows ---
def check_rows():
    df = select_sql_record("SELECT * FROM deliveries LIMIT 5;")
    return df.to_html(index=False)

# --- Gradio UI ---
with gr.Blocks(title="Autonomous Sports Commentary") as demo:
    with gr.Row():
        commentary_html = gr.HTML(value="<div>SCORE CARD:<br>Click LIVE SCORE to update...</div>")
        live_btn = gr.Button("🏏 LIVE SCORE")
        reset_btn = gr.Button("🗑️ Reset DB")
        check_btn = gr.Button("📊 Check DB Rows")

    live_btn.click(fn=replay, inputs=None, outputs=commentary_html)
    reset_btn.click(fn=truncate_table, inputs=None, outputs=None)
    check_btn.click(fn=check_rows, inputs=None, outputs=commentary_html)

demo.launch(server_name="0.0.0.0", server_port=10000)

