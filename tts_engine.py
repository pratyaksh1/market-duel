"""
TTS Engine
Default: Edge TTS (free, Microsoft neural voices)
Upgrade: set ElevenLabs env vars to auto-switch to ElevenLabs
"""

import asyncio
import edge_tts
import os
import logging
import httpx
import config

logger = logging.getLogger(__name__)

USE_ELEVENLABS = bool(
    config.ELEVENLABS_API_KEY
    and config.ELEVENLABS_HOST_A_VOICE_ID
    and config.ELEVENLABS_HOST_B_VOICE_ID
)


class TTSEngine:
    def __init__(self):
        self.voice_a = config.EDGE_TTS_VOICE_A
        self.voice_b = config.EDGE_TTS_VOICE_B
        self.temp_dir = config.TEMP_DIR
        os.makedirs(self.temp_dir, exist_ok=True)

    async def generate_audio_segments(self, script: str) -> list:
        """Parse script and render each line as an MP3 segment"""
        lines = self._parse_script(script)
        logger.info(f"Rendering {len(lines)} dialogue lines via {'ElevenLabs' if USE_ELEVENLABS else 'Edge TTS'}...")

        # Process in batches to avoid overloading
        batch_size = 10
        all_paths = []

        for i in range(0, len(lines), batch_size):
            batch = lines[i: i + batch_size]
            tasks = [self._render_line(line_data) for line_data in batch]
            paths = await asyncio.gather(*tasks, return_exceptions=True)

            for p in paths:
                if isinstance(p, Exception):
                    logger.warning(f"Segment render failed: {p}")
                    all_paths.append(None)
                else:
                    all_paths.append(p)

            logger.info(f"Batch {i // batch_size + 1} complete ({min(i + batch_size, len(lines))}/{len(lines)} lines)")

        valid = [p for p in all_paths if p]
        logger.info(f"Successfully rendered {len(valid)}/{len(lines)} segments")
        return all_paths  # Return full list including Nones — mixer handles gaps

    async def _render_line(self, line_data: tuple) -> str | None:
        index, host, text = line_data

        if not text.strip():
            return None

        # Filename includes HOST_A/HOST_B so audio_mixer can detect host from filename
        filename = f"segment_{index:04d}_{host}.mp3"
        output_path = os.path.join(self.temp_dir, filename)

        try:
            if USE_ELEVENLABS:
                await self._elevenlabs_tts(host, text, output_path)
            else:
                await self._edge_tts(host, text, output_path)
            return output_path
        except Exception as e:
            logger.error(f"TTS failed for segment {index} ({host}): {e}")
            return None

    async def _edge_tts(self, host: str, text: str, output_path: str):
        """Free Edge TTS with Indian English voices"""
        voice = self.voice_a if host == "HOST_A" else self.voice_b
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    async def _elevenlabs_tts(self, host: str, text: str, output_path: str):
        """ElevenLabs TTS — upgrade path"""
        voice_id = (
            config.ELEVENLABS_HOST_A_VOICE_ID
            if host == "HOST_A"
            else config.ELEVENLABS_HOST_B_VOICE_ID
        )
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": config.ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
            )
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(resp.content)

    def _parse_script(self, script: str) -> list:
        """Parse raw script into (index, host, text) tuples"""
        lines = []
        i = 0
        for line in script.strip().splitlines():
            line = line.strip()
            if line.startswith("HOST_A:"):
                text = line[len("HOST_A:"):].strip()
                if text:
                    lines.append((i, "HOST_A", text))
                    i += 1
            elif line.startswith("HOST_B:"):
                text = line[len("HOST_B:"):].strip()
                if text:
                    lines.append((i, "HOST_B", text))
                    i += 1
        return lines
