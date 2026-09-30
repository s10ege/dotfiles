#!/usr/bin/env bash
# Claude Code statusline (black & red powerline style):
#   model | dir  branch | ctx bar | 5h/7d usage | cost | time | lines
# Needs a Nerd Font / powerline font for the arrow and icon glyphs.
input=$(cat)
LIMIT=275000

j() { jq -r "$1 // empty" <<<"$input" 2>/dev/null; }

model=$(j '.model.display_name')
cwd=$(j '.workspace.current_dir // .cwd')
transcript=$(j '.transcript_path')
cost=$(j '.cost.total_cost_usd')
dur=$(j '.cost.total_duration_ms')
added=$(j '.cost.total_lines_added')
removed=$(j '.cost.total_lines_removed')
five=$(j '.rate_limits.five_hour.used_percentage')
week=$(j '.rate_limits.seven_day.used_percentage')
five_reset=$(j '.rate_limits.five_hour.resets_at')

# Context tokens: last usage entry in transcript, fallback to context_window.current_usage
used=""
if [ -n "$transcript" ] && [ -f "$transcript" ]; then
  used=$(tail -n 300 "$transcript" | jq -rs '
    [.[] | select(.message.usage != null and (.isSidechain // false) == false) | .message.usage] | last
    | if . then ((.input_tokens // 0) + (.cache_read_input_tokens // 0) + (.cache_creation_input_tokens // 0)) else empty end' 2>/dev/null)
fi
if [ -z "$used" ]; then
  used=$(j '.context_window.current_usage | if . then ((.input_tokens // 0) + (.cache_read_input_tokens // 0) + (.cache_creation_input_tokens // 0)) else empty end')
fi

# Palette (256-colour)
RED=124       # brand block
ALERT=52      # background of a segment that is running hot
DARK_A=234    # dark segments alternate between these two so every arrow stays visible
DARK_B=236
TEXT=252
MUTED=243
ARROW=$'\uE0B0'
I_DIR=$'\uF07C'
I_GIT=$'\uE0A0'
THIN=$'\uE0B1'      # used between two segments that share a background
RST=$'\e[0m'
BOLD=$'\e[1m'
NOBOLD=$'\e[22m'
out=""
prev=""
alt=0

fg() { printf '\e[38;5;%sm' "$1"; }

# seg <bg256> <fg256> <text>
seg() {
  local bg=$1 fg=$2 text=$3
  if [ "$prev" = "$bg" ]; then
    out+=$'\e[38;5;'"${fg}"$'m'"${THIN}"
  elif [ -n "$prev" ]; then
    out+=$'\e[38;5;'"${prev}"$'m\e[48;5;'"${bg}"$'m'"${ARROW}"
  fi
  out+=$'\e[48;5;'"${bg}"$'m\e[38;5;'"${fg}"$'m'" ${text} "
  prev=$bg
}

# dark <fg256> <text> [hot]: next alternating dark background, or the alert background when hot
dark() {
  local bg
  if [ "$alt" -eq 0 ]; then bg=$DARK_A; alt=1; else bg=$DARK_B; alt=0; fi
  [ -n "$3" ] && bg=$ALERT
  seg "$bg" "$1" "$2"
}

# heat <pct>: bar colour by level
heat() {
  if [ "$1" -lt 50 ]; then echo 167; elif [ "$1" -lt 80 ]; then echo 203; else echo 196; fi
}

# bar <pct> <cells>: coloured ▰▱ bar, restores TEXT colour afterwards
bar() {
  local pct=$1 cells=$2 filled i b=""
  filled=$(( (pct * cells + 50) / 100 ))
  [ "$pct" -gt 0 ] && [ "$filled" -eq 0 ] && filled=1
  b+=$(fg "$(heat "$pct")")
  for ((i = 1; i <= cells; i++)); do
    [ "$i" -eq $((filled + 1)) ] && b+=$(fg 239)
    if [ "$i" -le "$filled" ]; then b+="▰"; else b+="▱"; fi
  done
  printf '%s%s' "$b" "$(fg $TEXT)"
}

# pctfmt <pct>: bold percentage in heat colour
pctfmt() { printf '%s%s%s%%%s%s' "$(fg "$(heat "$1")")" "$BOLD" "$1" "$NOBOLD" "$(fg $TEXT)"; }

# 1. Model: solid red brand block
[ -n "$model" ] && seg "$RED" 255 "${BOLD}󰚩 ${model}${NOBOLD}"

# 2. Directory and git branch
if [ -n "$cwd" ]; then
  dark "$TEXT" "${I_DIR} ${cwd##*/}"
  branch=$(git -C "$cwd" --no-optional-locks symbolic-ref --short HEAD 2>/dev/null)
  if [ -n "$branch" ]; then
    dirty=""
    [ -n "$(git -C "$cwd" --no-optional-locks status --porcelain 2>/dev/null)" ] && dirty=" $(fg 196)●$(fg 217)"
    dark 217 "${I_GIT} ${branch}${dirty}"
  fi
fi

# 3. Context window
if [ -n "$used" ]; then
  pct=$(( used * 100 / LIMIT ))
  [ "$pct" -gt 100 ] && pct=100
  k=$(awk -v u="$used" 'BEGIN{printf "%.0fk", u/1000}')
  hot=""; [ "$pct" -ge 80 ] && hot=1
  dark "$TEXT" "󰧑 $(bar "$pct" 10) $(pctfmt "$pct") $(fg $MUTED)${k}" "$hot"
fi

# 4. Subscription usage: 5-hour session and 7-day weekly (only present for subscribers)
if [ -n "$five" ] || [ -n "$week" ]; then
  txt=""; hot=""
  if [ -n "$five" ]; then
    p=$(printf '%.0f' "$five")
    txt+="5h $(bar "$p" 5) $(pctfmt "$p")"
    [ "$p" -ge 80 ] && hot=1
    # time until the session window resets (resets_at may be epoch seconds or an ISO date)
    if [ -n "$five_reset" ]; then
      if [[ "$five_reset" =~ ^[0-9]+$ ]]; then r=$five_reset; else r=$(date -d "$five_reset" +%s 2>/dev/null); fi
      if [ -n "$r" ]; then
        left=$(( r - $(date +%s) ))
        if [ "$left" -gt 0 ]; then
          if [ "$left" -ge 3600 ]; then rt="$((left/3600))h$((left%3600/60))m"; else rt="$((left/60))m"; fi
          txt+=" $(fg $MUTED)↻${rt}$(fg $TEXT)"
        fi
      fi
    fi
  fi
  if [ -n "$week" ]; then
    p=$(printf '%.0f' "$week")
    txt+="${txt:+ $(fg 239)│$(fg $TEXT) }7d $(bar "$p" 5) $(pctfmt "$p")"
    [ "$p" -ge 80 ] && hot=1
  fi
  dark "$TEXT" "󰔟 ${txt}" "$hot"
fi

# 5. Cost
[ -n "$cost" ] && dark 203 "$(printf '$%.2f' "$cost")"

# 6. Session time
if [ -n "$dur" ]; then
  s=$(( dur / 1000 ))
  if [ "$s" -ge 3600 ]; then t="$((s/3600))h$((s%3600/60))m"; else t="$((s/60))m$((s%60))s"; fi
  dark "$MUTED" "󰥔 ${t}"
fi

# 7. Lines changed
[ -n "$added$removed" ] && dark "$TEXT" "+${added:-0} $(fg 196)-${removed:-0}"

# closing arrow
[ -n "$prev" ] && out+="${RST}"$'\e[38;5;'"${prev}"$'m'"${ARROW}${RST}"
printf '%s' "$out"
