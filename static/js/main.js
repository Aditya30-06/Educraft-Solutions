// ===== NAVBAR SCROLL =====
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) navbar.classList.add('scrolled');
    else navbar.classList.remove('scrolled');
});

// ===== HAMBURGER =====
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');
hamburger?.addEventListener('click', () => {
    navLinks.classList.toggle('open');
    hamburger.classList.toggle('active');
});

// ===== CHATBOT — MENU-DRIVEN =====
const chatbotToggle = document.getElementById('chatbotToggle');
const chatbotBox = document.getElementById('chatbotBox');
const chatbotClose = document.getElementById('chatbotClose');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');
const chatMessages = document.getElementById('chatbotMessages');
const chatIcon = document.getElementById('chatIcon');
const chatIconClose = document.getElementById('chatIconClose');
const chatBadge = document.getElementById('chatBadge');

function openChat() {
    chatbotBox.classList.add('open');
    chatIcon.style.display = 'none';
    chatIconClose.style.display = 'block';
    if (chatBadge) chatBadge.style.display = 'none';
}

function closeChat() {
    chatbotBox.classList.remove('open');
    chatIcon.style.display = 'block';
    chatIconClose.style.display = 'none';
}

chatbotToggle?.addEventListener('click', () => {
    if (chatbotBox.classList.contains('open')) closeChat();
    else openChat();
});
chatbotClose?.addEventListener('click', closeChat);

// ── Core helpers ──
function addMessage(html, isUser = false) {
    const div = document.createElement('div');
    div.className = 'chat-msg ' + (isUser ? 'user' : 'bot');
    div.innerHTML = `<div class="chat-bubble">${html}</div>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function clearMenus() {
    chatMessages.querySelectorAll('.chat-menu').forEach(m => m.remove());
}

function showTypingThen(ms, callback) {
    const dot = document.createElement('div');
    dot.className = 'chat-msg bot';
    dot.id = 'typingIndicator';
    dot.innerHTML = `<div class="chat-bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div>`;
    chatMessages.appendChild(dot);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    setTimeout(() => { dot.remove(); callback(); }, ms);
}

