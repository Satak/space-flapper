import numpy as np
import wave
import struct
import math
import os

# Create sounds directory if it doesn't exist
os.makedirs('sounds', exist_ok=True)

def create_sound(filename, frequency, duration, volume=0.5, sample_rate=44100):
    """Create a simple sine wave sound"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    wave_data = np.sin(2 * np.pi * frequency * t)

    # Apply volume
    wave_data = wave_data * volume

    # Convert to 16-bit integer values
    wave_data = (wave_data * 32767).astype(np.int16)

    # Create WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data.tobytes())

def create_laser_sound(filename, duration=0.1, volume=0.3, sample_rate=44100):
    """Create a laser-like sound with descending pitch"""
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Create descending frequency
    freq_start = 1000
    freq_end = 200
    freq = np.linspace(freq_start, freq_end, len(t))

    wave_data = np.sin(2 * np.pi * freq * t)

    # Apply envelope
    envelope = np.exp(-3 * t/duration)
    wave_data = wave_data * envelope

    # Normalize and apply volume
    wave_data = wave_data / np.max(np.abs(wave_data)) * volume

    # Convert to 16-bit integer values
    wave_data = (wave_data * 32767).astype(np.int16)

    # Create WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data.tobytes())

def create_spread_laser_sound(filename, volume=0.4):
    """Create a clean laser sound for spread weapon"""
    duration = 0.30  # shorter duration
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Simple laser with slight pitch rise
    base_freq = 600
    freq = base_freq * (-1 + t * 0.8)  # Slight pitch rise

    # Main tone
    audio = np.sin(2 * np.pi * freq * t)

    # Apply envelope
    envelope = np.exp(-t * 20)  # Quick decay
    audio = audio * envelope

    # Normalize and apply volume
    audio = audio / np.max(np.abs(audio)) * volume

    # Normalize and convert to 16-bit integer
    audio = np.clip(audio, -1, 1)
    audio = np.int16(audio * 32767)

    # Save to file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())

def create_power_up_sound(filename, duration=0.4, volume=0.4, sample_rate=44100):
    """Create a power-up sound"""
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Create ascending frequency
    freq_start = 500
    freq_end = 1200
    freq = np.linspace(freq_start, freq_end, len(t))

    wave_data = np.sin(2 * np.pi * freq * t)

    # Apply envelope
    envelope = np.exp(-2 * t/duration)
    wave_data = wave_data * envelope

    # Normalize and apply volume
    wave_data = wave_data / np.max(np.abs(wave_data)) * volume

    # Convert to 16-bit integer values
    wave_data = (wave_data * 32767).astype(np.int16)

    # Create WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data.tobytes())

def create_enemy_death_sound(filename, duration=0.2, volume=0.4, sample_rate=44100):
    """Create an explosion sound"""
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Create noise-based explosion
    noise = np.random.normal(0, 1, len(t))

    # Add some low frequency rumble
    rumble = np.sin(2 * np.pi * 50 * t)

    wave_data = noise + rumble

    # Apply envelope
    envelope = np.exp(-10 * t/duration)
    wave_data = wave_data * envelope

    # Normalize and apply volume
    wave_data = wave_data / np.max(np.abs(wave_data)) * volume

    # Convert to 16-bit integer values
    wave_data = (wave_data * 32767).astype(np.int16)

    # Create WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data.tobytes())

def create_hit_sound(filename, duration=0.2, volume=0.4, sample_rate=44100):
    """Create a metallic hit sound with reverb"""
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Main impact - high frequency ping
    freq_start = 880  # A5 note
    freq_end = 440   # A4 note
    freq = np.exp(-5 * t/duration) * freq_start + (1 - np.exp(-5 * t/duration)) * freq_end
    wave_data = np.sin(2 * np.pi * freq * t)

    # Add metallic overtones
    overtones = [1.5, 2, 2.5, 3]  # Metallic harmonics
    for harmonic in overtones:
        wave_data += 0.3 * np.sin(2 * np.pi * freq * harmonic * t) * np.exp(-10 * t/duration)

    # Add some noise burst at the start
    noise_duration = int(sample_rate * 0.05)  # 50ms noise
    noise = np.random.normal(0, 0.5, len(t))
    noise_envelope = np.zeros_like(t)
    noise_envelope[:noise_duration] = np.exp(-10 * np.linspace(0, 1, noise_duration))
    wave_data += noise * noise_envelope

    # Apply main envelope
    envelope = np.exp(-5 * t/duration)
    wave_data = wave_data * envelope

    # Normalize and apply volume
    wave_data = wave_data / np.max(np.abs(wave_data)) * volume

    # Convert to 16-bit integer values
    wave_data = (wave_data * 32767).astype(np.int16)

    # Create WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data.tobytes())

def create_game_over_sound(filename, duration=1.0, volume=0.5, sample_rate=44100):
    """Create a sad game over melody"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    wave_data = np.zeros_like(t)

    # Define a short sad melody (A minor scale: A -> G -> F -> E)
    notes = [
        (440.0, 0.0, 0.25),    # A4
        (392.0, 0.25, 0.25),   # G4
        (349.2, 0.5, 0.25),    # F4
        (329.6, 0.75, 0.25)    # E4
    ]

    # Generate each note
    for freq, start, note_duration in notes:
        # Convert time to samples
        start_idx = int(start * sample_rate)
        duration_samples = int(note_duration * sample_rate)
        end_idx = start_idx + duration_samples

        # Create note envelope
        note_t = np.linspace(0, note_duration, duration_samples)
        envelope = np.exp(-2 * note_t/note_duration)

        # Generate note with slight vibrato
        vibrato = 1 + 0.02 * np.sin(2 * np.pi * 5 * note_t)  # 5 Hz vibrato
        note = np.sin(2 * np.pi * freq * note_t * vibrato)

        # Add some harmonics for richness
        note += 0.3 * np.sin(2 * np.pi * freq * 2 * note_t)  # First overtone
        note += 0.2 * np.sin(2 * np.pi * freq * 3 * note_t)   # Second overtone

        # Apply envelope to this note
        note = note * envelope

        # Add to main wave
        wave_data[start_idx:end_idx] += note

    # Normalize and apply volume
    wave_data = wave_data / np.max(np.abs(wave_data)) * volume

    # Convert to 16-bit integer values
    wave_data = (wave_data * 32767).astype(np.int16)

    # Create WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data.tobytes())

