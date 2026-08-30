# 📱 LinkedIn Post: Google Cloud GenMedia & Voice Canvas Studio

---

### Streamlined Post Copy (Ready to Publish)

Most AI video workflows still feel completely disjointed.

You generate an image in one tool. You switch to another to edit it (and lose the original style). You export to a third tool to animate, and then hunt for stock audio in a fourth.

Google Cloud recently rolled out four new GenMedia models on Vertex AI that change this dynamic:

• Gemini 3.5 Transcribe: Real-time multilingual speech recognition with low-latency streaming and zero text-prompt lag.
• Gemini 3.7 Flash: Sub-second tool calling and function calling for in-flight intent routing.
• Gemini 3.1 Flash Image: 16:9 widescreen image generation with conversational in-painting — modifying the scene without starting from scratch.
• Gemini Omni 1.1 Flash: Temporal video generation (720p 24fps) that natively synthesizes synchronized 48 kHz stereo ambient audio in the same pass.

I brought them together into Voice Canvas Studio — a 100% voice-driven creative loop.

Here is the exact flow:

1. Speak an idea:
"Paint a roaring mountain waterfall in a dense green forest."
➔ Real-time multilingual transcription captures the audio stream, and 3.1 Flash Image paints the 16:9 baseline.

2. Speak a revision:
"Add a traditional wooden bridge crossing over the river."
➔ 3.7 Flash routes the edit tool call, and 3.1 Flash Image edits in-place, keeping the landscape, camera angle, and style intact.

3. Speak motion & sound:
"Animate this with the sound of rushing water."
➔ Gemini Omni 1.1 Flash generates the 24fps motion AND the matching stereo soundscape natively in one shot.

The audio track is the biggest highlight here: Omni doesn’t just guess motion vectors; it synthesizes natural environmental acoustics (flowing water, wind, forest ambience) synced to the visual physics.

Entire pipeline runs on Google Cloud Vertex AI using standard Application Default Credentials (ADC) — no API keys required.

Code, architecture diagram, and full video are open-source on GitHub:
👉 https://github.com/upasana1105/UP_Demos/tree/main/gemini35-voice-to-action

(🔊 Make sure to unmute the video to hear the ambient audio generated natively by Omni 1.1 Flash!)

#GoogleCloud #VertexAI #Gemini #Omni11Flash #GenMedia #MultimodalAI #GenerativeAI #VoiceAI #OpenSource