function showMenu(options) {
    clearMenus();
    const wrap = document.createElement('div');
    wrap.className = 'chat-menu';
    wrap.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px;padding:8px 12px 4px;';
    options.forEach(opt => {
        const btn = document.createElement('button');
        btn.className = 'suggestion-btn';
        btn.textContent = opt.label;
        btn.onclick = () => {
            clearMenus();
            addMessage(opt.label, true);
            showTypingThen(600, () => opt.action());
        };
        wrap.appendChild(btn);
    });
    chatMessages.appendChild(wrap);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ── Menu Definitions ──
function mainMenu() {
    showMenu([
        { label: '📦 Our Packages', action: packagesMenu },
        { label: '🔬 Plagiarism Check', action: plagiarismMenu },
        { label: '⏱ Delivery Timeline', action: timelineMenu },
        { label: '💰 Pricing', action: pricingMenu },
        { label: '🚀 Get Started', action: getStartedMenu },
        { label: '📞 Contact Us', action: contactMenu },
    ]);
}

function packagesMenu() {
    addMessage('We offer <b>3 research packages</b>. Which would you like to know about?');
    showMenu([
        { label: '📗 Basic Research', action: basicPackage },
        { label: '📘 Applied Research', action: appliedPackage },
        { label: '📕 Advanced Research', action: advancedPackage },
        { label: '🏠 Main Menu', action: () => { addMessage('Sure! Here\'s what I can help with:'); mainMenu(); } },
    ]);
}

function basicPackage() {
    addMessage('📗 <b>Basic Research</b><br><br>✅ Topic finalization support<br>✅ Basic research drafting<br>✅ 1 Plagiarism check (Turnitin) &lt;20%<br>✅ 1–2 revisions<br>✅ Standard delivery timeline<br><br><i>Ideal for UG/PG students starting their journey.</i>');
    backOrContact();
}

function appliedPackage() {
    addMessage('📘 <b>Applied Research</b><br><br>✅ In-depth research & technical writing<br>✅ Plagiarism below 12%<br>✅ Methodology + data interpretation<br>✅ Conference shortlisting support<br>✅ 3–4 revisions<br>✅ Faster delivery than Basic<br><br><i>Designed for serious researchers & PG students.</i>');
    backOrContact();
}

function advancedPackage() {
    addMessage('📕 <b>Advanced Research</b><br><br>✅ High impact & technical paper writing<br>✅ Plagiarism below 8%<br>✅ Scopus / SCI / Web of Science targeting<br>✅ Unlimited revisions & priority delivery<br>✅ Submission & reviewer comment support<br><br><i>End-to-end premium support for PhD scholars & corporates.</i>');
    backOrContact();
}

function plagiarismMenu() {
    addMessage('🔬 <b>Plagiarism Checking</b><br><br>We use <b>Turnitin</b> and advanced tools to ensure original content:<br><br>• Basic — below <b>20%</b><br>• Applied — below <b>12%</b><br>• Advanced — below <b>8%</b><br><br>All work is checked before delivery and revised if needed.');
    backOrContact();
}

function timelineMenu() {
    addMessage('⏱ <b>Delivery Timelines</b><br><br>Timelines vary by package and complexity:<br><br>• <b>Basic</b> — Standard delivery (depends on scope)<br>• <b>Applied</b> — Faster than Basic<br>• <b>Advanced</b> — Priority delivery, expedited available<br><br>We are fully committed to your agreed deadline.');
    backOrContact();
}

function pricingMenu() {
    addMessage('💰 <b>Pricing</b><br><br>Pricing depends on your <b>course, subject, scope, and deadline</b>. Our expert will give you an exact quote once we understand your needs.<br><br>Would you like to get a personalised quote?');
    showMenu([
        { label: '✅ Yes, get a quote', action: getStartedMenu },
        { label: '📦 See Packages First', action: packagesMenu },
        { label: '🏠 Main Menu', action: () => { addMessage('Sure! Here\'s what I can help with:'); mainMenu(); } },
    ]);
}

function getStartedMenu() {
    addMessage('🚀 <b>Getting Started is easy!</b><br><br>Please share:<br>• Your <b>course</b> (UG/PG/PhD)<br>• <b>Domain / Subject</b><br>• <b>Deadline</b><br>• Current status (if any work done)<br><br>Based on this, our expert will recommend the best package and connect with you shortly!');
    showMenu([
        { label: '📞 Call Us Now', action: contactMenu },
        { label: '📧 Email Us', action: emailMenu },
        { label: '🏠 Main Menu', action: () => { addMessage('Sure! Here\'s what I can help with:'); mainMenu(); } },
    ]);
}

function contactMenu() {
    addMessage('📞 <b>Contact Us</b><br><br>📱 <b>Phone / WhatsApp:</b> <a href="tel:+919821693299" style="color:var(--teal)">+91 9821693299</a><br>📧 <b>Email:</b> <a href="mailto:pshiksha4.0@gmail.com" style="color:var(--teal)">pshiksha4.0@gmail.com</a><br>🏢 <b>Address:</b> 1/191, Ground Floor, Subhash Nagar, New Delhi – 110027<br><br>⏰ <b>Hours:</b> Mon–Sat 9AM–7PM | Sun 10AM–2PM');
    showMenu([
        { label: '📦 View Packages', action: packagesMenu },
        { label: '🏠 Main Menu', action: () => { addMessage('Sure! Here\'s what I can help with:'); mainMenu(); } },
    ]);
}

function emailMenu() {
    addMessage('📧 Drop us an email at <a href="mailto:pshiksha4.0@gmail.com" style="color:var(--teal)">pshiksha4.0@gmail.com</a> with your details and we\'ll respond within 24 hours!');
    backOrContact();
}

function backOrContact() {
    showMenu([
        { label: '📞 Contact Us', action: contactMenu },
        { label: '📦 All Packages', action: packagesMenu },
        { label: '🏠 Main Menu', action: () => { addMessage('Sure! Here\'s what I can help with:'); mainMenu(); } },
    ]);
}

// ── Launch on open / suggestion click ──
function sendSuggestion(text) {
    openChat();
    clearMenus();
    addMessage(text, true);
    showTypingThen(600, () => {
        if (text.includes('packages')) packagesMenu();
        else if (text.includes('plagiarism')) plagiarismMenu();
        else if (text.includes('timeline')) timelineMenu();
        else if (text.includes('started')) getStartedMenu();
        else mainMenu();
    });
}

// Re-enable text input — hybrid mode (menu + typing)
function sendMessage() {
    const text = chatInput ? chatInput.value.trim() : '';
    if (!text) return;
    clearMenus();
    addMessage(text, true);
    chatInput.value = '';
    const t = text.toLowerCase();
    showTypingThen(600, () => {
        if (t.includes('package') || t.includes('basic') || t.includes('applied') || t.includes('advanced')) packagesMenu();
        else if (t.includes('plagiar')) plagiarismMenu();
        else if (t.includes('timeline') || t.includes('deadline') || t.includes('delivery')) timelineMenu();
        else if (t.includes('price') || t.includes('pricing') || t.includes('cost') || t.includes('fee')) pricingMenu();
        else if (t.includes('start') || t.includes('begin') || t.includes('help')) getStartedMenu();
        else if (t.includes('contact') || t.includes('phone') || t.includes('email') || t.includes('call')) contactMenu();
        else { addMessage('I\'m not sure about that, but here\'s what I can help with:'); mainMenu(); }
    });
}

if (chatInput) chatInput.addEventListener('keydown', e => { if (e.key === 'Enter') sendMessage(); });
if (chatSend) chatSend.addEventListener('click', sendMessage);

// Auto-show main menu after welcome message
setTimeout(() => { if (chatMessages) mainMenu(); }, 300);

// ===== SCROLL ANIMATIONS =====
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, { threshold: 0.1 });

document.querySelectorAll('.service-card, .dest-card, .testimonial-card, .overseas-card, .os-card, .sd-card, .team-card, .num-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(24px)';
    el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(el);
});

// ===== AUTO-DISMISS FLASH MESSAGES =====
setTimeout(() => {
    document.querySelectorAll('.flash').forEach(el => el.remove());
}, 5000);

// ===== DESTINATIONS BACKGROUND =====
document.querySelectorAll('.dest-card').forEach(card => {
    const bg = card.style.getPropertyValue('--bg');
    if (bg) card.style.backgroundImage = bg;
});
