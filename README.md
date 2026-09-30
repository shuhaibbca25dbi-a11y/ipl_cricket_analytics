# IPL — Cricket Analytics Dataset (REAL, 2008–2026)
**Semester 3 OJT · Role: Data Analyst · Domain: Sports Analytics**

Built from the public **"IPL Dataset 2008 to 2026"** (Kaggle, compiled from **Cricsheet**;
enriched with ESPN Cricinfo / IPL official stats). 100% real names and real ball-by-ball —
nothing invented. The numeric team / player IDs in the raw files are **resolved to real
names** by the loader so every table reads naturally.

## Verified real
19 seasons (2008–2026), all-time run charts match reality: **V Kohli 9,050 · RG Sharma 7,185
· S Dhawan 6,769**. Toss-winner win rate **0.517** (a near coin-flip, as in real life).

## Scale
| Table | Rows |
|---|---:|
| matches | 1,212 |
| deliveries (ball-by-ball) | **288,226** |
| players | 799 |
| teams | 16 (incl. historical) |
| venues | 63 |

## Files
| File | Purpose |
|---|---|
| `ipl.db` | SQLite — all tables + indexes, **ready for SQL** |
| `tables/*.csv` | matches, deliveries, players, teams, venues (real names) |
| `load_real_ipl.py` | Rebuilds everything from the raw Kaggle files (auto-finds `../IPL_2008-2026` or `./raw`) |
| `README.md` | This guide |

## Schema (key columns)
**matches** — match_id, season, match_date, city, venue, event_name, match_type, format, overs,
**team1, team2** (names) + team1_id/team2_id, **toss_winner** (name)+id, toss_decision,
**match_winner** (name)+id, win_by_runs, win_by_wickets, result, **player_of_match** (name)+id
**deliveries** — match_id, season_id, innings, over_number, ball_number, **batting_team / bowling_team** (names)+ids,
**batter, bowler, non_striker** (names), batter_runs, extras, total_runs, is_wicket (0/1),
wicket_kind, player_out, fielders_involved, is_wide_ball / is_no_ball / is_leg_bye / is_bye / is_penalty, is_super_over
**players** — player_id, player_name, bat_style, bowl_style, field_pos, player_full_name
**teams** — team_id, team_name · **venues** — venue_id, venue_name, city

## Tasks supported
| Task | Example question |
|---|---|
| **1 · SQL** | Real strike rates & economy; team totals by venue; season run-rates; player-of-match tallies |
| **2 · Statistics** | "Does winning the toss win the match?" (toss rate 0.517 → test it); powerplay vs death-over scoring; home-city effect |
| **3 · ML** | Predict match outcome; regress a batter's runs; classify a delivery as boundary/dot |
| **4 · AI-assisted** | "Ask the Commentator" — natural-language → SQL over real cricket data |
| **5 · Storytelling** | "What actually wins matches — batting or death bowling?" board deck |

## Updating later
When newer seasons are published, drop the refreshed Kaggle files into `../IPL_2008-2026`
(or a `raw/` folder here) and run `python load_real_ipl.py` again.

## Source & licence
"IPL Dataset 2008 to 2026" (Kaggle, author *Abhishek Marathe*), compiled from Cricsheet
(https://cricsheet.org). Licence **CC BY-SA 4.0** — if you share students' work publicly,
credit Cricsheet and the dataset author. Internal training use is fine.

## Real-data notes (know these before analysing)
Because this is **genuine** data, it carries authentic quirks (kept intact on purpose):
- **Season label `2020/21`** — every other season is a plain year; IPL 2020 (played in the UAE across 2020–21) uses the real label `2020/21`. It appears as a distinct value when you `GROUP BY season`.
- **`ball_number` is 0-indexed and can exceed 5** (0–10): wides/no-balls add extra deliveries within an over (`over_number` is 0–19).
- **Expected NULLs (not missing data):** `city` is null for ~51 matches (neutral/overseas venues) and `player_of_match` for ~9 (abandoned / no-result matches).
- **`fielders_involved` won't fully join to `players`** — some entries are substitutes/fielders outside the player master; use it as free text, not a key.
- Convenience `*_id` columns (team1_id, match_winner_id, player_of_match_id) are provided alongside the resolved names for joins.
