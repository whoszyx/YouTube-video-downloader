(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  const REQUIRED_IDS = [
    "urlInput", "fetchBtn", "error", "errorText",
    "videoCard", "thumbnail", "duration", "videoTitle", "videoUploader",
    "optionsCard", "downloadBtn",
    "progressCard", "progressFill", "progressPct", "progressText", "progressMeta", "downloadLink",
  ];

  let lastInfo = null;
  let pollTimer = null;

  function requireEls(ids) {
    const missing = ids.filter((id) => !document.getElementById(id));
    if (missing.length) {
      console.error("[random.exe] missing DOM elements:", missing);
      return false;
    }
    return true;
  }

  function showError(msg) {
    $("errorText").textContent = msg;
    $("error").classList.remove("hidden");
  }

  function clearError() {
    $("error").classList.add("hidden");
    $("errorText").textContent = "";
  }

  function fmtDuration(seconds) {
    if (!seconds && seconds !== 0) return "";
    const s = Math.floor(seconds % 60);
    const m = Math.floor((seconds / 60) % 60);
    const h = Math.floor(seconds / 3600);
    const pad = (n) => String(n).padStart(2, "0");
    return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`;
  }

  async function fetchInfo() {
    clearError();
    const url = $("urlInput").value.trim();
    if (!url) {
      showError("Paste a URL first.");
      return;
    }

    $("fetchBtn").disabled = true;
    $("fetchBtn").textContent = "…";
    $("videoCard").classList.add("hidden");
    $("optionsCard").classList.add("hidden");
    $("progressCard").classList.add("hidden");

    try {
      const res = await fetch("/api/info", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (!res.ok || data.error) {
        showError(data.error || "Failed to fetch video info.");
        return;
      }
      lastInfo = data;
      renderInfo(data);
    } catch (e) {
      showError("Network error: " + e.message);
    } finally {
      $("fetchBtn").disabled = false;
      $("fetchBtn").textContent = "fetch";
    }
  }

  function renderInfo(info) {
    $("thumbnail").src = info.thumbnail || "";
    $("duration").textContent = fmtDuration(info.duration);
    $("videoTitle").textContent = info.title || "untitled";
    $("videoUploader").textContent = info.uploader || "unknown channel";

    $("videoCard").classList.remove("hidden");
    $("optionsCard").classList.remove("hidden");
  }

  async function startDownload() {
    clearError();
    if (!lastInfo) {
      showError("Fetch video info first.");
      return;
    }
    const url = $("urlInput").value.trim();
    if (!url) {
      showError("Paste a URL first.");
      return;
    }

    $("downloadBtn").disabled = true;
    $("downloadLink").classList.add("hidden");
    $("progressCard").classList.remove("hidden");
    $("progressFill").style.width = "0%";
    $("progressPct").textContent = "0%";
    $("progressText").textContent = "queuing…";
    $("progressMeta").textContent = "";

    try {
      const res = await fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (!res.ok || data.error) {
        $("downloadBtn").disabled = false;
        showError(data.error || "Failed to start download.");
        return;
      }
      pollStatus(data.job_id);
    } catch (e) {
      $("downloadBtn").disabled = false;
      showError("Network error: " + e.message);
    }
  }

  function pollStatus(jobId) {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(async () => {
      try {
        const res = await fetch(`/api/status/${jobId}`);
        const data = await res.json();
        if (!res.ok) {
          clearInterval(pollTimer);
          pollTimer = null;
          $("downloadBtn").disabled = false;
          showError(data.error || "Status check failed.");
          return;
        }
        updateProgress(data);
        if (data.status === "ready") {
          clearInterval(pollTimer);
          pollTimer = null;
          $("downloadBtn").disabled = false;
          const link = $("downloadLink");
          link.href = `/api/file/${jobId}`;
          link.setAttribute("download", data.download_name || "download");
          link.classList.remove("hidden");
          $("progressText").textContent = "complete";
          $("progressMeta").textContent = data.download_name || "";
        } else if (data.status === "error") {
          clearInterval(pollTimer);
          pollTimer = null;
          $("downloadBtn").disabled = false;
          $("progressText").textContent = "failed";
          $("progressMeta").textContent = data.error || "Unknown error.";
        }
      } catch (e) {
        clearInterval(pollTimer);
        pollTimer = null;
        $("downloadBtn").disabled = false;
        showError("Polling error: " + e.message);
      }
    }, 500);
  }

  function updateProgress(data) {
    const p = Math.max(0, Math.min(100, data.progress || 0));
    $("progressFill").style.width = p + "%";
    $("progressPct").textContent = Math.round(p) + "%";
    if (data.status === "downloading") {
      $("progressText").textContent = "downloading…";
    } else if (data.status === "processing") {
      $("progressText").textContent = "merging…";
    } else if (data.status === "starting") {
      $("progressText").textContent = "initializing…";
    }
  }

  function init() {
    if (!requireEls(REQUIRED_IDS)) return;

    $("fetchBtn").addEventListener("click", fetchInfo);
    $("urlInput").addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        fetchInfo();
      }
    });
    $("downloadBtn").addEventListener("click", startDownload);

    window.addEventListener("beforeunload", () => {
      if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", init);
})();