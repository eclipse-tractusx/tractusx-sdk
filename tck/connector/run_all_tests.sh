#!/usr/bin/env bash
# #################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 Catena-X Automotive Network e.V.
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
# #################################################################################

# Run all 6 TCK E2E connector tests in parallel with a live real-time dashboard.
#
# Usage:
#   ./tck/connector/run_all_tests.sh [OPTIONS]
#
# Options:
#   --local                      Install the SDK from the local workspace before
#                                running tests (runs: pip install -e . --quiet).
#                                By default no installation is performed.
#   --no-cleanup                 Skip cleanup of provider resources and backend data
#   --config <path>              Path to a YAML config file to use instead of the
#                                default tck-config.yaml.  All connectivity values
#                                (URLs, keys, BPNs, DIDs, policies) are loaded from
#                                the given file.  Each script loads its own section
#                                automatically (jupiter / saturn).
#   --config-section <name>      Override the section name to load from the YAML file.
#                                Each script has a built-in default (e.g. "saturn").
#   --provider-url <url>         Override provider EDC base URL for all tests
#   --consumer-url <url>         Override consumer EDC base URL for all tests
#   --backend-url <url>          Override backend storage URL for all tests
#   --provider-api-key <key>     Override provider API key for all tests
#   --consumer-api-key <key>     Override consumer API key for all tests
#   --provider-bpn <bpn>         Override provider BPN for all tests
#   --consumer-bpn <bpn>         Override consumer BPN for all tests
#   --provider-did <did>         Override provider DID for DID-based tests
#   --consumer-did <did>         Override consumer DID for DID-based tests
#
# All options are forwarded verbatim to each of the 6 test scripts.
#
# Examples:
#   # Install local SDK and use a custom config file (e.g. for INT environment):
#   ./run_all_tests.sh --local --config /path/to/int_config.yaml
#
#   # Quick ad-hoc URL override without editing any file:
#   ./run_all_tests.sh --provider-url http://my-provider.example.com
#
#   # Skip cleanup:
#   ./run_all_tests.sh --no-cleanup
#
# Logs are written to tck/connector/logs/run_all_tests/<date>/<run-id>/

set -uo pipefail

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# ── Parse --local flag (consumed here, not forwarded to child scripts) ────────
INSTALL_LOCAL=false
EXTRA_ARGS=""
for arg in "$@"; do
    if [[ "${arg}" == "--local" ]]; then
        INSTALL_LOCAL=true
    else
        EXTRA_ARGS="${EXTRA_ARGS:+${EXTRA_ARGS} }${arg}"
    fi
done

# ── Unique run directory: logs/run_all_tests/<date>/<HHMMSS_hex6>/ ────────────
RUN_DATE="$(date '+%Y-%m-%d')"
RUN_ID="$(date '+%H%M%S')_$(LC_ALL=C tr -dc 'a-f0-9' </dev/urandom 2>/dev/null | head -c 6 || printf '%06x' $(( RANDOM * RANDOM % 16777216 )))"
LOG_DIR="${SCRIPT_DIR}/logs/run_all_tests/${RUN_DATE}/${RUN_ID}"

cd "${REPO_ROOT}"
mkdir -p "${LOG_DIR}"

# ── Optionally install the SDK from the local workspace ───────────────────────
if [[ "${INSTALL_LOCAL}" == "true" ]]; then
    echo "Installing tractusx-sdk from local workspace (--local)..."
    pip install -e . --quiet
    echo "Installation complete."
    echo ""
fi
echo "Run ID  : ${RUN_ID}"
echo "Log dir : ${LOG_DIR}"
echo ""

# ── ANSI colours & styles ─────────────────────────────────────────────────────
RESET=$'\033[0m'
BOLD=$'\033[1m'
GREEN=$'\033[32m'
RED=$'\033[31m'
CYAN=$'\033[36m'
DIM=$'\033[2m'

# ── Test list ─────────────────────────────────────────────────────────────────
TESTS=(
    "tck_e2e_jupiter_0-10-X_detailed"
    "tck_e2e_jupiter_0-10-X_simple"
    "tck_e2e_saturn_0-11-X_detailed"
    "tck_e2e_saturn_0-11-X_detailed_did"
    "tck_e2e_saturn_0-11-X_simple"
    "tck_e2e_saturn_0-11-X_simple_did"
)

