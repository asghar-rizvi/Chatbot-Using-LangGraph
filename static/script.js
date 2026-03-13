/* ── State ──────────────────────────────────────────── */
let currentChatId = null;
let isStreaming = false;

/* ── DOM refs ───────────────────────────────────────── */
const $chatList   = document.getElementById("chat-list");
const $messages   = document.getElementById("messages");
const $input      = document.getElementById("msg-input");
const $sendBtn    = document.getElementById("btn-send");
const $title      = document.getElementById("chat-title");
const $pdfInput   = document.getElementById("pdf-input");
const $uploadSt   = document.getElementById("upload-status");
const $sidebar    = document.getElementById("sidebar");

/* ── Tool display names ─────────────────────────────── */
const TOOL_LABEL = {
  add:              "🧮 Adding",
  subtract:         "🧮 Subtracting",
  multiply:         "🧮 Multiplying",
  divide:           "🧮 Dividing",
  get_stock_price:  "📈 Fetching stock price",
  web_search:       "🔍 Searching the web",
  search_documents: "📄 Searching documents",
};

/* ── Helpers ────────────────────────────────────────── */
function uid() {
  return crypto.randomUUID
    ? crypto.randomUUID()
    : "xxxx-xxxx-xxxx".replace(/x/g, () => ((Math.random() * 16) | 0).toString(16));
}

function scrollBottom() {
  $messages.scrollTo({ top: $messages.scrollHeight, behavior: "smooth" });
}

/* ── API calls ──────────────────────────────────────── */
async function apiCreateChat(id, title) {
  await fetch("/api/chats", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, title }),
  });
}

async function apiGetChats() {
  const r = await fetch("/api/chats");
  return r.json();
}

async function apiDeleteChat(id) {
  await fetch(`/api/chats/${id}`, { method: "DELETE" });
}

async function apiGetMessages(id) {
  const r = await fetch(`/api/chats/${id}/messages`);
  return r.json();
}

/* ── Render chat list ───────────────────────────────── */
async function loadChats() {
  const chats = await apiGetChats();
  $chatList.innerHTML = "";
  chats.forEach((c) => {
    const div = document.createElement("div");
    div.className = "chat-item" + (c.id === currentChatId ? " active" : "");
    div.innerHTML = `<span class="title">${esc(c.title)}</span><button class="del" title="Delete">×</button>`;
    div.querySelector(".title").onclick = () => selectChat(c.id, c.title);
    div.querySelector(".del").onclick = async (e) => {
      e.stopPropagation();
      await apiDeleteChat(c.id);
      if (currentChatId === c.id) { currentChatId = null; showWelcome(); }
      loadChats();
    };
    $chatList.appendChild(div);
  });
}

/* ── Render messages ────────────────────────────────── */
function showWelcome() {
  $title.textContent = "Select or create a chat";
  $messages.innerHTML = `
    <div class="welcome">
      <h2>🤖 AI Chatbot</h2><p>Create a chat to get started</p>
      <div class="pills">
        <span>🧮 Calculator</span><span>📈 Stocks</span>
        <span>🔍 Web Search</span><span>📄 PDF RAG</span>
      </div>
    </div>`;
}

function appendBubble(role, html) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = html;
  wrap.appendChild(bubble);
  $messages.appendChild(wrap);
  scrollBottom();
  return bubble;
}

async function selectChat(id, title) {
  currentChatId = id;
  $title.textContent = title;
  $messages.innerHTML = "";
  const msgs = await apiGetMessages(id);
  msgs.forEach((m) => {
    const html =
      m.role === "user" ? esc(m.content) : marked.parse(m.content || "");
    appendBubble(m.role === "user" ? "user" : "assistant", html);
  });
  scrollBottom();
  loadChats();
  // close sidebar on mobile
  if (window.innerWidth <= 768) $sidebar.classList.add("hidden");
}

