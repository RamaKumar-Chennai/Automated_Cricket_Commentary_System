import gradio as gr
import json
import time

from datetime import datetime

import os
from sql_insert_select import create_connection
from sql_insert_select import insert_delivery
from sql_insert_select import truncate_table
from sql_insert_select import select_sql_record



# --- Load match JSON ---
with open("match.json", encoding="utf-8") as f:
    match_data = json.load(f)

info = match_data["info"]
teams = info["teams"]

innings=match_data["innings"]
first_batting_team=innings[0]["team"]
second_batting_team=innings[1]["team"]

# Extract year and match number and stage
match_date = info["dates"][0]
year = datetime.strptime(match_date, "%Y-%m-%d").year
match_number = info["event"]["match_number"]
event_name = info["event"]["name"]

# Extract stage (Semi Final / Final / League)
stage = info["event"].get("stage", "League")        # returns "Semi Final" or "Final" if present

   
def safe_truncate():
    try:
        conn = create_connection()
        if conn:
            truncate_table()
    except Exception as e:
        print("⚠️ DB not ready:", e)



# --- Replay function ---

def replay():
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
            seen_deliveries = {}  # track duplicates for rebowled balls

            for delivery in over["deliveries"]:
                over_part = int(over["over"])
                runs_batter = delivery["runs"]["batter"]
                runs_extras = delivery["runs"]["extras"]
                runs_total = delivery["runs"]["total"]

                # ✅ Handle extras
                extras_detail = ""
                extras_type = None
                is_extra_ball = False
                if "extras" in delivery and delivery["extras"]:
                    for k, v in delivery["extras"].items():
                        extras_detail = f"<b>Extras:</b> {k.capitalize()} +{v}"
                        extras_type = k  # store extras type for DB
                        if k in ["wides", "noballs"]:
                            is_extra_ball = True

                json_delivery = delivery["actual_delivery"]

                # Track duplicates for rebowled balls
                if json_delivery not in seen_deliveries:
                    seen_deliveries[json_delivery] = 1
                else:
                    seen_deliveries[json_delivery] += 1

                # ✅ Ball display logic
                if is_extra_ball:
                    ball_display = f"{over_part+1}.{legal_ball_count+1} (extra)"
                else:
                    legal_ball_count += 1
                    ball_display = f"{over_part+1}.{legal_ball_count}"
                    if seen_deliveries[json_delivery] > 1:
                        ball_display = f"{ball_display} (rebowled)"

                batter = delivery["batter"]
                bowler = delivery["bowler"]
                non_striker = delivery.get("non_striker", "")

                # ✅ Handle wickets
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

                # --- Boundary logic ---
                boundary_4 = 1 if runs_batter == 4 and not delivery.get("extras") else 0
                boundary_6 = 1 if runs_batter == 6 and not delivery.get("extras") else 0

                # ✅ Build ball data
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

                
                # ✅ Scorecard block
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
                """

                # 🎯 Target + Required RR (second innings only)
                if innings_index == 1:
                    remaining_runs = target - total_runs
                    remaining_balls = (len(match_data["innings"][0]["overs"]) * balls_per_over) - (
                        over_part * balls_per_over + legal_ball_count
                    )
                    required_rr = round((remaining_runs / remaining_balls) * balls_per_over, 2) if remaining_balls > 0 else 0
                    block_html += f"""
                      <div style='display:flex;justify-content:flex-end;'>
                        🎯 <b>Target:</b> {target} &nbsp;&nbsp;
                        📊 <b>Required RR:</b> {required_rr}
                      </div>
                    """

                # Bowler vs batter line
                block_html += f"""
                  <div style='margin-top:6px;'>
                    ⚾ {bowler} to 🏏 {batter} (non-striker: {non_striker})
                  </div>
                </div>
                """

                # 🎯 Flash cards
                if dismissal_msg:
                    block_html += f"<div style='background:#f1948a;padding:8px;border-radius:8px;font-weight:bold;'>❌ WICKET! {dismissal_msg}</div>"
                elif boundary_4:
                    block_html += "<div style='background:#82e0aa;padding:8px;border-radius:8px;font-weight:bold;'>🏏 FOUR!</div>"
                elif boundary_6:
                    block_html += "<div style='background:#f9e79f;padding:8px;border-radius:8px;font-weight:bold;'>🔥 SIX!</div>"
                elif is_extra_ball:
                    block_html += f"<div style='background:#aed6f1;padding:8px;border-radius:8px;font-weight:bold;'>⚠️ {extras_detail}</div>"

                

                # ✅ Skip scorecard if innings ended
                if wickets == 10:
                    continue  

                # Yield scorecard 
                yield block_html

                conn = create_connection()
                insert_delivery(conn, team, year, stage, match_number, innings_index, over_part+1, legal_ball_count, ball_data)

                # Event-based delay
                if dismissal_msg:
                    delay = 0.1
                elif boundary_4 or boundary_6:
                    delay = 0.1
                else:
                    delay = 0.1
                time.sleep(delay)


# --- Players toggle ---
def toggle_players(current_html):
    if current_html.strip() == "":
        team1_players = "<ul>" + "".join([f"<li>{p}</li>" for p in info["players"][teams[0]]]) + "</ul>"
        team2_players = "<ul>" + "".join([f"<li>{p}</li>" for p in info["players"][teams[1]]]) + "</ul>"
        return f"""
        <div style='background:#fff3e0;padding:10px;border-radius:8px; max-height:300px; overflow-y:auto;'>
            <h4>👥 Team Squads</h4>
            <b>{teams[0]}:</b>{team1_players}
            <b>{teams[1]}:</b>{team2_players}
        </div>
        """
    else:
        return ""

# --- Sidebar details ---
def sidebar_details():
    venue = info.get("venue", "")
    city = info.get("city", "")
    toss_winner = info["toss"]["winner"]
    toss_decision = info["toss"]["decision"]
    match_type = info.get("match_type", "")
    overs = info.get("overs", "")
    balls_per_over = info.get("balls_per_over", "")
    officials = info.get("officials", {})
    umpires = ", ".join(officials.get("umpires", []))
    tv_umpires = ", ".join(officials.get("tv_umpires", []))
    reserve_umpires = ", ".join(officials.get("reserve_umpires", []))
    referee = ", ".join(officials.get("match_referees", []))

    return f"""
    <div class='match-details'>
        📅 Date: {match_date}<br>
        🏟️ Venue: {venue}, {city}<br>
        🎲 Toss: {toss_winner} chose to {toss_decision}<br>
        📖 Match Type: {match_type}<br>
        ⏱️ Overs: {overs}<br>
        🎯 Balls per Over: {balls_per_over}<br>
        👨‍⚖️ Umpires: {umpires}<br>
        📺 TV Umpires: {tv_umpires}<br>
        🧑‍⚖️ Reserve Umpires: {reserve_umpires}<br>
        📝 Referee: {referee}
    </div>
    """

# --- CSS ---

css_styles = """
.header-block {
    background: linear-gradient(90deg, #ff9a9e, #fad0c4);
    padding:12px;
    border-radius:10px;
    display:flex;
    align-items:center;
}
.flashing-header {
    font-size:22px;
    font-weight:bold;
    animation: bannerFlash 3s infinite;
    margin-left:15px;
}
@keyframes bannerFlash {
    0%{color:#d32f2f;}
    25%{color:#1976d2;}
    50%{color:#388e3c;}
    75%{color:#fbc02d;}
    100%{color:#7b1fa2;}
}
.sidebar-block {
    background: linear-gradient(180deg, #fce4ec, #f8bbd0);
    padding:12px;
    border-radius:10px;
    position:sticky;
    top:0;
    height:100%;
    color:#4a148c;
    font-weight:bold;
}

/* ✅ Scorecard styling: border + reduced height + centered text + smaller font */
.scorecard {
    border: 2px solid #1976d2;
    border-radius:8px;
    padding:10px;
    background:#bbdefb;
    color:#0d47a1;
    text-align:center;
    font-weight:bold;
    font-size:14px;   /* reduced font size */
    min-height:80px;  /* reduced height */
}





/* 🌐 Page background */
body, .gradio-container {
    background: linear-gradient(135deg, #fce4ec, #e0f7fa);  /* soft pink → aqua gradient */
}

/* 🚫 Hide Gradio footer */
footer {
    display: none !important;
}

"""





with gr.Blocks(css=css_styles, title="Autonomous Sports Commentary (Live Replay)") as demo:
    with gr.Row(elem_classes="header-block"):
        gr.Image(value="stadium_image.webp", type="filepath", show_label=False, scale=0, elem_id="stadium-img")
        gr.HTML(f"""
            <div class='flashing-header'>
                🏏 {event_name } ({year}) – Match {match_number}<br>
                🏟️ {teams[0]} vs {teams[1]}
            </div>
        """)

    with gr.Row():
        with gr.Column(scale=1, elem_classes="sidebar-block"):
            gr.HTML(sidebar_details())
            players_html = gr.HTML(value="", elem_id="players-block")
            toggle_players_btn = gr.Button("👥 Show/Hide Players")
            toggle_players_btn.click(fn=toggle_players, inputs=players_html, outputs=players_html)

        with gr.Column(scale=3):
            # ✅ Default centered SCORE CARD message
            commentary_html = gr.HTML(
                value="<div>SCORE CARD:<br>Click LIVE SCORE to update...</div>",
                label="Ball-by-Ball Replay",
                elem_classes="scorecard"
            )

            live_btn = gr.Button("🏏 LIVE SCORE")

            
    # Wire your own function here later
    live_btn.click(fn=replay, inputs=None, outputs=[commentary_html])


demo.launch(server_name="0.0.0.0", server_port=10000)

