"""
Voice agent using Pipecat + AssemblyAI Universal-3 Pro Streaming.

Stack:
  Transport — Daily.co WebRTC
  STT       — AssemblyAI Universal-3 Pro Streaming (u3-rt-pro)
  LLM       — OpenAI GPT-4o with streaming
  TTS       — Cartesia Sonic
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import EndFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.transcript_processor import TranscriptProcessor
from pipecat.services.assemblyai.stt import AssemblyAISTTService, AssemblyAIConnectionParams
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.services.openai import OpenAILLMService
from pipecat.transports.services.daily import DailyParams, DailyTransport

load_dotenv()

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

SYSTEM_PROMPT = """
You are a friendly, helpful voice assistant powered by AssemblyAI Universal-3 Pro Streaming.
Keep responses under 2–3 sentences. Speak naturally — no markdown, no lists, no bullet points.
""".strip()


async def main(room_url: str, token: str | None = None):
    # ── Transport ───────────────────────────────────────────────────────────
    transport = DailyTransport(
        room_url,
        token,
        "Voice Assistant",
        DailyParams(
            audio_out_enabled=True,
            transcription_enabled=False,  # We use AssemblyAI, not Daily transcription
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            vad_audio_passthrough=True,
        ),
    )

    # ── STT: AssemblyAI Universal-3 Pro Streaming ───────────────────────────
    stt = AssemblyAISTTService(
        connection_params=AssemblyAIConnectionParams(
            api_key=os.environ["ASSEMBLYAI_API_KEY"],
            # Universal-3 Pro: 307 ms P50 latency, neural turn detection,
            # anti-hallucination, real-time diarization, mid-session prompting.
            speech_model="u3-rt-pro",
            # End-of-turn: emit when turn confidence crosses this threshold.
            end_of_turn_confidence_threshold=0.7,
            # Silence (ms) before speculative end-of-turn check.
            min_end_of_turn_silence_when_confident=300,
            # Hard ceiling for turn silence.
            max_turn_silence=1000,
        )
    )

    # ── LLM ────────────────────────────────────────────────────────────────
    llm = OpenAILLMService(api_key=os.environ["OPENAI_API_KEY"], model="gpt-4o")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    # ── TTS ────────────────────────────────────────────────────────────────
    tts = CartesiaTTSService(
        api_key=os.environ["CARTESIA_API_KEY"],
        voice_id="79a125e8-cd45-4c13-8a67-188112f4dd22",
    )

    # ── Transcript logging ─────────────────────────────────────────────────
    transcript = TranscriptProcessor()

    @transcript.event_handler("on_transcript_update")
    async def on_transcript_update(processor, frame):
        for msg in frame.messages:
            logger.info(f"[{msg.role}] {msg.content}")

    # ── Pipeline ───────────────────────────────────────────────────────────
    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            transcript.user(),
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
            transcript.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        PipelineParams(allow_interruptions=True),
    )

    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        await transport.capture_participant_transcription(participant["id"])
        # Greet the user on connection
        await task.queue_frames(
            [
                context_aggregator.user().get_context_frame(),
            ]
        )
        logger.info(f"Participant joined: {participant['id']}")

    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        await task.queue_frame(EndFrame())

    runner = PipelineRunner()
    await runner.run(task)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pipecat + AssemblyAI U3 Pro voice agent")
    parser.add_argument("--url", required=True, help="Daily.co room URL")
    parser.add_argument("--token", default=None, help="Daily.co meeting token (optional)")
    args = parser.parse_args()

    asyncio.run(main(args.url, args.token))
