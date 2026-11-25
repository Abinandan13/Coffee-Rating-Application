/**
 * Coffee Rating Application - Frontend Script
 * Module 3: Database & Backend API Integration
 * 
 * Features:
 * - Fetches real-time coffee catalogue and vote counts from SQLite via GET /api/coffees.
 * - Submits live votes to POST /api/coffees/{coffee_id}/vote with atomic database increments.
 * - Disables vote button during request processing to prevent duplicate clicks.
 * - Displays interactive toast feedback, error alerts, and loading states.
 * - Robust event listener initialization with DOM element validation.
 * - Preserves all original coffee designs, image fallbacks, and responsiveness.
 */

// ==============================================================================
// 1. CONFIGURATION & ENVIRONMENT DETECTION
// ==============================================================================

/**
 * Automatically detects whether the frontend is served from the FastAPI backend
 * or from a separate origin (such as a local dev server, file://, or port 3000/5500).
 * 
 * When running via file:// or another port, it directs all REST API requests
 * directly to the FastAPI Uvicorn server running at http://127.0.0.1:8000.
 */
const API_BASE_URL = (
  window.location.protocol === "http:" || 
  window.location.protocol === "https:"
) && window.location.port === "8000"
  ? ""
  : "http://127.0.0.1:8000";

/**
 * Standard configuration object for client-side API requests.
 * Includes timeout durations and default HTTP headers for JSON payloads.
 * 
 * @property {number} timeoutMs - Max wait time before timing out API calls
 * @property {Object} headers - Default HTTP request headers
 */
const API_CONFIG = {
  timeoutMs: 8000,
  headers: {
    "Accept": "application/json",
    "Content-Type": "application/json"
  }
};

/**
 * In-memory reference of currently rendered coffees.
 * Kept in sync with live SQLite database responses.
 * 
 * @type {Array<Object>}
 */
let currentCoffees = [];

// ==============================================================================
// 2. SVG IMAGE FALLBACK GENERATOR
// ==============================================================================

/**
 * Generates an embedded, vector-based SVG placeholder image as a data URI.
 * Guarantees crisp visual presentation if external images fail to load or
 * when running offline without internet access.
 * 
 * The placeholder features a warm, rich gradient background matching
 * the coffee theme with a central emblem and coffee title.
 * 
 * @param {string} coffeeName - Name of the coffee to render on placeholder
 * @returns {string} Data URI with inline SVG graphic
 */
