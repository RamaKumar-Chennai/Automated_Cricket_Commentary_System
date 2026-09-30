import gradio as gr
import json
import time
from datetime import datetime

# Load match JSON
with open(r"D:\\VS_CODE\\INTEL-AIML\\Automated_Sports_Commentary_System\\ipl_json\\335982.json", encoding="utf-8") as f:
    match_data = json.load(f)

info = match_data["info"]
teams = info["teams"]

# Extract year and match number
match_date = info["dates"][0]   # e.g. "2008-04-18"
year = datetime.strptime(match_date, "%Y-%m-%d").year
match_number = info["event"]["match_number"]

# --- Replay function (shortened for clarity) ---

def replay():
    balls_per_over = info["balls_per_over"]

    # 🏏 First innings total → target for second innings
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
            for delivery in over["deliveries"]:
                raw_ball = delivery["actual_delivery"]
                over_part, ball_part = raw_ball.split(".")
                display_over = int(over_part) + 1
                display_ball = int(ball_part)
                ball_display = f"{display_over}.{display_ball}"

                batter = delivery["batter"]
                bowler = delivery["bowler"]
                non_striker = delivery.get("non_striker", "")
                runs = delivery["runs"]["total"]

                dismissal_msg = ""
                if "wickets" in delivery:
                    for w in delivery["wickets"]:
                        wickets += 1
                        dismissal_msg = f"{w['player_out']} {w['kind'].upper()}"

                total_runs += runs
                overs_fraction = int(over_part) + int(ball_part) / balls_per_over
                current_rr = round(total_runs / overs_fraction, 2) if overs_fraction > 0 else 0

                # 🏏 Always show Current Run Rate
                block_html = f"""
<div style='background:#e3f2fd;padding:12px;border-radius:10px;'>
    <div style='display:flex;justify-content:space-between;'>
        <div>
            <b>{team}</b> &nbsp;&nbsp;
            <b>Ball {ball_display}</b> &nbsp;&nbsp;
            <b>Runs:</b> {runs}
        </div>
        <div>
            <b>Score:</b> {total_runs}/{wickets} &nbsp;&nbsp;
            ⚡ <b>Current RR:</b> {current_rr}
        </div>
    </div>
    <div style='margin-top:6px;'>
        {bowler} to {batter} (non-striker: {non_striker})
    </div>
</div>
"""



                # 🎯 Add Target + Required RR only in second innings
                if innings_index == 1:
                    remaining_runs = target - total_runs
                    remaining_balls = (len(match_data["innings"][0]["overs"]) * balls_per_over) - (
                        int(over_part) * balls_per_over + int(ball_part)
                    )
                    required_rr = round((remaining_runs / remaining_balls) * balls_per_over, 2) if remaining_balls > 0 else 0
                    block_html += f"&nbsp;&nbsp; 🎯 <b>Target:</b> {target} &nbsp;&nbsp; 📊 <b>Required RR:</b> {required_rr}"

                    block_html += f"""
                    <br>
                    {bowler} to {batter} (non-striker: {non_striker})
                     </div>
                """

                if dismissal_msg:
                    block_html += f"<div style='background:#fff176;padding:8px;border-radius:8px;font-weight:bold;'>❌ WICKET! {dismissal_msg}</div>"
                elif runs == 4:
                    block_html += "<div style='background:#ffecb3;padding:8px;border-radius:8px;font-weight:bold;'>🏏 FOUR!</div>"
                elif runs == 6:
                    block_html += "<div style='background:#ffccbc;padding:8px;border-radius:8px;font-weight:bold;'>🔥 SIX!</div>"

                yield block_html
                time.sleep(15)



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
    background-color:#fce4ec;
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
    0%   { color: #d32f2f; }
    25%  { color: #1976d2; }
    50%  { color: #388e3c; }
    75%  { color: #fbc02d; }
    100% { color: #7b1fa2; }
}
.sidebar-block {
    background-color:#fce4ec;
    padding:12px;
    border-radius:10px;
    position:sticky;
    top:0;
}
.match-details {
    font-size:14px;
    margin-top:10px;
}
.commentary-box {background-color:#bbdefb; padding:15px; border-radius:10px;}
.detailed-box {
    background-color:#f3e5f5; 
    padding:15px; 
    border-radius:10px; 
    max-height:600px;   /* taller */
    overflow-y:auto;
}
.controls-box {background-color:#ffe4e1; padding:10px; border-radius:10px;}

/* 🚫 Hide image controls (zoom, download, share) */



/* Hide any buttons overlaying the image */
/* Hide all toolbar buttons inside the image */
#stadium-img .image-buttons {
    display: none !important;
}

/* 🚫 Hide Gradio footer bar */
footer {
    display: none !important;
}


"""

# --- Gradio UI ---
with gr.Blocks(css=css_styles, title="Autonomous Sports Commentary (Live Replay)") as demo:
    # ✅ Title card with stadium image (left) + flashing text (right)
    with gr.Row(elem_classes="header-block"):
        gr.Image(
            value="stadium_image.webp",   # file in same folder
            type="filepath",
            label=None,                   # 🚫 no label
            show_label=False,             # 🚫 force hide label
            scale=0,
            elem_id="stadium-img"
        )
        gr.HTML(f"""
            <div class='flashing-header'>
                🏏 INDIAN PREMIER LEAGUE SEASON - 1 ({year}) – Match {match_number}<br>
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
            commentary = gr.HTML(label="Ball-by-Ball Replay")
            
            live_btn = gr.Button("🏏 LIVE SCORE")
            live_btn.click(fn=replay, inputs=None, outputs=commentary)
           

            with gr.Row():
                with gr.Column(scale=2, elem_classes="detailed-box"):
                    detailed = gr.Textbox(label="Detailed Commentary", lines=15)

                with gr.Column(scale=1, elem_classes="controls-box"):
                    gr.Markdown("### ⚙️ Controls")
                    stats_input = gr.Textbox(label="Stats Question", placeholder="e.g. Who is top scorer?")
                    stats_output = gr.Textbox(label="Stats Agent Response")
                    stats_input.submit(fn=lambda q: f"Analyst Agent Response: (stub) Answer to '{q}'", inputs=stats_input, outputs=stats_output)

                    rag_input = gr.Textbox(label="General Q&A", placeholder="e.g. Explain Duckworth-Lewis")
                    rag_output = gr.Textbox(label="Q&A Agent Response")
                    rag_input.submit(fn=lambda q: f"Q&A Agent Response: (stub) Answer to '{q}'", inputs=rag_input, outputs=rag_output)

demo.launch(inbrowser=True)
