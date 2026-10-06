/**
 * Socratic Tutor - Frontend Controller
 * Connects the UI to the FastAPI Socratic Tutor backend.
 */

const API_BASE_URL = "http://127.0.0.1:8000";

// State
let currentSessionId = null;
let isProcessing = false;
let selectedImageFile = null;

// DOM Elements
const chatMessages = document.getElementById("chat-messages");
const welcomeCard = document.getElementById("welcome-card");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const resetBtn = document.getElementById("reset-btn");
const loadingIndicator = document.getElementById("loading-indicator");
const sessionBadge = document.getElementById("session-badge");
const uploadImageBtn = document.getElementById("upload-image-btn");
const imageInput = document.getElementById("image-input");
const imagePreviewArea = document.getElementById("image-preview-area");
const imagePreview = document.getElementById("image-preview");
const imagePreviewName = document.getElementById("image-preview-name");
const clearImageBtn = document.getElementById("clear-image-btn");

/**
 * Initializes listeners and setups.
 */
function init() {
  // Input auto-resize and validation
  messageInput.addEventListener("input", handleInputChange);

  // Keyboard shortcut: Enter sends (Shift+Enter for newline)
  messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const hasContent = messageInput.value.trim().length > 0 || selectedImageFile !== null;
      if (!isProcessing && hasContent) {
        chatForm.requestSubmit();
      }
    }
  });

  // Image upload handling
  if (uploadImageBtn && imageInput) {
    uploadImageBtn.addEventListener("click", () => imageInput.click());
    imageInput.addEventListener("change", handleImageSelect);
  }
  if (clearImageBtn) {
    clearImageBtn.addEventListener("click", clearSelectedImage);
  }

  // Form submission
  chatForm.addEventListener("submit", handleSubmit);

  // Reset button
  resetBtn.addEventListener("reset", handleReset);
  resetBtn.addEventListener("click", handleReset);

  // Starter example chips
  document.querySelectorAll(".starter-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const prompt = chip.getAttribute("data-prompt");
      if (prompt && !isProcessing) {
        messageInput.value = prompt;
        handleInputChange();
        chatForm.requestSubmit();
      }
    });
  });

  renderMath(document.body);
  messageInput.focus();
}

/**
 * Handles selection of an image file for multimodal math guidance.
 */
function handleImageSelect(e) {
  const file = e.target.files && e.target.files[0];
  if (!file) return;

  selectedImageFile = file;
  if (imagePreview) {
    imagePreview.src = URL.createObjectURL(file);
  }
  if (imagePreviewName) {
    imagePreviewName.textContent = file.name;
  }
  if (imagePreviewArea) {
    imagePreviewArea.classList.remove("hidden");
  }
  if (uploadImageBtn) {
    uploadImageBtn.classList.add("has-image");
  }
  handleInputChange();
  messageInput.focus();
}

/**
 * Clears the currently selected image and hides the preview.
 */
function clearSelectedImage() {
  selectedImageFile = null;
  if (imageInput) {
    imageInput.value = "";
  }
  if (imagePreview) {
    imagePreview.src = "";
  }
  if (imagePreviewArea) {
    imagePreviewArea.classList.add("hidden");
  }
  if (uploadImageBtn) {
    uploadImageBtn.classList.remove("has-image");
  }
  handleInputChange();
}

/**
 * Adjusts textarea height and toggles send button state.
 */
function handleInputChange() {
  // Resize textarea based on content
  messageInput.style.height = "auto";
  messageInput.style.height = `${Math.min(messageInput.scrollHeight, 140)}px`;

  // Enable/disable send button (enable if text OR image present)
  const hasContent = messageInput.value.trim().length > 0 || selectedImageFile !== null;
  sendBtn.disabled = !hasContent || isProcessing;
}

/**
 * Handles sending a student message to the tutor API.
 */
