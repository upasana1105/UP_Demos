/**
 * Voice Canvas Studio — Pure Apple Voice Interface
 * Driven entirely by user voice input via Gemini 3.5 Transcribe + 3.1 Flash Image
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let isRecording = false;
  let mediaRecorder = null;
  let audioChunks = [];
  let audioContext = null;
  let analyser = null;
  let dataArray = null;
  let animationFrameId = null;
  let currentActiveImageUrl = null;
  let previousArtworkUrl = null;
  let showingOriginal = false;
  let currentVideoUrl = null;
  let isShowingVideo = false;
  let liveCapturedText = "";
  let speechRecognizer = null;

  // DOM Elements
  const blankCanvasState = document.getElementById("blankCanvasState");
  const activeArtworkContainer = document.getElementById("activeArtworkContainer");
  const canvasImage = document.getElementById("canvasImage");
  const canvasVideo = document.getElementById("canvasVideo");
  const compareImage = document.getElementById("compareImage");
  const compareToggleBtn = document.getElementById("compareToggleBtn");
  const compareToggleLabel = document.getElementById("compareToggleLabel");
  const viewToggleBtn = document.getElementById("viewToggleBtn");
  const viewToggleLabel = document.getElementById("viewToggleLabel");
  const soundToggleBtn = document.getElementById("soundToggleBtn");
  const soundToggleLabel = document.getElementById("soundToggleLabel");
  const soundIcon = document.getElementById("soundIcon");
  const unmuteOverlayBtn = document.getElementById("unmuteOverlayBtn");
  const downloadBtn = document.getElementById("downloadBtn");
  const canvasPaintingOverlay = document.getElementById("canvasPaintingOverlay");
  const paintingStatusTitle = document.getElementById("paintingStatusTitle");
  const paintingStatusSubtitle = document.getElementById("paintingStatusSubtitle");
  const canvasProgressBar = document.getElementById("canvasProgressBar");
  const captionText = document.getElementById("captionText");
  const masterMicBtn = document.getElementById("masterMicBtn");
  const micIconContainer = document.getElementById("micIconContainer");
  const micPulseRing = document.getElementById("micPulseRing");
  const micStatusText = document.getElementById("micStatusText");
  const waveContainer = document.getElementById("waveContainer");
  const liveWaveCanvas = document.getElementById("liveWaveCanvas");
  const waveCtx = liveWaveCanvas.getContext("2d");
  const micButtonLabel = document.getElementById("micButtonLabel");
  const quotaAlertBanner = document.getElementById("quotaAlertBanner");
  const quotaAlertMsg = document.getElementById("quotaAlertMsg");
  const dismissQuotaBtn = document.getElementById("dismissQuotaBtn");

  // Bulletproof Inline SVG Icon Helpers
  function setMicIconIdle() {
    if (!micIconContainer) return;
    micIconContainer.innerHTML = `
      <svg class="w-5 h-5 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
        <line x1="12" x2="12" y1="19" y2="22"/>
      </svg>
    `;
  }

  function setMicIconActive() {
    if (!micIconContainer) return;
    micIconContainer.innerHTML = `
      <svg class="w-5 h-5 text-stone-950 animate-pulse" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
      </svg>
    `;
  }

  function setMicIconLoading() {
    if (!micIconContainer) return;
    micIconContainer.innerHTML = `
      <svg class="w-5 h-5 text-white animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
      </svg>
    `;
  }

  // Subtle Success Chime (Web Audio API)
  function playSuccessChime() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
      osc.frequency.exponentialRampToValueAtTime(880.0, ctx.currentTime + 0.18); // A5
      gain.gain.setValueAtTime(0.08, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.5);
    } catch (e) {}
  }

  let liveTranscribeInterval = null;
  let isTranscribingChunk = false;

  // Apply Art Result to Canvas
  function applyArtResult(data) {
    canvasProgressBar.style.width = "100%";
    setTimeout(() => {
      canvasPaintingOverlay.classList.add("hidden");
    }, 200);

    if (!data || !data.success) {
      const msg = (data && data.error) ? data.error : "Generation failed. Please try again.";
      showQuotaAlert(msg);
      captionText.innerHTML = `<span class="text-amber-800 text-xs font-sans">${msg}</span>`;
      micStatusText.innerText = (data && data.error_type === "quota_exceeded") ? "Omni 1.1 Quota Limit on GCP. Click 'Enter API Key' to use AI Studio." : "Operation notice";
      if (micButtonLabel) {
        micButtonLabel.classList.remove("text-stone-950");
        micButtonLabel.classList.add("text-white");
        micButtonLabel.innerText = "Tap to Speak";
      }
      setMicIconIdle();
      masterMicBtn.classList.remove("active-recording");
      return;
    }

    hideQuotaAlert();
    playSuccessChime();

    if (data.is_video && data.video_url) {
      currentVideoUrl = data.video_url;
      isShowingVideo = true;
      canvasVideo.src = data.video_url;
      canvasVideo.classList.remove("hidden");
      canvasImage.classList.add("hidden");
      viewToggleBtn.classList.remove("hidden");
      viewToggleLabel.innerText = "View Still";
      downloadBtn.href = data.video_url;
      downloadBtn.download = "omni_artwork.mp4";
      captionText.innerHTML = `🎬 <i>"${data.transcript}"</i>`;
      micStatusText.innerText = "Gemini Omni 1.1 Flash animation active. Speak to edit, or toggle still view.";
      if (micButtonLabel) {
        micButtonLabel.classList.remove("text-stone-950");
        micButtonLabel.classList.add("text-white");
        micButtonLabel.innerText = "Tap to Speak";
      }
      setMicIconIdle();
      masterMicBtn.classList.remove("active-recording");
      return;
    }

    // New still image
    currentVideoUrl = null;
    isShowingVideo = false;
    canvasVideo.pause();
    canvasVideo.classList.add("hidden");
    canvasImage.classList.remove("hidden");
    viewToggleBtn.classList.add("hidden");

    if (data.is_edit && currentActiveImageUrl) {
      previousArtworkUrl = currentActiveImageUrl;
      compareToggleBtn.classList.remove("hidden");
    }

    currentActiveImageUrl = data.image_url;
    
    // Progressive unblur reveal
    canvasImage.classList.remove("progressive-reveal");
    void canvasImage.offsetWidth;
    canvasImage.classList.add("progressive-reveal");
    
    canvasImage.src = data.image_url;
    downloadBtn.href = data.image_url;
    downloadBtn.download = "studio_art.png";

    // Transition from blank to active
    blankCanvasState.classList.add("hidden");
    activeArtworkContainer.classList.remove("hidden");

    captionText.innerHTML = `"${data.transcript}"`;
    if (micButtonLabel) {
      micButtonLabel.classList.remove("text-stone-950");
      micButtonLabel.classList.add("text-white");
      micButtonLabel.innerText = "Tap to Speak";
    }
    setMicIconIdle();
    masterMicBtn.classList.remove("active-recording");
    micStatusText.innerText = "Speak in any language to edit this artwork, then press the button";
  }

  // Clear to Blank Canvas
  clearCanvasBtn.addEventListener("click", async () => {
    try {
      await fetch("/api/clear_canvas", { method: "POST" });
    } catch (e) {}
    currentActiveImageUrl = null;
    previousArtworkUrl = null;
    currentVideoUrl = null;
    isShowingVideo = false;
    canvasVideo.pause();
    canvasVideo.src = "";
    canvasVideo.classList.add("hidden");
    canvasImage.classList.remove("hidden");
    viewToggleBtn.classList.add("hidden");
    if (soundToggleBtn) soundToggleBtn.classList.add("hidden");
    if (unmuteOverlayBtn) unmuteOverlayBtn.classList.add("hidden");
    canvasImage.src = "";
    activeArtworkContainer.classList.add("hidden");
    blankCanvasState.classList.remove("hidden");
    compareToggleBtn.classList.add("hidden");
    captionText.innerText = "";
    micStatusText.innerText = "Speak your idea, then press the button to sculpt";
    liveCapturedText = "";
  });

  // Compare Toggle Button (Before / After)
  compareToggleBtn.addEventListener("click", () => {
    if (!previousArtworkUrl) return;
    showingOriginal = !showingOriginal;
    if (showingOriginal) {
      canvasImage.src = previousArtworkUrl;
      compareToggleLabel.innerText = "Show Edit";
      compareToggleBtn.classList.add("bg-stone-900", "text-white");
    } else {
      canvasImage.src = currentActiveImageUrl;
      compareToggleLabel.innerText = "Show Original";
      compareToggleBtn.classList.remove("bg-stone-900", "text-white");
    }
  });

  async function triggerOmniAnimation(motionPrompt) {
    canvasPaintingOverlay.classList.remove("hidden");
    canvasProgressBar.style.width = "25%";
    paintingStatusTitle.innerText = "Animating with Gemini Omni 1.1 Flash...";
    paintingStatusSubtitle.innerText = "Synthesizing cinematic temporal motion from canvas artwork";
    playChime();

    let p = 25;
    const progressInterval = setInterval(() => {
      p = Math.min(p + 8, 92);
      canvasProgressBar.style.width = `${p}%`;
    }, 400);

    try {
      const res = await fetch("/api/animate_artwork", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: motionPrompt || "Cinematic subtle ambient motion, smooth gentle camera drift, photorealistic atmosphere, 8k.",
          resolution: "360p",
          aspect_ratio: "16:9"
        })
      });
      clearInterval(progressInterval);
      canvasProgressBar.style.width = "100%";

      const data = await res.json();
      setTimeout(() => {
        canvasPaintingOverlay.classList.add("hidden");
      }, 250);

      if (data.success && data.video_url) {
        hideQuotaAlert();
        playSuccessChime();
        currentVideoUrl = data.video_url;
        isShowingVideo = true;
        canvasVideo.src = data.video_url;
        canvasVideo.classList.remove("hidden");
        canvasImage.classList.add("hidden");
        canvasVideo.volume = 1.0;
        canvasVideo.muted = false;
        canvasVideo.play().then(() => {
          updateSoundButton(true);
          if (unmuteOverlayBtn) unmuteOverlayBtn.classList.add("hidden");
        }).catch(() => {
          // Autoplay with audio restricted by browser until user interaction
          canvasVideo.muted = true;
          canvasVideo.play();
          updateSoundButton(false);
          if (unmuteOverlayBtn) unmuteOverlayBtn.classList.remove("hidden");
        });
        viewToggleBtn.classList.remove("hidden");
        viewToggleLabel.innerText = "View Still";
        if (soundToggleBtn) soundToggleBtn.classList.remove("hidden");
        downloadBtn.href = data.video_url;
        downloadBtn.download = "omni_artwork.mp4";
        captionText.innerHTML = `🎬 <i>Animated with Gemini Omni 1.1 Flash</i>`;
        micStatusText.innerText = "Gemini Omni 1.1 Flash animation active. Speak to edit artwork, or toggle still view.";
      } else {
        const msg = data.error || "Omni 1.1 animation unavailable";
        showQuotaAlert(msg);
        captionText.innerHTML = `<span class="text-amber-800 text-xs font-sans">${msg}</span>`;
        micStatusText.innerText = data.error_type === "quota_exceeded" ? "Omni 1.1 Quota Limit on GCP. Set GEMINI_API_KEY to test via AI Studio." : "Animation notice";
      }
    } catch (err) {
      clearInterval(progressInterval);
      canvasPaintingOverlay.classList.add("hidden");
      captionText.innerText = "Animation service temporarily unavailable.";
    }
  }

  // Quota Alert & API Key Handlers
  function showQuotaAlert(msg) {
    if (quotaAlertBanner && quotaAlertMsg) {
      quotaAlertMsg.innerText = msg;
      quotaAlertBanner.classList.remove("hidden");
    }
  }

  function hideQuotaAlert() {
    if (quotaAlertBanner) quotaAlertBanner.classList.add("hidden");
  }

  if (dismissQuotaBtn) {
    dismissQuotaBtn.addEventListener("click", hideQuotaAlert);
  }

  // Video Audio Mute/Unmute Control
  function updateSoundButton(isAudioPlaying) {
    if (!soundToggleBtn || !soundToggleLabel || !soundIcon) return;
    if (isAudioPlaying) {
      soundToggleLabel.innerText = "Sound On";
      soundIcon.innerHTML = `
        <svg class="w-3.5 h-3.5 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
          <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
        </svg>`;
    } else {
      soundToggleLabel.innerText = "Muted";
      soundIcon.innerHTML = `
        <svg class="w-3.5 h-3.5 text-stone-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
          <line x1="23" y1="9" x2="17" y2="15"/>
          <line x1="17" y1="9" x2="23" y2="15"/>
        </svg>`;
    }
  }

  if (soundToggleBtn) {
    soundToggleBtn.addEventListener("click", () => {
      if (!canvasVideo) return;
      canvasVideo.muted = !canvasVideo.muted;
      canvasVideo.volume = 1.0;
      updateSoundButton(!canvasVideo.muted);
      if (!canvasVideo.muted && unmuteOverlayBtn) {
        unmuteOverlayBtn.classList.add("hidden");
      }
      if (!canvasVideo.muted && canvasVideo.paused) {
        canvasVideo.play();
      }
    });
  }

  if (unmuteOverlayBtn) {
    unmuteOverlayBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (!canvasVideo) return;
      canvasVideo.muted = false;
      canvasVideo.volume = 1.0;
      canvasVideo.play();
      updateSoundButton(true);
      unmuteOverlayBtn.classList.add("hidden");
    });
  }

  if (canvasVideo) {
    canvasVideo.addEventListener("click", () => {
      canvasVideo.muted = !canvasVideo.muted;
      canvasVideo.volume = 1.0;
      updateSoundButton(!canvasVideo.muted);
      if (!canvasVideo.muted && unmuteOverlayBtn) {
        unmuteOverlayBtn.classList.add("hidden");
      }
      if (canvasVideo.paused) canvasVideo.play();
    });
  }

  // Toggle between Still Image and Video View
  if (viewToggleBtn) {
    viewToggleBtn.addEventListener("click", () => {
      if (!currentVideoUrl) return;
      isShowingVideo = !isShowingVideo;
      if (isShowingVideo) {
        canvasVideo.classList.remove("hidden");
        canvasImage.classList.add("hidden");
        canvasVideo.play();
        viewToggleLabel.innerText = "View Still";
        if (soundToggleBtn) soundToggleBtn.classList.remove("hidden");
        if (canvasVideo.muted && unmuteOverlayBtn) unmuteOverlayBtn.classList.remove("hidden");
        downloadBtn.href = currentVideoUrl;
        downloadBtn.download = "omni_artwork.mp4";
      } else {
        canvasVideo.classList.add("hidden");
        canvasImage.classList.remove("hidden");
        canvasVideo.pause();
        viewToggleLabel.innerText = "View Video";
        if (soundToggleBtn) soundToggleBtn.classList.add("hidden");
        if (unmuteOverlayBtn) unmuteOverlayBtn.classList.add("hidden");
        downloadBtn.href = currentActiveImageUrl;
        downloadBtn.download = "studio_art.png";
      }
    });
  }

  // Microphone Recording Control: Start on first click, Create Artwork on second click
  masterMicBtn.addEventListener("click", () => {
    if (!isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
  });

  async function startRecording() {
    liveCapturedText = "";
    const isEdit = !!currentActiveImageUrl;
    captionText.innerHTML = isEdit
      ? '"Listening... speak your edit in any language or mix mid-sentence<span class="cursor-blink"></span>"'
      : '"Listening... speak your vision in any language or mix mid-sentence<span class="cursor-blink"></span>"';
    micStatusText.innerText = isEdit
      ? "Listening to your edit... Press button when done to apply changes"
      : "Listening to your vision... Press button when done to create artwork";

    // Visual transformation: Button becomes active recording instrument
    masterMicBtn.classList.add("active-recording");
    if (micButtonLabel) {
      micButtonLabel.classList.remove("text-white");
      micButtonLabel.classList.add("text-stone-950");
      micButtonLabel.innerText = isEdit ? "Apply Edit ✨" : "Sculpt Artwork ✨";
    }
    setMicIconActive();
    micPulseRing.classList.remove("hidden");
    waveContainer.classList.remove("hidden");
    waveContainer.classList.add("flex");

    // Capture User Media Microphone Stream directly for Gemini 3.5 Transcribe
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Browser blocks microphone on non-HTTPS origins.");
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContext.createMediaStreamSource(stream);
      analyser = audioContext.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);
      dataArray = new Uint8Array(analyser.frequencyBinCount);

      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) audioChunks.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        if (liveTranscribeInterval) {
          clearInterval(liveTranscribeInterval);
          liveTranscribeInterval = null;
        }
        const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
        stream.getTracks().forEach((t) => t.stop());
        await processAudioInput(audioBlob);
      };

      // Periodic live streaming transcription to Gemini 3.5 Transcribe every 1.1s
      if (liveTranscribeInterval) clearInterval(liveTranscribeInterval);
      liveTranscribeInterval = setInterval(async () => {
        if (!isRecording || audioChunks.length === 0 || isTranscribingChunk) return;
        isTranscribingChunk = true;
        try {
          const interimBlob = new Blob(audioChunks, { type: "audio/wav" });
          const reader = new FileReader();
          reader.onloadend = async () => {
            try {
              const base64Audio = reader.result.split(",")[1];
              const res = await fetch("/api/live_transcribe", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ audio_base64: base64Audio, mime_type: "audio/wav" }),
              });
              const data = await res.json();
              if (data.transcript && isRecording) {
                liveCapturedText = data.transcript;
                captionText.innerHTML = `"${data.transcript}<span class="cursor-blink"></span>"`;
              }
            } catch (e) {
            } finally {
              isTranscribingChunk = false;
            }
          };
          reader.readAsDataURL(interimBlob);
        } catch (e) {
          isTranscribingChunk = false;
        }
      }, 1100);

      mediaRecorder.start(600);
      isRecording = true;

      // Render Waveform
      liveWaveCanvas.width = waveContainer.clientWidth || 224;
      liveWaveCanvas.height = waveContainer.clientHeight || 36;
      renderLiveWaveform();

    } catch (err) {
      console.error("Mic stream error:", err);
      isRecording = false;
      micStatusText.innerText = "Please enable microphone in browser";
      captionText.innerHTML = '"Microphone permission needed: please allow microphone access in your browser."';
      masterMicBtn.classList.remove("bg-amber-500", "hover:bg-amber-600", "text-stone-950");
      masterMicBtn.classList.add("bg-stone-900", "hover:bg-stone-800", "text-white");
      if (micButtonLabel) {
        micButtonLabel.classList.remove("text-stone-950");
        micButtonLabel.classList.add("text-white");
        micButtonLabel.innerText = "Tap to Speak";
      }
      setMicIconIdle();
      micPulseRing.classList.add("hidden");
      waveContainer.classList.add("hidden");
    }
  }

  function stopRecording() {
    const isEdit = !!currentActiveImageUrl;
    if (liveTranscribeInterval) {
      clearInterval(liveTranscribeInterval);
      liveTranscribeInterval = null;
    }

    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    } else if (liveCapturedText) {
      processTextInput(liveCapturedText);
    }
    isRecording = false;
    masterMicBtn.classList.remove("active-recording");
    if (micButtonLabel) {
      micButtonLabel.classList.remove("text-stone-950");
      micButtonLabel.classList.add("text-white");
      micButtonLabel.innerText = isEdit ? "Applying Edit..." : "Sculpting Artwork...";
    }
    setMicIconLoading();
    micPulseRing.classList.add("hidden");
    waveContainer.classList.add("hidden");
    waveContainer.classList.remove("flex");
    micStatusText.innerText = isEdit ? "Gemini is editing existing artwork..." : "Synthesizing with Gemini 3.1 Flash Image...";
    cancelAnimationFrame(animationFrameId);
  }

  function renderLiveWaveform() {
    if (!isRecording) return;
    analyser.getByteFrequencyData(dataArray);

    waveCtx.clearRect(0, 0, liveWaveCanvas.width, liveWaveCanvas.height);
    const barCount = 26;
    const barWidth = Math.max(3, Math.floor((liveWaveCanvas.width / barCount) - 3));
    let x = 2;

    for (let i = 0; i < barCount; i++) {
      const idx = Math.floor((i / barCount) * (dataArray.length * 0.75));
      const magnitude = (dataArray[idx] || 0) / 255;
      const barHeight = Math.max(3, magnitude * liveWaveCanvas.height * 0.9);

      const grad = waveCtx.createLinearGradient(0, 0, 0, liveWaveCanvas.height);
      grad.addColorStop(0, "#F59E0B");
      grad.addColorStop(1, "#D97706");

      waveCtx.fillStyle = grad;
      if (waveCtx.roundRect) {
        waveCtx.beginPath();
        waveCtx.roundRect(x, (liveWaveCanvas.height - barHeight) / 2, barWidth, barHeight, 2);
        waveCtx.fill();
      } else {
        waveCtx.fillRect(x, (liveWaveCanvas.height - barHeight) / 2, barWidth, barHeight);
      }
      x += barWidth + 3;
    }

    animationFrameId = requestAnimationFrame(renderLiveWaveform);
  }

  // Send Recorded Audio to Gemini Backend
  async function processAudioInput(blob) {
    canvasPaintingOverlay.classList.remove("hidden");
    paintingStatusTitle.innerText = "Gemini is sculpting...";
    paintingStatusSubtitle.innerText = liveCapturedText ? `"${liveCapturedText}"` : "Transcribing your voice with Gemini 3.5 Transcribe";

    canvasProgressBar.style.width = "30%";
    setTimeout(() => { canvasProgressBar.style.width = "65%"; }, 250);

    const reader = new FileReader();
    reader.readAsDataURL(blob);
    reader.onloadend = async () => {
      const base64Audio = reader.result.split(",")[1];
      try {
        const res = await fetch("/api/voice_draw", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            audio_base64: base64Audio,
            mime_type: blob.type || "audio/wav",
            // Allow Gemini 3.5 Transcribe to natively detect and transcribe Hindi / 85+ languages!
            force_simulation: false,
          }),
        });
        const data = await res.json();
        applyArtResult(data);
      } catch (err) {
        console.error("Processing error:", err);
        canvasPaintingOverlay.classList.add("hidden");
        micStatusText.innerText = "Tap to Speak";
      }
    };
  }

  // Fallback: Send Transcribed Text Directly to Gemini
  async function processTextInput(text) {
    canvasPaintingOverlay.classList.remove("hidden");
    paintingStatusTitle.innerText = "Gemini is sculpting...";
    paintingStatusSubtitle.innerText = `"${text}"`;
    canvasProgressBar.style.width = "35%";
    setTimeout(() => { canvasProgressBar.style.width = "70%"; }, 250);

    try {
      const res = await fetch("/api/voice_draw", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          spoken_text_override: text,
          force_simulation: false,
        }),
      });
      const data = await res.json();
      applyArtResult(data);
    } catch (err) {
      console.error("Text submission error:", err);
      canvasPaintingOverlay.classList.add("hidden");
      micStatusText.innerText = "Tap to Speak";
    }
  }
});
