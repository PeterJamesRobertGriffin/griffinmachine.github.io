#!/usr/bin/env python3

import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
CLIPS_DIR = PROJECT_ROOT / "clips"

# Stay comfortably below GitHub's 100 MB individual-file limit.
TARGET_MB = 90

# Don't bother re-encoding files already below this size.
TARGET_BYTES = TARGET_MB * 1024 * 1024

# Video/audio settings.
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"

VIDEO_CRF = 22
AUDIO_BITRATE_K = 128

# Maximum number of automatic attempts.
MAX_ATTEMPTS = 3

# Supported video extensions.
VIDEO_EXTENSIONS = {
    ".mp4",
    ".m4v",
    ".mov",
    ".mkv",
    ".webm",
    ".avi",
    ".ts",
    ".mts",
    ".m2ts",
}


# ============================================================
# HELPERS
# ============================================================

def command_exists(command: str) -> bool:
    """Return True if a command exists in PATH."""
    return shutil.which(command) is not None


def run_command(command: list[str]) -> subprocess.CompletedProcess:
    """Run a command and raise a useful error on failure."""
    print("\nRunning:")
    print(" ".join(f'"{x}"' if " " in x else x for x in command))

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        print("\nFFmpeg/FFprobe error:")
        print(result.stderr)
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}"
        )

    return result


def get_duration(path: Path) -> float:
    """Get video duration in seconds using ffprobe."""
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]

    result = run_command(command)

    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(
            f"Could not determine duration of {path}"
        ) from exc

    if not math.isfinite(duration) or duration <= 0:
        raise RuntimeError(
            f"Invalid duration for {path}: {duration}"
        )

    return duration


def format_size(size_bytes: int) -> str:
    """Human-readable file size."""
    mb = size_bytes / (1024 * 1024)
    return f"{mb:.2f} MB"


def calculate_video_bitrate(
    duration_seconds: float,
    target_bytes: int,
    audio_bitrate_k: int,
) -> int:
    """
    Calculate a video bitrate that should fit under the target size.

    We reserve space for audio and container overhead.
    """
    target_bits = target_bytes * 8

    audio_bits = (
        audio_bitrate_k
        * 1000
        * duration_seconds
    )

    # Reserve ~8% for MP4/container overhead and bitrate variance.
    usable_video_bits = (
        target_bits - audio_bits
    ) * 0.92

    if usable_video_bits <= 0:
        raise RuntimeError(
            "Target size is too small for this video's duration."
        )

    bitrate_bps = (
        usable_video_bits /
        duration_seconds
    )

    return max(100_000, int(bitrate_bps))


def make_temp_path(original: Path) -> Path:
    """Create a temporary output filename beside the original."""
    return original.with_name(
        original.stem + ".github_tmp" + original.suffix
    )


