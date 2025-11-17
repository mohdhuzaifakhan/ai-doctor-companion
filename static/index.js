const sendBtn = document.getElementById("sendBtn");
const uploadBtn = document.getElementById("uploadBtn");
const userInput = document.getElementById("userInput");
const chatWindow = document.getElementById("chat-window");
const fileInput = document.getElementById("fileInput");

// ---- WEBSOCKET SETUP ----
let socket = new WebSocket("ws://localhost:8000/ws");

socket.onopen = () => {
  console.log("WebSocket connected");
};

socket.onmessage = (event) => {
  hideTyping();
  addAIMessage(event.data);
};

socket.onerror = (error) => {
  console.error("WebSocket error:", error);
};

// ---- UI LOGIC (UNCHANGED) ----

function addUserMessage(text) {
  const msg = document.createElement("div");
  msg.className = "message user";
  msg.innerHTML = `${text}<div class="timestamp">${getTime()}</div>`;
  chatWindow.appendChild(msg);
  scrollToBottom();
}

function addAIMessage(text) {
  const msg = document.createElement("div");
  msg.className = "message ai";
  msg.innerHTML = `${text}<div class="timestamp">${getTime()}</div>`;
  chatWindow.appendChild(msg);
  scrollToBottom();
}

function showTyping() {
  const typing = document.createElement("div");
  typing.className = "message ai typing-bubble";
  typing.innerHTML = `
    <div class="typing">
      <span></span><span></span><span></span>
    </div>
  `;
  chatWindow.appendChild(typing);
  scrollToBottom();
}

function hideTyping() {
  const typing = document.querySelector(".typing-bubble");
  if (typing) typing.remove();
}

function getTime() {
  return new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  addUserMessage(text);
  userInput.value = "";

  showTyping();

  // ---- Send message to FastAPI WebSocket ----
  socket.send(text);
}

// File uploader (unchanged)
uploadBtn.onclick = () => fileInput.click();

fileInput.onchange = () => {
  const file = fileInput.files[0];
  if (!file) return;

  addUserMessage(`📄 Uploaded file: <b>${file.name}</b>`);

  // TODO: send to /upload-lab API
};

sendBtn.onclick = sendMessage;
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});

function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}
