
import gradio as gr
import json
import time
from datetime import datetime

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
                is_extra_ball = False
                if "extras" in delivery and delivery["extras"]:
                    for k, v in delivery["extras"].items():
                        extras_detail = f"<b>Extras:</b> {k.capitalize()} +{v}"
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
                if "wickets" in delivery:
                    for w in delivery["wickets"]:
                        wickets += 1
                        dismissal_msg = f"{w['player_out']} {w['kind'].upper()}"

                total_runs += runs_total
                overs_fraction = over_part + (legal_ball_count / balls_per_over)
                current_rr = round(total_runs / overs_fraction, 2) if overs_fraction > 0 else 0

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
                time.sleep(0.1)


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

/* ✅ Text Commentary box with light aqua theme */
.detailed-box {
    background: #b2ebf2;        /* light aqua outer background */
    border: 3px solid #4dd0e1;  /* medium teal border */
    border-radius: 8px;
    padding: 10px;
}

.detailed-box textarea {
    background: #e0f7fa;        /* pale aqua inside */
    color: #006064;             /* deep teal text */
    font-weight: bold;
    border: 2px solid #26c6da;  /* inner border */
    border-radius: 6px;
}


/* Controls container */
.controls-box {
    background: #fce4ec;        /* soft pink background */
    border: 2px solid #f48fb1;  /* pink border */
    border-radius: 8px;
    padding: 8px;
}

/* Text input area */
.controls-box textarea,
.controls-box input {
    background: #fff0f6;        /* lighter pink inside */
    border: 2px solid #f8bbd0;  /* subtle border */
    border-radius: 6px;
    color: #4a148c;             /* deep purple text */
    font-weight: bold;
    padding: 6px;
}

/* Focus effect */
.controls-box textarea:focus,
.controls-box input:focus {
    outline: none;
    border-color: #ce93d8;      /* lavender highlight */
    box-shadow: 0 0 6px #ba68c8;
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



.voice-box {
    background: #b2ebf2;        /* light aqua outer background */
    border: 1px solid #4dd0e1;  /* thinner border */
    border-radius: 4px;
    padding: 2px;               /* minimal padding */
    display: inline-block;      /* keeps it compact */
}



.voice-box audio {
    width: 160px !important;    /* narrower width */
    height: 26px !important;    /* minimum most browsers allow */
    background: #e0f7fa;        /* pale aqua inside */
    border: 1px solid #26c6da;  /* thinner inner border */
    border-radius: 4px;
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
    live_btn.click(fn=replay, inputs=None, outputs=[commentary_html, detailed, commentary_audio])

demo.launch(inbrowser=True)

