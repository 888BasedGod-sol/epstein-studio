const list = document.getElementById("browseList");
const moreBtn = document.getElementById("browseMore");

let page = 1;
let loading = false;
let hasMore = true;

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
  link.href = `/${encodeURIComponent(item.slug || item.filename.replace(/\\.pdf$/i, ""))}`;
  const name = document.createElement("span");
  name.textContent = item.filename;
  link.appendChild(name);
  list.appendChild(link);
}

async function loadPage() {
  if (loading || !hasMore) return;
  setLoading(true);
  try {
    const response = await fetch(`/browse-list/?page=${page}`);
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

loadPage();