N=${#TESTS[@]}

# ── Per-test state (indexed arrays) ───────────────────────────────────────────
declare -a PIDS START_TIMES STATUSES DURATIONS LOGS

for i in "${!TESTS[@]}"; do
    LOGS[$i]="${LOG_DIR}/${TESTS[$i]}.log"
    STATUSES[$i]="PENDING"
    DURATIONS[$i]="0"
    START_TIMES[$i]=0
    PIDS[$i]=0
done

SUITE_START=$(date +%s)

# ── Table layout ──────────────────────────────────────────────────────────────
# Rows: top + title + subtitle + sep + header + sep + N tests + sep + footer + bottom
TABLE_LINES=$(( N + 9 ))

# Visible column widths (no ANSI codes counted here)
COL_NAME=36      # max test name chars (longest is 34)
COL_STATUS=9     # all status strings are exactly 9 visible chars
COL_TIME=7       # right-aligned time field
# Inner visible width: 1 + COL_NAME + 2 + COL_STATUS + 2 + COL_TIME + 1
W=$(( 1 + COL_NAME + 2 + COL_STATUS + 2 + COL_TIME + 1 ))

# ── Drawing helpers ───────────────────────────────────────────────────────────
repeat_char() { printf "%${2}s" | tr ' ' "${1}"; }
hr_top() { printf "╔%s╗\n" "$(repeat_char '═' $W)"; }
hr_mid() { printf "╠%s╣\n" "$(repeat_char '═' $W)"; }
hr_bot() { printf "╚%s╝\n" "$(repeat_char '═' $W)"; }

elapsed_str() {
    local s=$1
    if   (( s < 60   )); then printf "%ds"     "$s"
    elif (( s < 3600 )); then printf "%dm%02ds" $(( s/60 )) $(( s%60 ))
    else                      printf "%dh%02dm" $(( s/3600 )) $(( (s%3600)/60 ))
    fi
}

# rpad: print $1 (plain visible text) left-padded to $2 chars, apply color $3 around it
rpad() {
    local text="$1" width="$2" color="${3:-}" reset="${4:-}"
    local len=${#text}
    local pad=$(( width - len < 0 ? 0 : width - len ))
    printf "%s%s%s%${pad}s" "${color}" "${text}" "${reset}" ""
}

# lpad: right-align $1 within $2 chars
lpad() {
    local text="$1" width="$2"
    local len=${#text}
    local pad=$(( width - len < 0 ? 0 : width - len ))
    printf "%${pad}s%s" "" "${text}"
}

# Status: always 9 visible chars — print color separately, no printf width
status_colored() {
    local plain color
    case "$1" in
        RUNNING) plain="⟳ RUNNING" ; color="${CYAN}${BOLD}"  ;;
        PASS)    plain="✓ PASS   " ; color="${GREEN}${BOLD}" ;;
        FAIL)    plain="✗ FAIL   " ; color="${RED}${BOLD}"   ;;
        PENDING) plain="◌ PENDING" ; color="${DIM}"          ;;
        *)       plain="? UNKNOWN" ; color="${DIM}"          ;;
    esac
    # COL_STATUS = 9 visible chars — verified by ${#plain}
    printf "%s%s%s" "${color}" "${plain}" "${RESET}"
}