def compress_video(path: Path) -> bool:
    """
    Compress one video.

    Returns True if the file was changed, False if skipped.
    """

    original_size = path.stat().st_size

    print("\n" + "=" * 70)
    print(f"FILE: {path}")
    print(f"CURRENT SIZE: {format_size(original_size)}")

    # --------------------------------------------------------
    # Skip files already below target.
    # --------------------------------------------------------

    if original_size <= TARGET_BYTES:
        print(
            f"SKIP: already under {TARGET_MB} MB."
        )
        return False

    # --------------------------------------------------------
    # Get duration.
    # --------------------------------------------------------

    duration = get_duration(path)

    print(
        f"DURATION: {duration:.2f} seconds "
        f"({duration / 60:.2f} minutes)"
    )

    # --------------------------------------------------------
    # Generate output in temporary location.
    # --------------------------------------------------------

    temp_path = make_temp_path(path)

    if temp_path.exists():
        temp_path.unlink()

    bitrate_bps = calculate_video_bitrate(
        duration,
        TARGET_BYTES,
        AUDIO_BITRATE_K,
    )

    print(
        f"INITIAL VIDEO BITRATE: "
        f"{bitrate_bps / 1000:.0f} kbps"
    )

    # --------------------------------------------------------
    # Multiple attempts.
    # --------------------------------------------------------

    for attempt in range(1, MAX_ATTEMPTS + 1):

        print(
            f"\nEncoding attempt "
            f"{attempt}/{MAX_ATTEMPTS}"
        )

        # Slightly reduce bitrate on later attempts.
        attempt_bitrate = int(
            bitrate_bps *
            (0.82 ** (attempt - 1))
        )

        command = [
            "ffmpeg",
            "-y",

            "-i",
            str(path),

            # Video
            "-c:v",
            VIDEO_CODEC,

            "-b:v",
            str(attempt_bitrate),

            "-preset",
            "medium",

            "-pix_fmt",
            "yuv420p",

            # Audio
            "-c:a",
            AUDIO_CODEC,

            "-b:a",
            f"{AUDIO_BITRATE_K}k",

            # Keep compatibility high.
            "-movflags",
            "+faststart",

            str(temp_path),
        ]

        try:
            run_command(command)

        except RuntimeError:
            if temp_path.exists():
                temp_path.unlink()
            raise

        if not temp_path.exists():
            raise RuntimeError(
                f"FFmpeg did not produce output for {path}"
            )

        compressed_size = temp_path.stat().st_size

        print(
            f"RESULT SIZE: "
            f"{format_size(compressed_size)}"
        )

        # ----------------------------------------------------
        # Success.
        # ----------------------------------------------------

        if compressed_size <= TARGET_BYTES:

            print(
                f"SUCCESS: "
                f"{format_size(original_size)} "
                f"-> "
                f"{format_size(compressed_size)}"
            )

            # Replace original only after success.
            temp_path.replace(path)

            return True

        # ----------------------------------------------------
        # Too large.
        # ----------------------------------------------------

        print(
            f"Still above {TARGET_MB} MB."
        )

        if attempt < MAX_ATTEMPTS:
            print(
                "Retrying with a lower bitrate..."
            )

            temp_path.unlink()

    # --------------------------------------------------------
    # Failed all attempts.
    # --------------------------------------------------------

    if temp_path.exists():
        temp_path.unlink()

    raise RuntimeError(
        f"Could not compress {path} "
        f"below {TARGET_MB} MB after "
        f"{MAX_ATTEMPTS} attempts."
    )


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    print("=" * 70)
    print("GITHUB CLIPS COMPRESSOR")
    print("=" * 70)

    # --------------------------------------------------------
    # Check dependencies.
    # --------------------------------------------------------

    if not command_exists("ffmpeg"):
        print(
            "ERROR: ffmpeg was not found."
        )
        print(
            "Install it first, for example:"
        )
        print(
            "sudo pacman -S ffmpeg"
        )
        return 1

    if not command_exists("ffprobe"):
        print(
            "ERROR: ffprobe was not found."
        )
        return 1

    # --------------------------------------------------------
    # Check clips directory.
    # --------------------------------------------------------

    if not CLIPS_DIR.exists():
        print(
            f"ERROR: clips folder not found:"
        )
        print(CLIPS_DIR)
        return 1

    print(
        f"\nClips directory:"
        f"\n{CLIPS_DIR}"
    )

    print(
        f"\nTarget:"
        f"\nUnder {TARGET_MB} MB per video"
    )

    # --------------------------------------------------------
    # Find all videos recursively.
    # --------------------------------------------------------

    videos = sorted(
        path
        for path in CLIPS_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in VIDEO_EXTENSIONS
        and ".github_tmp" not in path.name
    )

    if not videos:
        print(
            "\nNo video files found."
        )
        return 0

    print(
        f"\nFound {len(videos)} video files."
    )

    # --------------------------------------------------------
    # Process files.
    # --------------------------------------------------------

    changed = 0
    skipped = 0
    failed = 0

    for index, video in enumerate(videos, start=1):

        print(
            f"\n\n[{index}/{len(videos)}]"
        )

        try:
            was_changed = compress_video(video)

            if was_changed:
                changed += 1
            else:
                skipped += 1

        except Exception as error:
            failed += 1

            print(
                f"\nERROR processing:"
                f"\n{video}"
            )
            print(error)

            # Continue with the next file rather than
            # stopping the entire batch.
            continue

    # --------------------------------------------------------
    # Summary.
    # --------------------------------------------------------

    print("\n\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

    print(
        f"Compressed: {changed}"
    )

    print(
        f"Skipped:    {skipped}"
    )

    print(
        f"Failed:     {failed}"
    )

    # --------------------------------------------------------
    # Final oversized-file scan.
    # --------------------------------------------------------

    print(
        "\nChecking for files still over "
        f"{TARGET_MB} MB..."
    )

    oversized = []

    for video in videos:

        if not video.exists():
            continue

        size = video.stat().st_size

        if size > TARGET_BYTES:
            oversized.append(
                (video, size)
            )

    if oversized:

        print(
            "\nWARNING: These files are still "
            f"over {TARGET_MB} MB:"
        )

        for video, size in oversized:
            print(
                f"{format_size(size):>10}  {video}"
            )

        return 2

    print(
        "\nAll videos are under the target size."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())