const list = document.getElementById("browseList");
const moreBtn = document.getElementById("browseMore");
const sortSelect = document.getElementById("browseSort");
const notificationDots = document.querySelectorAll(".notif-dot");
const randomBtn = document.getElementById("browseRandom");
const searchInput = document.getElementById("browseSearch");

let page = 1;
let loading = false;
let hasMore = true;
let currentSort = sortSelect ? sortSelect.value : "name";
let currentQuery = "";
let searchTimer = null;

function setLoading(state) {
  loading = state;
  if (moreBtn) {
    moreBtn.disabled = state;
    moreBtn.textContent = state ? "Loading..." : "Load More";
  }
}

function appendCard(item) {
  const link = document.createElement("a");
  link.className = "browse-card";
  link.href = `/${encodeURIComponent(item.slug || item.filename.replace(/\.pdf$/i, ""))}`;
  const name = document.createElement("span");
  name.textContent = item.filename;
  const meta = document.createElement("div");
  meta.className = "browse-meta";
  const voteWrap = document.createElement("span");
  voteWrap.className = "browse-meta-item";
  const voteIcon = document.createElement("img");
  voteIcon.src = "/static/epstein_ui/icons/thumbs-up.svg";
  voteIcon.alt = "";
  const voteCount = document.createElement("span");
  voteCount.textContent = item.upvotes ?? 0;
  voteWrap.appendChild(voteIcon);
  voteWrap.appendChild(voteCount);

  const annWrap = document.createElement("span");
  annWrap.className = "browse-meta-item";
  const annIcon = document.createElement("img");
  annIcon.src = "/static/epstein_ui/icons/pencil.svg";
  annIcon.alt = "";
  const annCount = document.createElement("span");
  annCount.textContent = item.annotations ?? 0;
  annWrap.appendChild(annIcon);
  annWrap.appendChild(annCount);

  meta.appendChild(voteWrap);
  meta.appendChild(annWrap);
  link.appendChild(name);
  link.appendChild(meta);
  list.appendChild(link);
}

async function loadPage() {
  if (loading || !hasMore) return;
  setLoading(true);
  try {
    const response = await fetch(
      `/browse-list/?page=${page}&sort=${encodeURIComponent(currentSort)}&q=${encodeURIComponent(currentQuery)}`
    );
    if (!response.ok) {
      throw new Error("Failed to load");
    }
    const data = await response.json();
    (data.items || []).forEach(appendCard);
    hasMore = Boolean(data.has_more);
    page += 1;
    if (!hasMore && moreBtn) {
      moreBtn.classList.add("hidden");
    }
  } catch (err) {
    console.error(err);
  } finally {
    setLoading(false);
  }
}

if (moreBtn) {
  moreBtn.addEventListener("click", loadPage);
}

if (sortSelect) {
  sortSelect.addEventListener("change", () => {
    currentSort = sortSelect.value;
    page = 1;
    hasMore = true;
    list.innerHTML = "";
    if (moreBtn) moreBtn.classList.remove("hidden");
    loadPage();
  });
}

if (randomBtn) {
  randomBtn.addEventListener("click", async () => {
    randomBtn.disabled = true;
    randomBtn.textContent = "Loading...";
    try {
      const response = await fetch("/random-pdf/");
      if (!response.ok) throw new Error("Failed");
      const data = await response.json();
      if (data.pdf) {
        const slug = data.pdf.replace(/\.pdf$/i, "");
        window.location.href = `/${encodeURIComponent(slug)}`;
      }
    } catch (err) {
      console.error(err);
    } finally {
      randomBtn.disabled = false;
      randomBtn.textContent = "Random File";
    }
  });
}

if (searchInput) {
  searchInput.addEventListener("input", () => {
    if (searchTimer) window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => {
      currentQuery = searchInput.value.trim();
      page = 1;
      hasMore = true;
      list.innerHTML = "";
      if (moreBtn) moreBtn.classList.remove("hidden");
      loadPage();
    }, 200);
  });
}

loadPage();
if (document.body.dataset.auth === "1") {
  fetch("/notifications-count/")
    .then((response) => response.ok ? response.json() : null)
    .then((data) => {
      if (!data) return;
      notificationDots.forEach((dot) => {
        if (!dot) return;
        dot.classList.toggle("hidden", !data.count);
      });
    })
    .catch((err) => console.error(err));
}
