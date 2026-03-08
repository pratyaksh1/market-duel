"""
Audio Mixer
Stitches TTS audio segments into one final MP3.
Robust against failed/missing segments — uses segment metadata
instead of relying on array index alignment with the script.
"""

from pydub import AudioSegment
from pydub.effects import normalize
import os
import logging
import config

logger = logging.getLogger(__name__)

PAUSE_SAME_HOST_MS = 400
PAUSE_HOST_SWITCH_MS = 700


class AudioMixer:
    def __init__(self):
        self.output_dir = config.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def mix(self, segment_paths: list, script: str, output_filename: str) -> str:
        """
        Stitch audio segments into one MP3.

        segment_paths: list of file paths in order (some may be missing/failed)
        script: raw script text (used only for logging — NOT for index alignment)
        output_filename: final MP3 filename
        """
        logger.info(f"Mixing {len(segment_paths)} segments...")

        combined = AudioSegment.empty()
        prev_host = None
        successful = 0
        skipped = 0

        for path in segment_paths:
            # Skip missing or empty files
            if not path or not os.path.exists(path):
                skipped += 1
                continue

            if os.path.getsize(path) == 0:
                logger.warning(f"Skipping empty segment: {path}")
                skipped += 1
                continue

            # Determine host from filename (e.g. segment_0012_HOST_A.mp3)
            current_host = self._host_from_path(path)

            try:
                segment = AudioSegment.from_mp3(path)

                # Normalize individual segment volume
                segment = normalize(segment)

                # Add appropriate pause
                if prev_host is not None:
                    pause_ms = (
                        PAUSE_HOST_SWITCH_MS
                        if current_host != prev_host
                        else PAUSE_SAME_HOST_MS
                    )
                    combined += AudioSegment.silent(duration=pause_ms)

                combined += segment
                prev_host = current_host
                successful += 1

            except Exception as e:
                logger.warning(f"Failed to load segment {path}: {e}")
                skipped += 1
                continue

        if len(combined) == 0:
            raise RuntimeError(
                f"Audio mix is empty — all {len(segment_paths)} segments failed to load"
            )

        logger.info(
            f"Mixed {successful} segments successfully, skipped {skipped}. "
            f"Duration: {len(combined) / 60000:.1f} minutes"
        )

        # Final master normalize
        combined = normalize(combined)

        # Export
        output_path = os.path.join(self.output_dir, output_filename)
        combined.export(
            output_path,
            format="mp3",
            bitrate="128k",
            tags={
                "title": output_filename.replace(".mp3", "").replace("_", " "),
                "artist": "Market Duel AI",
                "album": "Daily Market Analysis",
                "genre": "Finance",
            },
        )

        logger.info(f"Podcast saved to: {output_path}")
        return output_path

    def cleanup(self, segment_paths: list):
        """Remove all temp segment files"""
        removed = 0
        for path in segment_paths:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
                    removed += 1
            except Exception as e:
                logger.warning(f"Could not delete temp file {path}: {e}")
        logger.info(f"Cleaned up {removed} temp files")

    def _host_from_path(self, path: str) -> str:
        """
        Extract host identifier from filename.
        Expected format: segment_0012_HOST_A.mp3 or segment_0012.mp3
        Falls back to None if not determinable.
        """
        basename = os.path.basename(path)
        if "HOST_A" in basename:
            return "HOST_A"
        elif "HOST_B" in basename:
            return "HOST_B"
        return None
