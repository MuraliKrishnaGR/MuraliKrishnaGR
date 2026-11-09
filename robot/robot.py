"""Drive-the-robot game for the GitHub profile README.

A visitor opens an issue titled `robot|up` (or down/left/right/reset).
The workflow runs this script, which moves the robot, updates the README
between the ROBOT markers, and saves state to robot/state.json.

Usage: python robot/robot.py <command> <github_username>
"""
import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "robot" / "state.json"
README = ROOT / "README.md"
REPO = "MuraliKrishnaGR/MuraliKrishnaGR"

W, H = 9, 5
MOVES = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
ROCKS = {(2, 1), (6, 3), (4, 3), (7, 1)}

EMPTY, ROBOT, BATTERY, ROCK = "⬛", "🤖", "🔋", "🪨"


def new_battery(robot):
    free = [(x, y) for x in range(W) for y in range(H)
            if (x, y) not in ROCKS and (x, y) != tuple(robot)]
    return list(random.choice(free))


def default_state():
    robot = [0, 2]
    return {"robot": robot, "battery": new_battery(robot), "charged": 0,
            "moves": 0, "players": [], "log": []}


def load():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return default_state()


def step(state, cmd, user):
    event = ""
    if cmd == "reset":
        keep = {k: state[k] for k in ("charged", "moves", "players", "log")}
        state = {**default_state(), **keep}
        event = "reset the arena 🔄"
    else:
        dx, dy = MOVES[cmd]
        x, y = state["robot"]
        nx, ny = x + dx, y + dy
        if not (0 <= nx < W and 0 <= ny < H):
            event = f"tried {cmd}, bumped a wall 🧱"
        elif (nx, ny) in ROCKS:
            event = f"tried {cmd}, hit a rock 🪨"
        else:
            state["robot"] = [nx, ny]
            event = f"moved {cmd}"
            if state["robot"] == state["battery"]:
                state["charged"] += 1
                state["battery"] = new_battery(state["robot"])
                event += " and charged a battery ⚡"
    state["moves"] += 1
    if user not in state["players"]:
        state["players"].append(user)
    when = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    state["log"] = ([{"user": user, "event": event, "date": when}] + state["log"])[:5]
    return state


def render(state):
    rows = []
    for y in range(H):
        row = ""
        for x in range(W):
            if [x, y] == state["robot"]:
                row += ROBOT
            elif [x, y] == state["battery"]:
                row += BATTERY
            elif (x, y) in ROCKS:
                row += ROCK
            else:
                row += EMPTY
        rows.append(row)

    def btn(label, cmd, color):
        url = (f"https://github.com/{REPO}/issues/new?title=robot%7C{cmd}"
               "&body=Just+click+%27Create%27+%E2%80%94+the+robot+moves+in+about+a+minute%21")
        return (f'<a href="{url}"><img src="https://img.shields.io/badge/{label}-{color}'
                f'?style=for-the-badge" alt="{cmd}"/></a>')

    log = "\n".join(
        f"| [@{e['user']}](https://github.com/{e['user']}) | {e['event']} | {e['date']} |"
        for e in state["log"]) or "| — | waiting for the first driver… | — |"

    return f"""<!--ROBOT_START-->
<p align="center">
{"<br/>".join(rows)}
</p>

<p align="center">
{btn("%E2%86%91%20UP", "up", "a78bfa")}
<br/>
{btn("%E2%86%90%20LEFT", "left", "58e1ff")}
{btn("%E2%86%93%20DOWN", "down", "a78bfa")}
{btn("RIGHT%20%E2%86%92", "right", "58e1ff")}
<br/>
{btn("RESET", "reset", "f472b6")}
</p>

<p align="center">
⚡ <b>Batteries charged:</b> {state["charged"]} &nbsp;·&nbsp; 🕹️ <b>Total moves:</b> {state["moves"]} &nbsp;·&nbsp; 👥 <b>Drivers:</b> {len(state["players"])}
</p>

| Driver | Action | Date |
|---|---|---|
{log}
<!--ROBOT_END-->"""


def main():
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "").strip().lower()
    user = sys.argv[2] if len(sys.argv) > 2 else "someone"
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", user):
        user = "someone"
    if cmd not in MOVES and cmd not in ("reset", "render"):
        sys.exit(f"unknown command: {cmd!r}")

    state = load()
    if cmd != "render":
        state = step(state, cmd, user)
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    text = README.read_text(encoding="utf-8")
    text = re.sub(r"<!--ROBOT_START-->.*?<!--ROBOT_END-->",
                  lambda _: render(state), text, flags=re.S)
    README.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