function getSvgFallback(coffeeName) {
  const safeName = coffeeName ? String(coffeeName).replace(/[<>&"]/g, '') : 'Coffee';
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
      <defs>
        <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#4a2c1d" />
          <stop offset="100%" stop-color="#23160e" />
        </linearGradient>
      </defs>
      <rect width="600" height="400" fill="url(#grad)" />
      <circle cx="300" cy="180" r="90" fill="#eedfcf" opacity="0.15" />
      <text x="300" y="195" font-size="70" text-anchor="middle" fill="#d88a4c">☕</text>
      <text x="300" y="270" font-family="Georgia, serif" font-size="28" font-weight="bold" text-anchor="middle" fill="#faf6f0">${safeName}</text>
    </svg>
  `;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

// ==============================================================================
// 3. TOAST & NOTIFICATION SYSTEM
// ==============================================================================

/**
 * Retrieves or lazily creates the floating toast notifications container.
 * Accessible to screen readers via aria-live="polite".
 * Ensures the container element exists in the DOM before toasts are appended.
 * 
 * @returns {HTMLElement} The toast container DOM element
 */
function getOrCreateToastContainer() {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    container.setAttribute("aria-live", "polite");
    document.body.appendChild(container);
  }
  return container;
}

/**
 * Displays a subtle, animated toast notification in the bottom right corner.
 * Automatically clears after 3.2 seconds.
 * 
 * Provides immediate visual and audible feedback to users when votes are
 * successfully persisted in the backend database or when an error occurs.
 * 
 * @param {string} message - Feedback message to display to the user
 * @param {boolean} isError - Whether the message represents an error state
 */
function showToast(message, isError = false) {
  const container = getOrCreateToastContainer();
  const toast = document.createElement("div");
  toast.className = `toast ${isError ? "toast-error" : ""}`;
  toast.innerHTML = `
    <span class="toast-icon">${isError ? "⚠️" : "✓"}</span>
    <span class="toast-text">${message}</span>
  `;

  container.appendChild(toast);

  // Trigger smooth enter animation via CSS class
  requestAnimationFrame(() => {
    toast.classList.add("toast-visible");
  });

  // Auto remove after display duration
  setTimeout(() => {
    toast.classList.remove("toast-visible");
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }, 3200);
}

// ==============================================================================
// 4. CARD RENDERING & DOM LOGIC
// ==============================================================================

/**
 * Creates and returns the DOM element for a single coffee card.
 * Includes coffee image, name, description, live vote count badge, and Vote button.
 * 
 * The card layout follows modern semantic HTML5 conventions with accessible
 * ARIA roles and labels for screen readers.
 * 
 * @param {Object} coffee - Coffee item data object from SQLite
 * @returns {HTMLElement} The constructed coffee card element
 */
function createCoffeeCardElement(coffee) {
  const card = document.createElement("article");
  card.className = "coffee-card";
  card.dataset.id = coffee.id;

  const imageUrl = coffee.image_url || coffee.image;
  const voteCount = Number(coffee.votes);

  card.innerHTML = `
    <div class="card-image-wrap">
      <img 
        src="${imageUrl}" 
        alt="${coffee.name} coffee" 
        class="card-image" 
        loading="lazy"
        onerror="this.onerror=null; this.src=getSvgFallback('${coffee.name}');"
      >
    </div>
    <div class="card-content">
      <h2 class="card-title">${coffee.name}</h2>
      <p class="card-description">${coffee.description}</p>
      <div class="card-actions">
        <div class="vote-display" aria-label="${voteCount} ${voteCount === 1 ? 'vote' : 'votes'}">
          <span class="vote-icon" aria-hidden="true">★</span>
          <span class="vote-number" id="vote-count-${coffee.id}">${voteCount}</span>
          <span class="vote-label">${voteCount === 1 ? 'vote' : 'votes'}</span>
        </div>
        <button 
          type="button" 
          class="btn-vote" 
          id="btn-vote-${coffee.id}" 
          data-coffee-id="${coffee.id}"
          aria-label="Vote for ${coffee.name}"
        >
          <span class="btn-icon" aria-hidden="true">👍</span>
          <span class="btn-text">Vote</span>
        </button>
      </div>
    </div>
  `;

  return card;
}

/**
 * Renders all coffee cards into the designated grid container.
 * Safely resolves the grid container by ID or fallback selector.
 * 
 * Performs cleanup of any previous content or loading skeletons
 * before appending freshly rendered card components.
 * 
 * @param {Array} coffees - Array of coffee data objects
 */
function renderCoffeeCards(coffees) {
  const gridContainer = document.getElementById("coffee-grid") || document.getElementById("coffee-container");
  if (!gridContainer) {
    console.error("Coffee grid container (#coffee-grid) not found in DOM.");
    return;
  }

  // Clear existing items and loading indicators
  gridContainer.innerHTML = "";

  coffees.forEach(coffee => {
    const cardElement = createCoffeeCardElement(coffee);
    gridContainer.appendChild(cardElement);
  });
}

/**
 * Updates the displayed vote count for a specific coffee card with animation.
 * Adjusts singular vs. plural labels and updates accessibility attributes.
 * 
 * Uses a CSS keyframe bump pulse to provide tactile visual confirmation
 * that the vote increment succeeded.
 * 
 * @param {string} coffeeId - ID of the coffee card
 * @param {number} newCount - Updated vote count received from SQLite database
 */
function updateVoteDisplay(coffeeId, newCount) {
  const countElement = document.getElementById(`vote-count-${coffeeId}`);
  if (!countElement) return;

  // Update numeric text
  countElement.textContent = newCount;

  // Update singular/plural text and aria-label
  const card = countElement.closest(".coffee-card");
  if (card) {
    const labelElement = card.querySelector(".vote-label");
    if (labelElement) {
      labelElement.textContent = newCount === 1 ? "vote" : "votes";
    }
    const displayElement = card.querySelector(".vote-display");
    if (displayElement) {
      displayElement.setAttribute("aria-label", `${newCount} ${newCount === 1 ? 'vote' : 'votes'}`);
    }
  }

  // Trigger interactive bump pulse animation
  countElement.classList.remove("vote-bump");
  void countElement.offsetWidth; // Force reflow
  countElement.classList.add("vote-bump");
}

// ==============================================================================
// 5. BACKEND API INTEGRATION (Module 3)
// ==============================================================================

/**
 * Fetches all coffee items and their latest database vote counts from the backend API.
 * Updates the DOM with real-time SQLite database values.
 * 
 * Handles network or API failures by displaying an informative retry banner
 * without ever replacing real counts with fake zero fallback data.
 * 
 * @returns {Promise<void>}
 */
async function fetchCoffees() {
  const gridContainer = document.getElementById("coffee-grid") || document.getElementById("coffee-container");
  const refreshButton = document.getElementById("refresh-btn");

  if (refreshButton) {
    refreshButton.disabled = true;
    refreshButton.setAttribute("aria-busy", "true");
  }

  if (gridContainer && currentCoffees.length === 0) {
    gridContainer.innerHTML = `
      <div class="loading-indicator">
        <p>Loading artisan coffee collection from database...</p>
      </div>
    `;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeoutMs);

  try {
    const response = await fetch(`${API_BASE_URL}/api/coffees`, {
      method: "GET",
      headers: { "Accept": "application/json" },
      cache: "no-store",
      signal: controller.signal
    });

    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }

    const coffees = await response.json();
    if (!validateCoffeeCollection(coffees)) {
      throw new Error("Invalid coffee data received from backend API.");
    }

    currentCoffees = coffees;
    renderCoffeeCards(coffees);
  } catch (error) {
    console.error("Unable to fetch coffees from backend API:", error);
    const errorMessage = error.name === "AbortError"
      ? "Request timed out while connecting to backend server."
      : error.message;

    if (gridContainer) {
      if (currentCoffees.length === 0) {
        gridContainer.innerHTML = "";
      } else {
        const existingBanner = gridContainer.querySelector(".error-banner");
        if (existingBanner) {
          existingBanner.remove();
        }
      }

      const banner = document.createElement("div");
      banner.className = "error-banner";
      banner.innerHTML = `
        <p><strong>Unable to load live coffee votes:</strong> Could not fetch data from <code>${API_BASE_URL}/api/coffees</code> (${errorMessage}).</p>
        <p style="font-size: 0.85rem; margin-top: 0.4rem;">Make sure the FastAPI backend is running with <code>uvicorn main:app --reload --port 8000</code>.</p>
        <button type="button" class="btn-retry" id="retry-btn">Retry Connection</button>
      `;
      gridContainer.prepend(banner);

      const retryBtn = document.getElementById("retry-btn");
      if (retryBtn) {
        retryBtn.addEventListener("click", () => fetchCoffees());
      }
    }

    showToast(`Could not load coffees: ${errorMessage}`, true);
  } finally {
    clearTimeout(timeoutId);
    if (refreshButton) {
      refreshButton.disabled = false;
      refreshButton.removeAttribute("aria-busy");
    }
  }
}

/**
 * Handles the voting action:
 * - Prevents duplicate clicks while in-flight.
 * - Submits POST /api/coffees/{coffee_id}/vote to backend SQLite DB.
 * - Updates DOM count with atomic response from database.
 * - Shows feedback toast.
 * 
 * @param {string} coffeeId - ID of the coffee being voted for
 * @returns {Promise<void>}
 */
async function handleVoteClick(coffeeId) {
  const voteBtn = document.getElementById(`btn-vote-${coffeeId}`);
  if (!voteBtn || voteBtn.disabled) {
    return; // Prevent duplicate clicks while request is processing
  }

  const btnIcon = voteBtn.querySelector(".btn-icon");
  const btnText = voteBtn.querySelector(".btn-text");
  const originalText = btnText ? btnText.textContent : "Vote";

  // Set loading state & disable button to prevent concurrent duplicate submissions
  voteBtn.disabled = true;
  voteBtn.setAttribute("aria-busy", "true");
  if (btnText) btnText.textContent = "Voting...";

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeoutMs);

  try {
    const response = await fetch(`${API_BASE_URL}/api/coffees/${encodeURIComponent(coffeeId)}/vote`, {
      method: "POST",
      headers: { "Accept": "application/json" },
      cache: "no-store",
      signal: controller.signal
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server returned HTTP ${response.status}`);
    }

    const updatedCoffee = await response.json();
    if (!updatedCoffee || typeof updatedCoffee.votes !== "number" || !Number.isFinite(updatedCoffee.votes)) {
      throw new Error("Invalid vote response received from backend API.");
    }

    const targetId = updatedCoffee.id || coffeeId;

    // Update local in-memory reference
    const found = currentCoffees.find(c => c.id === targetId);
    if (found) found.votes = updatedCoffee.votes;

    // Update DOM display with actual database count
    updateVoteDisplay(targetId, updatedCoffee.votes);
    showToast(`Vote recorded for ${updatedCoffee.name}! Total: ${updatedCoffee.votes}`);
  } catch (error) {
    console.error("Voting request failed:", error);
    const errorMessage = error.name === "AbortError"
      ? "Request timed out while recording vote."
      : error.message;
    showToast(`Could not record vote: ${errorMessage}`, true);
  } finally {
    clearTimeout(timeoutId);
    // Restore button state
    voteBtn.disabled = false;
    voteBtn.removeAttribute("aria-busy");
    if (btnText) btnText.textContent = originalText;
  }
}