def create_charge_sound(filename, duration=0.1, volume=0.3, sample_rate=44100):
    """Create a rising pitch sound for charging"""
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Create rising frequency
    freq_start = 200
    freq_end = 800
    freq = np.linspace(freq_start, freq_end, len(t))

    wave_data = np.sin(2 * np.pi * freq * t)

    # Add some harmonics
    wave_data += 0.3 * np.sin(4 * np.pi * freq * t)

    # Apply envelope
    envelope = np.exp(-1 * t/duration)  # Gentler fade-out
    wave_data = wave_data * envelope

    # Normalize and apply volume
    wave_data = wave_data / np.max(np.abs(wave_data)) * volume

    # Convert to 16-bit integer values
    wave_data = (wave_data * 32767).astype(np.int16)

    # Create WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data.tobytes())

def create_shield_recharge_sound(filename):
    """Create a happy recharge sound for shield powerup"""
    duration = 0.4  # seconds
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Create a rising happy tone
    base_freq = 440  # Start at A4
    freq_mult = 1.5  # How much the frequency increases

    # Create two tones that rise in pitch
    tone1 = np.sin(2 * np.pi * base_freq * (1 + t * freq_mult) * t)
    tone2 = np.sin(2 * np.pi * (base_freq * 1.5) * (1 + t * freq_mult) * t)

    # Add some sparkle with high frequency beeps
    sparkle = np.sin(2 * np.pi * 1500 * t) * np.exp(-t * 20)
    sparkle += np.sin(2 * np.pi * 2000 * t) * np.exp(-t * 15)

    # Combine the sounds
    audio = tone1 * 0.3 + tone2 * 0.3 + sparkle * 0.2

    # Apply a happy envelope
    envelope = np.exp(-t * 3) * 0.7 + np.exp(-t * 8) * 0.3
    audio = audio * envelope

    # Normalize and convert to 16-bit integer
    audio = np.int16(audio * 32767)

    # Save to file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())

