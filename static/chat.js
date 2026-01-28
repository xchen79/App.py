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

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, message }),
        });

        const resData = await res.json();
        if (resData.ok) {
            appendMessage("Coach", resData.reply, "assistant");
            console.log("Response:", resData);
        } else {
            appendMessage("Error", resData.error, "error");
        }
    } catch (err) {
        appendMessage("Error", err.message, "error");
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
    msg.innerHTML = `<strong>${sender}:</strong> ${text}`;
    msg.style.margin = "5px 0";
    chatbox.appendChild(msg);
    chatbox.scrollTop = chatbox.scrollHeight;
}