async function handleSubmit(e) {
  e.preventDefault();

  const message = messageInput.value.trim();
  const imageToSend = selectedImageFile;

  if ((!message && !imageToSend) || isProcessing) return;

  // 1. Hide welcome card if still visible
  if (welcomeCard && welcomeCard.parentNode) {
    welcomeCard.style.display = "none";
  }

  // 2. Render student message (with thumbnail preview if image was provided)
  const imagePreviewUrl = imageToSend ? URL.createObjectURL(imageToSend) : null;
  appendStudentMessage(message, imagePreviewUrl);

  // 3. Clear and reset input and image
  clearSelectedImage();
  messageInput.value = "";
  handleInputChange();

  // 4. Set loading state
  setLoading(true);

  try {
    let response;

    if (imageToSend) {
      // Multimodal FormData flow to /api/chat/image
      // IMPORTANT: Do NOT manually set Content-Type header so browser sets multipart boundary
      const formData = new FormData();
      formData.append("image", imageToSend);
      if (message) {
        formData.append("message", message);
      }
      if (currentSessionId) {
        formData.append("session_id", currentSessionId);
      }

      response = await fetch(`${API_BASE_URL}/api/chat/image`, {
        method: "POST",
        body: formData,
      });
    } else {
      // Existing text JSON flow to /api/chat (unchanged)
      const payload = {
        message: message,
      };
      if (currentSessionId) {
        payload.session_id = currentSessionId;
      }

      response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server returned status ${response.status}`);
    }

    const data = await response.json();

    // 5. Update session ID and badge
    if (data.session_id) {
      currentSessionId = data.session_id;
      sessionBadge.textContent = "Session Active";
      sessionBadge.style.color = "#a5b4fc";
      sessionBadge.style.borderColor = "rgba(99, 102, 241, 0.4)";
    }

    // 6. Render tutor response with insight and status
    appendTutorMessage(data.response, data.misconception, data.status);

  } catch (error) {
    console.error("Chat error:", error);
    appendErrorMessage(
      `Could not reach tutor: ${error.message}. Please make sure the FastAPI backend is running at ${API_BASE_URL}.`
    );
  } finally {
    setLoading(false);
    messageInput.focus();
  }
}

/**
 * Renders the student's message bubble.
 */
function appendStudentMessage(text, imageUrl = null) {
  const row = document.createElement("div");
  row.className = "message-row student";

  const content = document.createElement("div");
  content.className = "message-content";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  if (imageUrl) {
    const img = document.createElement("img");
    img.src = imageUrl;
    img.alt = "Uploaded math problem";
    img.className = "message-bubble-image";
    bubble.appendChild(img);
  }

  if (text) {
    const textSpan = document.createElement("span");
    textSpan.textContent = text;
    bubble.appendChild(textSpan);
  }

  content.appendChild(bubble);
  row.appendChild(content);

  // Render LaTeX math if present in student message
  renderMath(bubble);

  chatMessages.appendChild(row);
  scrollToBottom();
}

/**
 * Renders the tutor's response, misconception insight, and status badge.
 */
function appendTutorMessage(response, misconception, status) {
  const row = document.createElement("div");
  row.className = "message-row tutor";

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = "📐";

  const content = document.createElement("div");
  content.className = "message-content";

  // Tutor main response bubble
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = response;
  content.appendChild(bubble);

  // Subtle learning insight (misconception diagnostic)
  if (misconception && misconception.toLowerCase() !== "none") {
    const insightCard = document.createElement("div");
    insightCard.className = "insight-card";
    insightCard.innerHTML = `
      <span class="insight-icon">💡</span>
      <div class="insight-text">
        <strong>Learning Insight:</strong> ${escapeHtml(misconception)}
      </div>
    `;
    content.appendChild(insightCard);
  }

  // Celebratory status badge if problem was resolved
  if (status && status.toUpperCase() === "RESOLVED") {
    const resolvedCard = document.createElement("div");
    resolvedCard.className = "resolved-card";
    resolvedCard.innerHTML = `
      <span>🎉</span>
      <span>Problem Resolved! Great job thinking through the steps!</span>
    `;
    content.appendChild(resolvedCard);
  }

  row.appendChild(avatar);
  row.appendChild(content);

  // Render LaTeX math inside tutor response bubble and learning insight
  renderMath(content);

  chatMessages.appendChild(row);
  scrollToBottom();
}

/**
 * Renders an error message bubble.
 */
function appendErrorMessage(text) {
  const row = document.createElement("div");
  row.className = "message-row tutor";

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = "⚠️";

  const content = document.createElement("div");
  content.className = "message-content";

  const bubble = document.createElement("div");
  bubble.className = "bubble error-bubble";
  bubble.textContent = text;

  content.appendChild(bubble);
  row.appendChild(avatar);
  row.appendChild(content);

  chatMessages.appendChild(row);
  scrollToBottom();
}

/**
 * Resets the session on the backend and clears the UI.
 */
async function handleReset() {
  if (isProcessing) return;

  try {
    resetBtn.disabled = true;
    resetBtn.textContent = "Resetting...";

    if (currentSessionId) {
      await fetch(`${API_BASE_URL}/api/reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: currentSessionId }),
      }).catch((err) => console.warn("Reset backend warning:", err));
    }

    // Reset state
    currentSessionId = null;
    sessionBadge.textContent = "Session Ready";
    sessionBadge.style.color = "";
    sessionBadge.style.borderColor = "";

    // Clear chat area and restore welcome card
    chatMessages.innerHTML = "";
    if (welcomeCard) {
      welcomeCard.style.display = "block";
      chatMessages.appendChild(welcomeCard);
    }

    clearSelectedImage();
    messageInput.value = "";
    handleInputChange();
    messageInput.focus();

  } catch (error) {
    console.error("Reset error:", error);
  } finally {
    resetBtn.disabled = false;
    resetBtn.innerHTML = `
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
        <path d="M21 3v5h-5" />
        <path d="M21 12a9 9 0 0 1-15 6.7L3 16" />
        <path d="M3 21v-5h5" />
      </svg>
      <span>New Session</span>
    `;
  }
}

/**
 * Toggles the loading indicator and input state.
 */
function setLoading(loading) {
  isProcessing = loading;
  if (loading) {
    loadingIndicator.classList.remove("hidden");
    sendBtn.disabled = true;
    scrollToBottom();
  } else {
    loadingIndicator.classList.add("hidden");
    handleInputChange();
  }
}

/**
 * Auto-scrolls the chat window to the newest message.
 */
function scrollToBottom() {
  requestAnimationFrame(() => {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });
}

/**
 * Renders LaTeX math notation in the specified DOM element using KaTeX auto-render.
 * Supports both display math ($$...$$, \[...\]) and inline math ($...$, \(...\)).
 */
function renderMath(element) {
  if (!element) return;
  if (typeof renderMathInElement === "function") {
    try {
      renderMathInElement(element, {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false },
          { left: "\\(", right: "\\)", display: false },
          { left: "\\[", right: "\\]", display: true },
        ],
        throwOnError: false,
      });
    } catch (err) {
      console.warn("KaTeX render notice:", err);
    }
  }
}

/**
 * Escapes HTML characters to prevent XSS.
 */
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// Start on DOM ready
document.addEventListener("DOMContentLoaded", init);