# ── Draw the dashboard table ──────────────────────────────────────────────────
draw_table() {
    local now; now=$(date +%s)
    local suite_elapsed=$(( now - SUITE_START ))
    local running=0 passed=0 failed=0

    for i in "${!TESTS[@]}"; do
        case "${STATUSES[$i]}" in
            RUNNING) (( running++ )) || true ;;
            PASS)    (( passed++  )) || true ;;
            FAIL)    (( failed++  )) || true ;;
        esac
    done

    # ── Top border ───────────────────────────────────────────────────
    hr_top

    # ── Title row ────────────────────────────────────────────────────
    local title="  Tractus-X SDK - TCK Connector Test Suite"
    printf "║"
    printf "%s" "${BOLD}"
    rpad "${title}" "${W}"
    printf "%s" "${RESET}"
    printf "║\n"

    # ── Subtitle row ─────────────────────────────────────────────────
    local started_at; started_at="$(date '+%Y-%m-%d %H:%M:%S')"
    local elapsed_label; elapsed_label="$(elapsed_str "${suite_elapsed}")"
    local subtitle="  Started: ${started_at}   Elapsed: ${elapsed_label}"
    printf "║"
    printf "%s" "${DIM}"
    rpad "${subtitle}" "${W}"
    printf "%s" "${RESET}"
    printf "║\n"

    # ── Column header ────────────────────────────────────────────────
    hr_mid
    printf "║"
    printf "%s" "${BOLD}"
    # 1 space + "TEST" padded to COL_NAME + 2 gap + "STATUS" padded to COL_STATUS + 2 gap + "TIME" right-aligned to COL_TIME + 1 space
    printf " "
    rpad "TEST" "${COL_NAME}"
    printf "  "
    rpad "STATUS" "${COL_STATUS}"
    printf "  "
    lpad "TIME" "${COL_TIME}"
    printf " "
    printf "%s" "${RESET}"
    printf "║\n"
    hr_mid

    # ── Test rows ────────────────────────────────────────────────────
    for i in "${!TESTS[@]}"; do
        local dur="${DURATIONS[$i]}"
        if [[ "${STATUSES[$i]}" == "RUNNING" && "${START_TIMES[$i]}" -gt 0 ]]; then
            dur=$(( now - START_TIMES[$i] ))
        fi
        local dur_str; dur_str="$(elapsed_str "${dur}")"

        printf "║ "
        rpad "${TESTS[$i]}" "${COL_NAME}"
        printf "  "
        status_colored "${STATUSES[$i]}"   # always COL_STATUS (9) visible chars
        printf "  "
        lpad "${dur_str}" "${COL_TIME}"
        printf " ║\n"
    done

    # ── Footer ───────────────────────────────────────────────────────
    hr_mid

    # Build footer visible string to compute padding
    local f_run="${running} running"   # e.g. "2 running"
    local f_pas="${passed} passed"
    local f_fai="${failed} failed"
    local footer_vis="  ${f_run}   ${f_pas}   ${f_fai}"
    local footer_pad=$(( W - ${#footer_vis} ))

    printf "║  "
    printf "%s%s%s" "${CYAN}${BOLD}" "${f_run}" "${RESET}"
    printf "   "
    printf "%s%s%s" "${GREEN}${BOLD}" "${f_pas}" "${RESET}"
    printf "   "
    if (( failed > 0 )); then
        printf "%s%s%s" "${RED}${BOLD}" "${f_fai}" "${RESET}"
    else
        printf "%s%s%s" "${DIM}" "${f_fai}" "${RESET}"
    fi
    printf "%${footer_pad}s║\n" ""

    hr_bot
}

# ── Redraw: move cursor up and overwrite ──────────────────────────────────────
redraw_table() {
    printf "\033[%dA" "${TABLE_LINES}"
    draw_table
}

# ── Kill children on Ctrl+C ───────────────────────────────────────────────────
cleanup_on_exit() {
    echo ""
    echo "Interrupted — stopping all test processes..."
    for i in "${!TESTS[@]}"; do
        [[ "${PIDS[$i]}" -gt 0 ]] && kill "${PIDS[$i]}" 2>/dev/null || true
    done
    exit 130
}
trap cleanup_on_exit INT TERM

# ── Launch all tests in parallel ──────────────────────────────────────────────
for i in "${!TESTS[@]}"; do
    # shellcheck disable=SC2086
    python "tck/connector/${TESTS[$i]}.py" ${EXTRA_ARGS} >"${LOGS[$i]}" 2>&1 &
    PIDS[$i]=$!
    START_TIMES[$i]=$(date +%s)
    STATUSES[$i]="RUNNING"
done

# ── Initial render ────────────────────────────────────────────────────────────
draw_table

# ── Live update loop ──────────────────────────────────────────────────────────
while true; do
    sleep 1
    all_done=true

    for i in "${!TESTS[@]}"; do
        [[ "${STATUSES[$i]}" == "RUNNING" ]] || continue

        if kill -0 "${PIDS[$i]}" 2>/dev/null; then
            all_done=false
        else
            set +e; wait "${PIDS[$i]}"; set -e
            DURATIONS[$i]=$(( $(date +%s) - START_TIMES[$i] ))
            RESULT=$(grep -oE 'RESULT: (PASS|FAIL)' "${LOGS[$i]}" 2>/dev/null \
                     | tail -1 | awk '{print $2}' || true)
            if   [[ "${RESULT}" == "PASS" ]]; then STATUSES[$i]="PASS"
            elif [[ "${RESULT}" == "FAIL" ]]; then STATUSES[$i]="FAIL"
            else STATUSES[$i]="FAIL"
            fi
        fi
    done

    redraw_table
    $all_done && break
done

# ── Log paths ─────────────────────────────────────────────────────────────────
echo ""
echo "Run ID : ${RUN_ID}"
echo "Logs   : ${LOG_DIR}/"
for i in "${!TESTS[@]}"; do
    printf "  %-46s  %s\n" "${TESTS[$i]}" "${LOGS[$i]}"
done
echo ""

# ── Exit code ─────────────────────────────────────────────────────────────────
FAIL_COUNT=0
for i in "${!TESTS[@]}"; do
    [[ "${STATUSES[$i]}" == "PASS" ]] || (( FAIL_COUNT++ )) || true
done
(( FAIL_COUNT > 0 )) && exit 1 || exit 0
