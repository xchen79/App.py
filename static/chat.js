const chatbox = document.getElementById("chatbox");
const sendBtn = document.getElementById("sendBtn");
const usernameInput = document.getElementById("username");
const messageInput = document.getElementById("message");
const chatForm = document.getElementById("chatForm");

async function sendMessage(event) {
    if (event && event.preventDefault) event.preventDefault();
    const username = (usernameInput && usernameInput.value) || "Player";
    const message = (messageInput && messageInput.value.trim()) || "";
    if (!message) return;

    appendMessage(username, message, "user");
    if (messageInput) messageInput.value = "";

    // show typing indicator in coach bubble
    let typingElem = document.createElement("div");
    typingElem.className = "message bot typing";
    typingElem.innerHTML = `<span class="typing-dots" aria-hidden="true"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span>`;
    typingElem.setAttribute('aria-label', 'Coach is typing');
    chatbox.appendChild(typingElem);
    chatbox.scrollTop = chatbox.scrollHeight;

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, message }),
        });

        const resData = await res.json();
        // remove typing indicator
        if (typingElem && typingElem.parentNode) typingElem.parentNode.removeChild(typingElem);

        if (resData.ok) {
            // stream the assistant reply one phrase at a time
            await streamAssistantResponse("Coach", resData.reply);
            console.log("Response:", resData);
        } else {
            appendMessage("Error", resData.error, "error");
        }
    } catch (err) {
        // remove typing indicator
        if (typingElem && typingElem.parentNode) typingElem.parentNode.removeChild(typingElem);
        appendMessage("Error", err.message, "error");
    }
}

// helper: sleep
function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

// stream assistant response word-by-word (faster)
async function streamAssistantResponse(sender, text) {
    const msg = document.createElement("div");
    msg.className = "message bot";
    msg.innerHTML = `<strong>${sender}:</strong> <span class="assistant-content"></span>`;
    msg.setAttribute('aria-label', sender + ': ' + text);

    // split into words (preserve punctuation attached to words)
    const words = text.split(/\s+/).filter(Boolean);

    // append message container immediately so user sees it
    chatbox.appendChild(msg);
    const contentSpan = msg.querySelector('.assistant-content');
    chatbox.scrollTop = chatbox.scrollHeight;

    for (const word of words) {
        // append next word and update scroll
        contentSpan.textContent = (contentSpan.textContent + (contentSpan.textContent ? ' ' : '') + word).trimEnd();
        chatbox.scrollTop = chatbox.scrollHeight;

        // faster delay per word: ~15ms per character, min 20ms, max 80ms
        const delay = Math.max(20, Math.min(80, word.length * 15));
        await sleep(delay);
    }
}

// handle form submit (covers Enter key and clicking the send button)
if (chatForm) {
    chatForm.addEventListener("submit", sendMessage);
} else if (sendBtn) {
    // fallback: if form isn't present, keep click handler
    sendBtn.addEventListener("click", sendMessage);
}

function appendMessage(sender, text, role) {
    const msg = document.createElement("div");
    // assign CSS classes so bubbles align left/right per role
    if (role === "assistant") {
        msg.className = "message bot";
    } else if (role === "user") {
        msg.className = "message user";
    } else if (role === "error") {
        msg.className = "message error";
        msg.style.color = "red";
    } else {
        msg.className = "message";
    }
    // show sender label only for assistant (coach), keep user messages label-free
    if (role === "assistant") {
        msg.innerHTML = `<strong>${sender}:</strong> ${text}`;
        msg.setAttribute('aria-label', sender + ': ' + text);
    } else {
        msg.textContent = text;
        msg.setAttribute('aria-label', sender + ': ' + text);
    }
    // increase vertical spacing between message rows
    msg.style.margin = "24px 0";
    chatbox.appendChild(msg);
    chatbox.scrollTop = chatbox.scrollHeight;
}