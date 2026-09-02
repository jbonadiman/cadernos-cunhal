const params = new URLSearchParams(location.search);
const bookSlug = params.get("book");

if (!bookSlug) {
  location.href = "index.html";
}

const bookTitle = document.getElementById("book-title");

const state = {
  manifest: null,
  currentPage: 1,
};

const pageImage = document.getElementById("page-image");
const pageUnavailable = document.getElementById("page-unavailable");
const pageInput = document.getElementById("page-input");
const pageCount = document.getElementById("page-count");

const transform = {
  zoom: 1,
  rotation: 0,
};

function applyTransform() {
  pageImage.style.transform = `scale(${transform.zoom}) rotate(${transform.rotation}deg)`;
}

function zoomIn() {
  transform.zoom = Math.min(transform.zoom + 0.2, 3);
  applyTransform();
}

function zoomOut() {
  transform.zoom = Math.max(transform.zoom - 0.2, 0.4);
  applyTransform();
}

function rotate() {
  transform.rotation = (transform.rotation + 90) % 360;
  applyTransform();
}

function toggleFullscreen() {
  if (document.fullscreenElement) {
    document.exitFullscreen();
  } else {
    document.getElementById("viewer").requestFullscreen();
  }
}

function renderCurrentPage() {
  const page = state.manifest.pages[state.currentPage - 1];
  pageImage.hidden = false;
  pageUnavailable.hidden = true;
  pageImage.src = `books/${bookSlug}/${page.image}`;
  pageImage.alt = `Página ${state.currentPage}`;
  pageInput.value = state.currentPage;
  pageCount.textContent = `/ ${state.manifest.page_count}`;
}

function goToPage(number) {
  transform.zoom = 1;
  transform.rotation = 0;
  applyTransform();
  const clamped = Math.min(Math.max(number, 1), state.manifest.page_count);
  state.currentPage = clamped;
  renderCurrentPage();
  renderTranscription();
}

function nextPage() {
  goToPage(state.currentPage + 1);
}

function prevPage() {
  goToPage(state.currentPage - 1);
}

const transcriptionPane = document.getElementById("transcription-pane");
const transcriptionText = document.getElementById("transcription-text");

let transcriptions = null;

fetch(`books/${bookSlug}/transcriptions.json`)
  .then((response) => response.json())
  .then((data) => {
    transcriptions = data;
    if (state.manifest) renderTranscription();
  });

function renderTranscription() {
  const text = transcriptions ? transcriptions[String(state.currentPage)] : undefined;

  if (!text) {
    transcriptionPane.hidden = true;
    transcriptionText.replaceChildren();
    return;
  }

  const paragraphs = text.split("\n").map((line) => {
    const p = document.createElement("p");
    p.textContent = line;
    return p;
  });

  transcriptionText.replaceChildren(...paragraphs);
  transcriptionPane.hidden = false;
}

document.getElementById("next-page").addEventListener("click", nextPage);
document.getElementById("prev-page").addEventListener("click", prevPage);
document.getElementById("zoom-in").addEventListener("click", zoomIn);
document.getElementById("zoom-out").addEventListener("click", zoomOut);
document.getElementById("rotate").addEventListener("click", rotate);
document.getElementById("fullscreen").addEventListener("click", toggleFullscreen);

pageInput.addEventListener("change", () => {
  goToPage(parseInt(pageInput.value, 10) || 1);
});

document.addEventListener("keydown", (event) => {
  if (document.activeElement === pageInput) return;
  if (event.key === "ArrowRight") nextPage();
  if (event.key === "ArrowLeft") prevPage();
});

pageImage.addEventListener("error", () => {
  pageImage.hidden = true;
  pageUnavailable.hidden = false;
});

fetch(`books/${bookSlug}/manifest.json`)
  .then((response) => response.json())
  .then((manifest) => {
    state.manifest = manifest;
    pageInput.max = manifest.page_count;
    document.title = `${manifest.title} — Álvaro Cunhal`;
    bookTitle.textContent = manifest.title;
    const initialPage = parseInt(params.get("page"), 10) || 1;
    goToPage(initialPage);
  });

let touchStartX = null;
let touchStartY = null;

document.getElementById("page-area").addEventListener("touchstart", (event) => {
  touchStartX = event.changedTouches[0].clientX;
  touchStartY = event.changedTouches[0].clientY;
});

document.getElementById("page-area").addEventListener("touchend", (event) => {
  if (touchStartX === null) return;
  const deltaX = event.changedTouches[0].clientX - touchStartX;
  const deltaY = event.changedTouches[0].clientY - touchStartY;
  const SWIPE_THRESHOLD = 50;
  if (Math.abs(deltaX) > Math.abs(deltaY)) {
    if (deltaX > SWIPE_THRESHOLD) prevPage();
    if (deltaX < -SWIPE_THRESHOLD) nextPage();
  }
  touchStartX = null;
  touchStartY = null;
});

const backgroundAudio = document.getElementById("background-audio");
const toggleAudioButton = document.getElementById("toggle-audio");
const audioBanner = document.getElementById("audio-banner");
const AUDIO_BANNER_DISMISSED_KEY = "cadernos-audio-banner-dismissed";

function updateAudioButtonLabel() {
  toggleAudioButton.textContent = backgroundAudio.muted ? "🔇 Música" : "🔊 Música";
}

function toggleAudio() {
  backgroundAudio.muted = !backgroundAudio.muted;
  if (!backgroundAudio.muted) {
    backgroundAudio.play().catch(() => {});
  }
  updateAudioButtonLabel();
}

toggleAudioButton.addEventListener("click", toggleAudio);
backgroundAudio.muted = true;
backgroundAudio.play().catch(() => {});
updateAudioButtonLabel();

if (localStorage.getItem(AUDIO_BANNER_DISMISSED_KEY) !== "true") {
  audioBanner.hidden = false;
}

document.getElementById("dismiss-audio-banner").addEventListener("click", () => {
  audioBanner.hidden = true;
  localStorage.setItem(AUDIO_BANNER_DISMISSED_KEY, "true");
});