def create_ufo_hit_sound(filename):
    """Create a metallic hit sound for UFO being damaged"""
    duration = 0.1
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Metallic clang
    freq = 800
    audio = np.sin(2 * np.pi * freq * t) * 0.5
    audio += np.sin(2 * np.pi * freq * 1.5 * t) * 0.3

    # Quick decay
    envelope = np.exp(-t * 30)
    audio = audio * envelope

    audio = audio / np.max(np.abs(audio))

    # Normalize and save
    audio = np.clip(audio, -1, 1)
    audio = np.int16(audio * 32767)
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())

def create_ufo_death_sound(filename):
    """Create explosion sound for UFO death"""
    duration = 0.5
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Base explosion
    noise = np.random.uniform(-1, 1, len(t))

    # Add some metallic frequencies
    freqs = [300, 450, 600]
    audio = noise * 0.5
    for freq in freqs:
        audio += np.sin(2 * np.pi * freq * t) * 0.2

    # Envelope with quick attack and slow decay
    envelope = np.exp(-t * 8)
    audio = audio * envelope

    # Normalize and save
    audio = np.clip(audio, -1, 1)
    audio = np.int16(audio * 32767)
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())

def create_ufo_shoot_sound(filename, volume=0.3):
    """Create alien-like shooting sound"""
    duration = 0.2
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # High pitched alien sound
    freq = 2000
    freq_mod = 1 + np.sin(2 * np.pi * 20 * t) * 0.3  # Frequency modulation
    audio = np.sin(2 * np.pi * freq * t * freq_mod)

    # Add some noise
    noise = np.random.uniform(-1, 1, len(t)) * 0.1
    audio = audio + noise

    # Quick decay envelope
    envelope = np.exp(-t * 15)
    audio = audio * envelope
    audio = audio / np.max(np.abs(audio)) * volume

    # Normalize and save
    audio = np.clip(audio, -1, 1)
    audio = np.int16(audio * 32767)
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())

def create_title_music():
    # Create a heroic theme in C major
    sample_rate = 44100
    duration = 4.0  # 4 seconds of music
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Main melody (heroic theme)
    melody_notes = [
        (523.25, 0.5),    # C5 (0.5s)
        (659.25, 0.5),    # E5
        (783.99, 0.5),    # G5
        (1046.50, 0.5),   # C6
        (783.99, 0.5),    # G5
        (659.25, 0.5),    # E5
        (523.25, 1.0),    # C5 (held longer)
    ]

    # Create the melody
    melody = np.zeros_like(t)
    current_time = 0

    for freq, dur in melody_notes:
        samples = int(dur * sample_rate)
        start = int(current_time * sample_rate)
        end = start + samples
        if end > len(t):
            break

        # Add some envelope for smoother sound
        envelope = np.ones(samples)
        attack = int(0.05 * samples)
        decay = int(0.1 * samples)
        envelope[:attack] = np.linspace(0, 1, attack)
        envelope[-decay:] = np.linspace(1, 0, decay)

        note = 0.3 * np.sin(2 * np.pi * freq * t[start:end])  # Main sine wave
        # Add harmonics for richer sound
        note += 0.15 * np.sin(4 * np.pi * freq * t[start:end])  # First harmonic
        note += 0.1 * np.sin(6 * np.pi * freq * t[start:end])   # Second harmonic

        melody[start:end] += note * envelope
        current_time += dur

    # Add a bass line
    bass_freq = 261.63  # C4
    bass = 0.2 * np.sin(2 * np.pi * bass_freq * t)
    bass *= np.exp(-t)  # Add decay

    # Combine melody and bass
    audio = melody + bass

    # Normalize
    audio = np.int16(audio * 32767)

    # Save
    with wave.open('sounds/title_music.wav', 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())