/* ── Streaming send ─────────────────────────────────── */
async function sendMessage() {
  const text = $input.value.trim();
  if (!text || isStreaming) return;

  // create chat if needed
  if (!currentChatId) {
    const id = uid();
    await apiCreateChat(id, "New Chat");
    currentChatId = id;
    // clear welcome
    $messages.innerHTML = "";
    await loadChats();
  }

  // show user bubble
  appendBubble("user", esc(text));
  $input.value = "";
  $input.style.height = "auto";
  setStreaming(true);

  // prepare assistant bubble
  const bubble = appendBubble("assistant", "");
  let mdText = "";

  try {
    const res = await fetch(`/api/chats/${currentChatId}/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: text }),
    });

    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop();

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data: ")) continue;
        let d;
        try { d = JSON.parse(trimmed.slice(6)); } catch { continue; }

        if (d.type === "tool_start") {
          const pill = document.createElement("div");
          pill.className = "tool-pill";
          pill.id = `tool-${d.name}`;
          pill.innerHTML = `<span class="spinner"></span><span>${TOOL_LABEL[d.name] || d.name}…</span>`;
          bubble.appendChild(pill);
          scrollBottom();
        } else if (d.type === "tool_end") {
          const pill = document.getElementById(`tool-${d.name}`);
          if (pill) {
            pill.classList.add("done");
            pill.innerHTML = `<span class="check">✓</span><span>${TOOL_LABEL[d.name] || d.name} done</span>`;
          }
        } else if (d.type === "token") {
          mdText += d.content;
          // ensure a text container exists
          let tc = bubble.querySelector(".text-content");
          if (!tc) {
            tc = document.createElement("div");
            tc.className = "text-content";
            bubble.appendChild(tc);
          }
          tc.innerHTML = marked.parse(mdText);
          scrollBottom();
        } else if (d.type === "error") {
          bubble.innerHTML += `<p style="color:var(--red)">Error: ${esc(d.content)}</p>`;
        }
      }
    }
  } catch (e) {
    bubble.innerHTML += `<p style="color:var(--red)">Network error: ${esc(e.message)}</p>`;
  }

  setStreaming(false);
  loadChats(); // refresh title
}

/* ── UI helpers ─────────────────────────────────────── */
function setStreaming(v) {
  isStreaming = v;
  $sendBtn.disabled = v;
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

/* ── Auto-resize textarea ───────────────────────────── */
$input.addEventListener("input", () => {
  $input.style.height = "auto";
  $input.style.height = Math.min($input.scrollHeight, 160) + "px";
});

/* ── Key bindings ───────────────────────────────────── */
$input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

/* ── Button clicks ──────────────────────────────────── */
$sendBtn.addEventListener("click", sendMessage);

document.getElementById("btn-new").addEventListener("click", async () => {
  const id = uid();
  await apiCreateChat(id, "New Chat");
  currentChatId = id;
  $messages.innerHTML = "";
  $title.textContent = "New Chat";
  loadChats();
  $input.focus();
});

document.getElementById("btn-menu").addEventListener("click", () => {
  $sidebar.classList.toggle("hidden");
});

/* ── PDF Upload ─────────────────────────────────────── */
$pdfInput.addEventListener("change", async () => {
  const file = $pdfInput.files[0];
  if (!file) return;
  $uploadSt.textContent = "Uploading…";
  const fd = new FormData();
  fd.append("file", file);
  try {
    const r = await fetch("/api/upload", { method: "POST", body: fd });
    const d = await r.json();
    if (d.error) {
      $uploadSt.textContent = "❌ " + d.error;
    } else {
      $uploadSt.textContent = `✅ ${d.filename} — ${d.chunks} chunks`;
    }
  } catch (e) {
    $uploadSt.textContent = "❌ Upload failed";
  }
  $pdfInput.value = "";
});

/* ── Init ───────────────────────────────────────────── */
loadChats();
if (window.innerWidth <= 768) $sidebar.classList.add("hidden");