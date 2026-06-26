# CodeCritic

> Arduino code that compiles and simulates before you build.

CodeCritic converts natural language Arduino project descriptions into verified sketches and Wokwi circuit diagrams. Every output is compiled with `arduino-cli` and simulated with `wokwi-cli` before it reaches you — the only AI tool that tells you whether the output is correct before you touch hardware.


## How It Works

CodeCritic runs an autonomous LangGraph state machine:

1. **Planner** — converts your prompt into a structured spec with component list, pin map, and DSL assertions
2. **Circuit Designer** — generates a Wokwi `diagram.json` with verified power and signal wiring
3. **Coder** — generates a `.ino` sketch with correct pin assignments and library calls
4. **Dependency Injector** — resolves and installs required libraries via `arduino-cli lib search`
5. **Compiler** — runs `arduino-cli compile`, retries with targeted fixes on failure
6. **Inspector** — runs `wokwi-cli` simulation, evaluates DSL assertions against VCD waveform output
7. **Output** — only delivers results that pass verification

Verified outputs are cached by prompt hash — identical prompts return instantly on repeat runs.

## Features

- Natural language → verified Arduino sketch + circuit diagram
- Supports Arduino Uno, Nano, and Mega
- ~40 verified Wokwi components
- Self-correcting compile loop with targeted error analysis
- Three verification strategies (GPIO timing, serial output, compile-only)
- Two-tier cache (prompt hash + spec hash)
- Deploy button — flash directly to your board via USB (Chrome/Edge only)
- Live streaming pipeline progress via SSE

## Prerequisites

- Python 3.12+ with [uv](https://github.com/astral-sh/uv)
- Node.js 18+
- [arduino-cli](https://arduino.github.io/arduino-cli/latest/installation/) — must be on PATH
- [wokwi-cli](https://docs.wokwi.com/wokwi-ci/getting-started) — path set in `.env`

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/codecritic.git
cd codecritic
```

### 2. Install backend dependencies

```bash
uv sync
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Fill in all values in `.env` — see [Environment Variables](#environment-variables) below.

### 5. Set up arduino-cli

```bash
arduino-cli core update-index
arduino-cli core install arduino:avr        # Uno / Nano / Mega
```

### 6. Set up Supabase

Create a Supabase project and run the following table migrations:

```sql
-- Sessions
create table sessions (
  session_id text primary key,
  final_status text,
  iteration_count int,
  pass_score float,
  error_log text,
  complexity int,
  spec_hash text,
  hex_path text
);

-- Generation cache
create table generation_cache (
  prompt_hash text unique,
  spec_hash text,
  board text,
  prompt text,
  sketch_ino text,
  diagram_json text,
  pass_score float,
  hex_path text,
  hit_count int default 0
);

-- Components
create table components (
  id serial primary key,
  name text,
  wokwi_type text,
  pin_map jsonb,
  hit_count int default 0
);

-- Emulator quirks
create table emulator_quirks (
  id serial primary key,
  component text,
  description text
);
```

Enable RLS and grant service_role ALL on all tables.

### 7. Run the backend

```bash
uv run uvicorn backend.api.main:app --reload --port 8000
```

### 8. Run the frontend

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment Variables

```env
# LLM providers
GOOGLE_API_KEY=                  # Gemini API key
GROQ_API_KEY=                    # Groq API key (fallback)

# Supabase
SUPABASE_URL=                    # your Supabase project URL
SUPABASE_SERVICE_KEY=            # service_role key (not anon key)

# Wokwi
WOKWI_CLI_TOKEN=                 # from wokwi.com/dashboard
WOKWI_CLI_PATH=                  # full path to wokwi-cli executable
WOKWI_MONTHLY_BUDGET_SECONDS=    # simulation budget (e.g. 3600)

# Arduino
ARDUINO_DATA_DIR=                # directory for arduino-cli packages and libraries
HEX_CACHE_DIR=                   # directory to store compiled .hex files

# LangSmith tracing (optional)
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://apac.api.smith.langchain.com

# Tavily search (component datasheet lookup)
TAVILY_API_KEY=
```

## Supported Boards

| Board | FQBN |
|-------|------|
| Arduino Uno | `arduino:avr:uno` |
| Arduino Nano | `arduino:avr:nano` |
| Arduino Mega | `arduino:avr:mega` |

## Limitations

- Web Serial deploy requires Chrome or Edge — Firefox is not supported
- ESP32 is not supported in this release
- Simulation does not cover I2C pull-up timing or SPI clock edge accuracy
- Input devices (buttons, potentiometers) are compile-verified only — simulation not supported
- Backend requires local installation of `arduino-cli` and `wokwi-cli`

## Tech Stack

- **Orchestration** — LangGraph
- **LLMs** — Gemini 2.5 Flash / Flash Lite · Groq llama-3.3-70b / llama-3.1-8b
- **Backend** — Python 3.12 · FastAPI · FastMCP
- **Frontend** — Next.js 14 · Tailwind CSS
- **Persistence** — Supabase
- **Toolchain** — arduino-cli · wokwi-cli
- **Tracing** — LangSmith

## License

MIT