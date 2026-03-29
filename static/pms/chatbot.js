// ── PMS PROJECT ASSISTANT CHATBOT — MENU-DRIVEN ──
const chatIcon = document.getElementById("chat-icon");
const chatBox  = document.getElementById("chatbot-box");

if (chatIcon) {
    chatIcon.addEventListener("click", () => {
        const isOpen = chatBox.style.display === "flex";
        chatBox.style.display = isOpen ? "none" : "flex";
        chatBox.style.flexDirection = "column";
        if (!isOpen) setTimeout(() => showMainMenu(), 100);
    });
}

const body = document.getElementById("chat-body");

// Hide input area — fully menu-driven
const chatInput = document.getElementById("chat-input");
const chatSend  = document.getElementById("chat-send");
if (chatInput) chatInput.style.display = "none";
if (chatSend)  chatSend.style.display  = "none";

// ── Core helpers ──
function appendBot(html) {
    const div = document.createElement("div");
    div.className = "chat-msg-bot";
    div.innerHTML = html;
    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
}

function appendUser(text) {
    const div = document.createElement("div");
    div.className = "chat-msg-user";
    div.textContent = text;
    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
}

function clearMenus() {
    body.querySelectorAll(".chat-menu-row").forEach(m => m.remove());
}

function showMenuAfter(ms, options) {
    // Typing indicator
    const dot = document.createElement("div");
    dot.className = "chat-msg-bot";
    dot.id = "pms-typing";
    dot.textContent = "typing...";
    body.appendChild(dot);
    body.scrollTop = body.scrollHeight;

    setTimeout(() => {
        dot.remove();
        showMenu(options);
    }, ms);
}

function showMenu(options) {
    clearMenus();
    const wrap = document.createElement("div");
    wrap.className = "chat-menu-row";
    wrap.style.cssText = "display:flex;flex-wrap:wrap;gap:6px;padding:6px 8px 2px;";
    options.forEach(opt => {
        const btn = document.createElement("button");
        btn.style.cssText = "background:rgba(26,60,110,0.08);border:1px solid rgba(26,60,110,0.2);color:#1a3c6e;border-radius:20px;padding:5px 12px;font-size:0.78rem;font-weight:600;cursor:pointer;font-family:inherit;transition:all 0.2s;";
        btn.textContent = opt.label;
        btn.onmouseover = () => { btn.style.background = "#1a3c6e"; btn.style.color = "#fff"; };
        btn.onmouseout  = () => { btn.style.background = "rgba(26,60,110,0.08)"; btn.style.color = "#1a3c6e"; };
        btn.onclick = () => {
            clearMenus();
            appendUser(opt.label);
            showMenuAfter(500, []);
            setTimeout(() => opt.action(), 500);
        };
        wrap.appendChild(btn);
    });
    body.appendChild(wrap);
    body.scrollTop = body.scrollHeight;
}

// ── Menu Definitions ──
function mainBackBtn() {
    return { label: "🏠 Main Menu", action: () => { appendBot("Sure! Back to main menu:"); showMainMenu(); } };
}

function showMainMenu() {
    appendBot("👋 Hi! I'm your <b>Project Assistant</b>. What would you like to know?");
    showMenu([
        { label: "📊 Project Status",    action: projectStatusMenu },
        { label: "📋 My Projects",       action: myProjectsMenu },
        { label: "⏱ Deadlines",         action: deadlinesMenu },
        { label: "📈 Progress Updates",  action: progressMenu },
        { label: "📁 Deliverables",      action: deliverablesMenu },
        { label: "📞 Contact Support",   action: supportMenu },
    ]);
}

function projectStatusMenu() {
    appendBot("📊 <b>Project Status Types</b><br><br>Your projects can have the following statuses:<br><br>• 🟡 <b>In Progress</b> — Actively being worked on<br>• ✅ <b>Completed</b> — Delivered and closed<br>• ⏸ <b>On Hold</b> — Temporarily paused<br>• 🕐 <b>Pending</b> — Awaiting start or client input<br><br>Check your dashboard for real-time status updates.");
    showMenu([
        { label: "📋 My Projects", action: myProjectsMenu },
        mainBackBtn(),
    ]);
}

function myProjectsMenu() {
    appendBot("📋 <b>Your Projects</b><br><br>All your assigned projects are listed on the <b>Dashboard</b>. You can:<br><br>• Click any project name to view full details<br>• See progress bars and deadlines at a glance<br>• Track status changes in real-time<br><br>Return to the dashboard to view your project list.");
    showMenu([
        { label: "📈 Progress Updates", action: progressMenu },
        { label: "⏱ Deadlines", action: deadlinesMenu },
        mainBackBtn(),
    ]);
}

function deadlinesMenu() {
    appendBot("⏱ <b>Deadlines</b><br><br>Your project deadlines are shown in the <b>Deadline</b> column on your dashboard.<br><br>• Deadlines are confirmed during project setup<br>• Any changes are communicated by your project manager<br>• If you need an extension, contact support<br><br>Need help? Reach out to our team.");
    showMenu([
        { label: "📞 Contact Support", action: supportMenu },
        mainBackBtn(),
    ]);
}

function progressMenu() {
    appendBot("📈 <b>Progress Updates</b><br><br>Progress is updated regularly by your project manager. You can see it as a <b>percentage bar</b> on your dashboard.<br><br>• 0–25% — Initial phase<br>• 25–50% — Research & drafting<br>• 50–75% — Review & revision<br>• 75–100% — Final delivery stage<br><br>Updates are reflected in real-time.");
    showMenu([
        { label: "📁 Deliverables", action: deliverablesMenu },
        { label: "📞 Contact Support", action: supportMenu },
        mainBackBtn(),
    ]);
}

function deliverablesMenu() {
    appendBot("📁 <b>Deliverables</b><br><br>Your project deliverables include:<br><br>• Final research document / paper<br>• Plagiarism report (Turnitin)<br>• Revision copies (as per your package)<br>• Reference list & citations<br><br>Deliverables are shared via email or through your project manager.");
    showMenu([
        { label: "📞 Contact Support", action: supportMenu },
        mainBackBtn(),
    ]);
}

function supportMenu() {
    appendBot("📞 <b>Contact Support</b><br><br>📱 <b>Phone / WhatsApp:</b> +91 9821693299<br>📧 <b>Email:</b> pshiksha4.0@gmail.com<br><br>⏰ <b>Hours:</b> Mon–Sat 9AM–7PM | Sun 10AM–2PM<br><br>Your project manager will respond within a few hours.");
    showMenu([
        { label: "📊 Project Status", action: projectStatusMenu },
        mainBackBtn(),
    ]);
}

// Auto-welcome on page load
document.addEventListener("DOMContentLoaded", () => {
    if (body) {
        appendBot("👋 Hi! I'm your <b>Project Assistant</b>. Click 💬 below to start.");
    }
});