const chatbox = document.getElementById("chatbox");
const sendBtn = document.getElementById("sendBtn");
const usernameInput = document.getElementById("username");
const messageInput = document.getElementById("message");

sendBtn.addEventListener("click", async () => {
    const username = usernameInput.value || "Player";
    const message = messageInput.value.trim();
    if (!message) return;

    appendMessage(username, message, "user");
    messageInput.value = "";

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ username, message })
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
});

function appendMessage(sender, text, role) {
    const msg = document.createElement("div");
    msg.innerHTML = `<strong>${sender}:</strong> ${text}`;
    msg.style.margin = "5px 0";
    if (role === "assistant") msg.style.color = "green";
    if (role === "error") msg.style.color = "red";
    chatbox.appendChild(msg);
    chatbox.scrollTop = chatbox.scrollHeight;
}