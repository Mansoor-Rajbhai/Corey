document.addEventListener("DOMContentLoaded", () => {
  // --- Theme Toggle Logic ---
  const themeToggleBtn = document.getElementById("theme-toggle");
  const themeIcon = document.getElementById("theme-icon");
  const htmlElement = document.documentElement;

  const savedTheme = localStorage.getItem("theme");
  const systemPrefersDark = window.matchMedia(
    "(prefers-color-scheme: dark)",
  ).matches;

  if (savedTheme === "dark" || (!savedTheme && systemPrefersDark)) {
    htmlElement.classList.add("dark");
    themeIcon.src = "../icons/moon.svg";
  } else {
    htmlElement.classList.remove("dark");
    themeIcon.src = "../icons/sun.svg";
  }

  themeToggleBtn.addEventListener("click", () => {
    if (htmlElement.classList.contains("dark")) {
      htmlElement.classList.remove("dark");
      themeIcon.src = "../icons/sun.svg";
      localStorage.setItem("theme", "light");
    } else {
      htmlElement.classList.add("dark");
      themeIcon.src = "../icons/moon.svg";
      localStorage.setItem("theme", "dark");
    }
  });

  // --- Futuristic Glowing Audio Visualizer (Enlarged Physical Profile) ---
  const micShortcutBtn = document.getElementById("mic-shortcut");
  const statusText = document.getElementById("status-text");
  const canvas = document.getElementById("visualizer-canvas");
  const ctx = canvas.getContext("2d");

  let audioCtx = null;
  let analyser = null;
  let biquadFilter = null;
  let source = null;
  let stream = null;
  let animationId = null;
  let isListening = false;

  // --- DECIBEL & WAVE CONFIGURATION ---
  const DB_THRESHOLD = 84; // ONLY trigger visualization above 84 dB
  const FFT_SIZE = 256;
  const SMOOTHING_FACTOR = 0.08;
  const EXPANSION_SMOOTHING = 0.12;

  const numBars = 28;
  const smoothHeights = new Array(numBars).fill(0);
  let idleTime = 0;

  // Dynamic tracking of the circle's expanded state
  let dynamicBaseRadiusScale = 1.0;

  // Handle high DPI displays for crisp rendering & seamless responsiveness
  function resizeCanvas() {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    const sideLength = Math.min(rect.width, rect.height || rect.width);

    canvas.style.width = `${sideLength}px`;
    canvas.style.height = `${sideLength}px`;

    canvas.width = sideLength * dpr;
    canvas.height = sideLength * dpr;
    ctx.scale(dpr, dpr);
  }

  resizeCanvas();
  window.addEventListener("resize", resizeCanvas);

  async function startListening() {
    if (isListening) return;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: false,
      });

      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = FFT_SIZE;

      biquadFilter = audioCtx.createBiquadFilter();
      biquadFilter.type = "highpass";
      biquadFilter.frequency.value = 130;

      source = audioCtx.createMediaStreamSource(stream);
      source.connect(biquadFilter);
      biquadFilter.connect(analyser);

      isListening = true;
      statusText.textContent = "Listening";
      statusText.classList.remove("opacity-40");
      statusText.classList.add("opacity-100");
    } catch (err) {
      console.warn("Microphone access pending user gesture.", err);
      statusText.textContent = "Click to activate mic";
    }
  }

  // --- Main render loops (Runs constantly at 60 FPS) ---
  const dataArray = new Uint8Array(FFT_SIZE / 2);

  function draw() {
    animationId = requestAnimationFrame(draw);

    const dpr = window.devicePixelRatio || 1;
    const width = canvas.width / dpr;
    const height = canvas.height / dpr;
    const centerX = width / 2;
    const centerY = height / 2;

    // ENLARGED BASE RADIUS: Boosted baseline to 0.38 to maximize the idle ring profile
    const baselineRadius = Math.min(width, height) * 0.38;

    ctx.clearRect(0, 0, width, height);

    let currentDB = 0;
    let hasActiveSpeech = false;
    let dbExcessRatio = 0;

    if (isListening && analyser) {
      analyser.getByteFrequencyData(dataArray);

      let sumSquares = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const amplitude = dataArray[i] / 255;
        sumSquares += amplitude * amplitude;
      }
      const rms = Math.sqrt(sumSquares / dataArray.length);
      currentDB = rms > 0 ? Math.round(20 * Math.log10(rms) + 100) : 0;

      hasActiveSpeech = currentDB >= DB_THRESHOLD;
      statusText.textContent = `Listening | ${currentDB} dB`;

      if (hasActiveSpeech) {
        // Calculate scale of intensity above 84 dB (capped at 100 max dB SPL)
        dbExcessRatio = Math.min(
          1.0,
          (currentDB - DB_THRESHOLD) / (100 - DB_THRESHOLD),
        );
      }
    } else {
      statusText.textContent = "Click to activate mic";
    }

    // --- EXPANSION PHYSICS ---
    // Target scale stretches up to 1.45x wider on dynamic loud inputs
    const targetScale = 1.0 + dbExcessRatio * 0.45;
    dynamicBaseRadiusScale +=
      (targetScale - dynamicBaseRadiusScale) * EXPANSION_SMOOTHING;

    // Calculate actual frame boundary
    const baseRadius = baselineRadius * dynamicBaseRadiusScale;

    // Render symmetric radial spectrum
    for (let i = 0; i < numBars; i++) {
      let targetHeight = 0;

      if (hasActiveSpeech) {
        const binIndex = Math.floor(
          Math.abs(i - numBars / 2) * (dataArray.length / (numBars / 2)),
        );
        const rawValue = dataArray[binIndex] || 0;

        // Capped responsive bars (0.10) to make sure they don't clip the outer viewport on wide scaling
        targetHeight = (rawValue / 255) * (baseRadius * 0.1);
      } else {
        // Smooth buffering wave animation
        idleTime += 0.0006;

        const angleOffset = (i / numBars) * Math.PI * 2;
        const waveSpeed = idleTime * 50;

        const rollingWave = Math.sin(waveSpeed - angleOffset * 2.5) * 0.5 + 0.5;
        const gentleBreathing = Math.sin(idleTime * 15) * 0.3 + 0.7;

        targetHeight = 1 + rollingWave * gentleBreathing * (baseRadius * 0.04);
      }

      // Apply linear interpolation (easing)
      smoothHeights[i] += (targetHeight - smoothHeights[i]) * SMOOTHING_FACTOR;

      const angle = (i / numBars) * Math.PI * 2;
      const cos = Math.cos(angle);
      const sin = Math.sin(angle);

      // Establish bar coordinates
      const innerX = centerX + cos * baseRadius;
      const innerY = centerY + sin * baseRadius;
      const outerX = centerX + cos * (baseRadius + smoothHeights[i]);
      const outerY = centerY + sin * (baseRadius + smoothHeights[i]);

      ctx.beginPath();
      ctx.moveTo(innerX, innerY);
      ctx.lineTo(outerX, outerY);

      const isDark = document.documentElement.classList.contains("dark");

      // Glowing gradient tracking the enlarged ring scale
      const gradient = ctx.createRadialGradient(
        centerX,
        centerY,
        baseRadius,
        centerX,
        centerY,
        baseRadius + baseRadius * 0.15,
      );
      gradient.addColorStop(0, "#06b6d4");
      gradient.addColorStop(0.5, "#3b82f6");
      gradient.addColorStop(1, "#a855f7");

      ctx.strokeStyle = gradient;
      ctx.lineWidth = Math.max(1.8, baseRadius * 0.025);
      ctx.lineCap = "round";

      // Glow intensity is magnified on wide shockwaves
      ctx.shadowBlur = isDark ? 8 + dbExcessRatio * 10 : 3 + dbExcessRatio * 5;
      ctx.shadowColor = "rgba(6, 182, 212, 0.45)";

      ctx.stroke();
    }
  }

  // Begin looping instantly
  draw();

  function stopListening() {
    isListening = false;
    if (stream) stream.getTracks().forEach((track) => track.stop());
    if (audioCtx) audioCtx.close();

    statusText.textContent = "Mic Standby";
    statusText.classList.add("opacity-40");
  }

  const initOnFirstClick = () => {
    startListening();
    document.removeEventListener("click", initOnFirstClick);
  };
  document.addEventListener("click", initOnFirstClick);

  micShortcutBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  });
});