/**
 * Helper to ensure the active vote button state is cleanly toggled.
 * 
 * @param {string} coffeeId - The ID of the targeted coffee
 * @param {boolean} isBusy - Whether a vote transaction is currently active
 */
function setButtonVotingState(coffeeId, isBusy) {
  const btn = document.getElementById(`btn-vote-${coffeeId}`);
  if (!btn) return;
  btn.disabled = isBusy;
  if (isBusy) {
    btn.setAttribute("aria-busy", "true");
  } else {
    btn.removeAttribute("aria-busy");
  }
}

/**
 * Validates coffee catalogue payloads to ensure schema integrity before rendering.
 * 
 * @param {Array} items - List of coffee objects to inspect
 * @returns {boolean} True if all items conform to expected schema
 */
function validateCoffeeCollection(items) {
  if (!Array.isArray(items)) return false;
  return items.every(
    item => item && item.id && item.name && typeof item.votes === "number" && Number.isFinite(item.votes)
  );
}

// ==============================================================================
// 6. EVENT LISTENERS INITIALIZATION
// ==============================================================================

/**
 * Initializes all primary DOM event listeners for the application.
 * Properly checks and resolves element references to prevent null addEventListener errors.
 * 
 * Specifically connects:
 * 1. The header refresh button (#refresh-btn) for reloading coffee data from SQLite.
 * 2. The main coffee cards container (#coffee-grid) for delegated click handling.
 * 
 * Mismatch Fix Details:
 * - In index.html, the Refresh button has ID 'refresh-btn' and the cards grid has ID 'coffee-grid'.
 * - Verifies that elements exist before calling addEventListener, preventing TypeError: Cannot read
 *   properties of null (reading 'addEventListener').
 * - Inspect around lines 480-510: line 495 is executed directly inside this function.
 */
function initEventListeners() {
  // Locate the header Refresh button by its explicit ID in index.html
  const refreshButton = document.getElementById("refresh-btn");
  if (refreshButton) {
    refreshButton.addEventListener("click", () => {
      fetchCoffees();
    });
  }

  // Locate the primary coffee grid container by ID or fallback container ID
  const coffeeGridContainer = (
    document.getElementById("coffee-grid") || 
    document.getElementById("coffee-container")
  );
  if (coffeeGridContainer) {
    coffeeGridContainer.addEventListener("click", (event) => {
      const voteButton = event.target.closest(".btn-vote");
      if (voteButton && voteButton.dataset.coffeeId) {
        handleVoteClick(voteButton.dataset.coffeeId);
      }
    });
  }
}

// ==============================================================================
// 7. APPLICATION BOOTSTRAP
// ==============================================================================

/**
 * Main application bootstrap function executed on DOMContentLoaded.
 * Ensures event listeners are initialized and initial data is fetched from SQLite.
 */
function initApp() {
  initEventListeners();
  fetchCoffees();
}

// Listen for DOM ready event to start the application
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initApp);
} else {
  // DOM is already ready (e.g. if loaded asynchronously or deferred)
  initApp();
}
