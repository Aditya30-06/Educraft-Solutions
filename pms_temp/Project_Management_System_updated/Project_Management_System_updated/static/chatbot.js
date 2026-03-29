// ── TOGGLE CHATBOT ──
const chatIcon = document.getElementById("chat-icon");
const chatBox  = document.getElementById("chatbot-box");

if (chatIcon) {
    chatIcon.addEventListener("click", () => {
        const isOpen = chatBox.style.display === "flex";
        chatBox.style.display = isOpen ? "none" : "flex";
        chatBox.style.flexDirection = "column";
        if (!isOpen) {
            document.getElementById("chat-input").focus();
        }
    });
}

// ── SEND MESSAGE ──
const input  = document.getElementById("chat-input");
const body   = document.getElementById("chat-body");
const sendBtn = document.getElementById("chat-send");

function appendMessage(text, type) {
    const div = document.createElement("div");
    div.className = type === "user" ? "chat-msg-user" : "chat-msg-bot";
    div.textContent = text;
    body.appendChild(div);
    
    // Smooth auto-scroll
    body.scrollTo({
        top: body.scrollHeight,
        behavior: "smooth"
    });
}

function sendMessage() {
    if (!input) return;
    const message = input.value.trim();
    if (!message) return;

    appendMessage(message, "user");
    input.value = "";

    // Add a typing indicator feel
    const typingId = Date.now();
    const typingDiv = document.createElement("div");
    typingDiv.className = "chat-msg-bot";
    typingDiv.id = `typing-${typingId}`;
    typingDiv.textContent = "typing...";
    body.appendChild(typingDiv);
    body.scrollTo({ top: body.scrollHeight, behavior: "smooth" });

    fetch("/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message })
    })
    .then(res => res.json())
    .then(data => { 
        document.getElementById(`typing-${typingId}`).remove();
        appendMessage(data.reply, "bot"); 
    })
    .catch(() => { 
        document.getElementById(`typing-${typingId}`).remove();
        appendMessage("⚠️ Server error. Try again.", "bot"); 
    });
}

if (input) {
    input.addEventListener("keypress", function (e) {
        if (e.key === "Enter") sendMessage();
    });
}
if (sendBtn) {
    sendBtn.addEventListener("click", sendMessage);
}