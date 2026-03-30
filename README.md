# Pipecat voice agent with AssemblyAI Universal-3 Pro Streaming

Build a real-time voice agent using **Pipecat** — Daily.co's open-source Voice AI framework — and the **AssemblyAI Universal-3 Pro Streaming model** as the speech-to-text engine.

Pipecat's modular pipeline design means you can swap any component without touching the rest. AssemblyAI has a first-party Pipecat plugin with full Universal-3 Pro Streaming support — no manual WebSocket wiring required.

## Why AssemblyAI in Pipecat?

| Metric | AssemblyAI Universal-3 Pro | Deepgram Nova-3 |
|--------|---------------------------|-----------------|
| P50 latency | **307 ms** | 516 ms |
| P99 latency | **1,012 ms** | 1,907 ms |
| Word Error Rate | **8.14%** | 9.87% |
| Neural turn detection | ✅ | ❌ (VAD only) |
| Mid-session prompting | ✅ | ❌ |
| Anti-hallucination | ✅ | ❌ |
| Real-time diarization | ✅ | ❌ |

The 41% latency advantage is noticeable in live conversation — and the neural turn detection means fewer awkward double-responses when users pause mid-thought.

## Architecture

```
Daily.co WebRTC room
       │ audio
       ▼
  Pipecat pipeline
  ┌─────────────────────────────────────────────┐
  │ transport.input()                           │
  │      │                                      │
  │ AssemblyAI Universal-3 Pro Streaming (STT)  │
  │      │ transcript + turn signal             │
  │ TranscriptProcessor                         │
  │      │                                      │
  │ OpenAI GPT-4o (streaming)                  │
  │      │ text chunks                          │
  │ Cartesia Sonic (TTS)                        │
  │      │ audio                                │
  │ transport.output()                          │
  └─────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.11+
- [AssemblyAI API key](https://app.assemblyai.com)
- [Daily.co API key](https://dashboard.daily.co)
- [OpenAI API key](https://platform.openai.com/api-keys)
- [Cartesia API key](https://play.cartesia.ai)

## Quick start

```bash
git clone https://github.com/kelseyefoster/voice-agent-pipecat-universal-3-pro
cd voice-agent-pipecat-universal-3-pro

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your API keys

# Create a Daily.co room
python create_room.py

# Start the bot (paste the room URL from above)
python bot.py --url https://your-name.daily.co/your-room
```

Open the room URL in your browser and start talking.

## Universal-3 Pro Streaming features

### Keyterm prompting

Boost accuracy on domain-specific vocabulary without restarting the session:

```python
stt = AssemblyAISTTService(
    connection_params=AssemblyAIConnectionParams(
        api_key=os.environ["ASSEMBLYAI_API_KEY"],
        speech_model="u3-rt-pro",
        keyterms_prompt=["AssemblyAI", "Universal-3", "Pipecat", "YourBrandName"],
    )
)
```

Up to 1,000 terms per session. Essential for medical, legal, and financial applications.

### Real-time speaker diarization

```python
connection_params=AssemblyAIConnectionParams(
    api_key=os.environ["ASSEMBLYAI_API_KEY"],
    speech_model="u3-rt-pro",
    speaker_labels=True,
    max_speakers=2,
)
```

### Multilingual support

```python
connection_params=AssemblyAIConnectionParams(
    api_key=os.environ["ASSEMBLYAI_API_KEY"],
    speech_model="u3-rt-pro",
    language_detection=True,  # auto-detect language per turn
)
```

Supported languages: English, Spanish, French, German, Italian, Portuguese.

## Tuning turn detection

```python
connection_params=AssemblyAIConnectionParams(
    api_key=os.environ["ASSEMBLYAI_API_KEY"],
    speech_model="u3-rt-pro",
    # Emit turn end when confidence crosses this threshold
    end_of_turn_confidence_threshold=0.7,
    # Minimum silence (ms) before a confident end-of-turn fires
    min_end_of_turn_silence_when_confident=300,
    # Hard ceiling — force turn end after this much silence
    max_turn_silence=1000,
)
```

## Deploy to PipecatCloud

```bash
pip install pipecatcloud
pcc auth login
pcc init
pcc secrets set my-agent-secrets --file .env
pcc deploy
```

## Related tutorials

- [Tutorial 01: LiveKit + Universal-3 Pro Streaming](../01-livekit-universal-3-pro) — managed LiveKit infrastructure instead of Daily.co
- [Tutorial 06: Daily.co bare-metal](../06-dailyco-universal-3-pro) — same Daily.co transport without the Pipecat abstraction layer
- [Tutorial 05: raw WebSocket voice agent](../05-websocket-universal-3-pro) — understand the underlying AssemblyAI WebSocket protocol

## Resources

- [AssemblyAI Pipecat integration guide](https://www.assemblyai.com/docs/integrations/pipecat)
- [Pipecat docs](https://docs.pipecat.ai)
- [AssemblyAI Universal-3 Pro Streaming](https://www.assemblyai.com/blog/universal-3-pro-streaming)
- [Pipecat GitHub](https://github.com/pipecat-ai/pipecat)

---

<div class="blog-cta_component">
  <div class="blog-cta_title">Add AssemblyAI to your Pipecat pipeline</div>
  <div class="blog-cta_rt w-richtext">
    <p>Sign up for a free AssemblyAI account and drop Universal-3 Pro Streaming into any Pipecat voice agent in minutes.</p>
  </div>
  <a href="https://www.assemblyai.com/dashboard/signup" class="button w-button">Start building</a>
</div>

<div class="blog-cta_component">
  <div class="blog-cta_title">Experiment with real-time turn detection</div>
  <div class="blog-cta_rt w-richtext">
    <p>Try streaming transcription in our Playground and observe how punctuation and silence handling shape turn boundaries in real time. Compare behaviors across Universal-3 Pro Streaming and Universal-streaming models.</p>
  </div>
  <a href="https://www.assemblyai.com/playground" class="button w-button">Open playground</a>
</div>