def create_ufo_presence_sound():
    """Create a low wobbly sound for UFO presence"""
    sample_rate = 44100
    duration = 2.0  # 2 second sound that will loop
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Base frequency for UFO sound (low pitch)
    base_freq = 80.0

    # Create wobble effect with LFO (Low Frequency Oscillator)
    lfo_freq = 2.0  # 2 Hz wobble
    wobble = 10.0 * np.sin(2 * np.pi * lfo_freq * t)  # +/- 10 Hz wobble

    # Combine base frequency with wobble
    frequency = base_freq + wobble

    # Generate the sound with frequency modulation
    audio = 0.3 * np.sin(2 * np.pi * frequency * t)  # Main sine wave
    # Add some harmonics for richer sound
    audio += 0.15 * np.sin(4 * np.pi * frequency * t)  # First harmonic
    audio += 0.1 * np.sin(6 * np.pi * frequency * t)   # Second harmonic

    # Add subtle noise for texture
    noise = np.random.normal(0, 0.05, len(t))
    audio += noise * 0.1

    # Apply slow amplitude modulation
    amp_mod = 0.7 + 0.3 * np.sin(2 * np.pi * 0.5 * t)  # 0.5 Hz amplitude modulation
    audio *= amp_mod

    # Normalize and convert to 16-bit integer
    audio = np.int16(audio * 32767)

    # Save the sound
    with wave.open('sounds/ufo_presence.wav', 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())

def create_explosion_sound():
    """Create a powerful explosion sound effect"""
    # Parameters for explosion sound
    duration = 1.0  # 1 second
    sample_rate = 44100
    num_samples = int(duration * sample_rate)

    # Create initial burst of noise
    noise = np.random.uniform(-0.8, 0.8, num_samples)

    # Create low frequency rumble
    t = np.linspace(0, duration, num_samples)
    bass_freq = 80  # Low frequency for the rumble
    rumble = np.sin(2 * np.pi * bass_freq * t) * 0.5

    # Combine noise and rumble
    explosion = noise + rumble

    # Apply envelope
    attack_time = 0.02  # Very quick attack
    decay_time = 0.8   # Long decay

    attack_samples = int(attack_time * sample_rate)
    decay_samples = int(decay_time * sample_rate)

    # Create envelope
    envelope = np.ones(num_samples)
    # Attack phase
    envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    # Decay phase
    decay_start = attack_samples
    envelope[decay_start:] = np.linspace(1, 0, num_samples - decay_start)

    # Apply envelope to sound
    explosion = explosion * envelope

    # Add some distortion for more impact
    explosion = np.clip(explosion * 1.5, -1, 1)

    # Convert to 16-bit integer samples
    explosion = np.int16(explosion * 32767)

    # Save the sound
    with wave.open('sounds/explosion.wav', 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(explosion.tobytes())

def main():
    try:
        os.makedirs('sounds', exist_ok=True)
        create_laser_sound('sounds/shoot.wav')  # Basic laser shoot sound
        create_laser_sound('sounds/laser.wav', duration=0.2, volume=0.35)  # Longer, stronger laser sound
        create_spread_laser_sound('sounds/spread.wav')  # Clean laser for spread
        create_hit_sound('sounds/hit.wav')  # Hit sound
        create_game_over_sound('sounds/game_over.wav')  # Game over sound
        create_power_up_sound('sounds/power_up.wav')  # Mario-style power up sound
        create_enemy_death_sound('sounds/enemy_death.wav')  # Enemy death sound
        create_charge_sound('sounds/charge.wav')  # Rising pitch charge sound
        create_shield_recharge_sound('sounds/shield_recharge.wav')  # Happy recharge sound
        create_ufo_hit_sound('sounds/ufo_hit.wav')  # UFO hit sound
        create_ufo_death_sound('sounds/ufo_death.wav')  # UFO death sound
        create_ufo_shoot_sound('sounds/ufo_shoot.wav', volume=0.3)  # UFO shoot sound at 30% volume
        create_title_music()  # Title screen music
        create_ufo_presence_sound()  # UFO presence sound
        create_explosion_sound()
        print("Successfully created sound files!")
    except Exception as e:
        print(f"Error creating sounds: {str(e)}")

if __name__ == "__main__":
    main()
