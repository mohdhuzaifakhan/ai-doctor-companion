const sendBtn = document.getElementById("sendBtn");
const uploadBtn = document.getElementById("uploadBtn");
const userInput = document.getElementById("userInput");
const chatWindow = document.getElementById("chat-window");
const fileInput = document.getElementById("fileInput");

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

function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  addUserMessage(text);
  userInput.value = "";

  showTyping();

  socket.send(
    JSON.stringify({
      input_event: "user_message",
      user_message: text,
    })
  );
}

sendBtn.onclick = sendMessage;
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});

uploadBtn.onclick = () => fileInput.click();

fileInput.onchange = async () => {
  const file = fileInput.files[0];
  if (!file) return;

  addUserMessage(`Uploading file: <b>${file.name}</b>`);

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("http://localhost:8000/upload", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) throw new Error("Upload failed");

    const data = await response.json();
    console.log("Upload result:", data);

    const filePath = data.file_path;

    addUserMessage(`File uploaded successfully!`);

    showTyping();

    socket.send(
      JSON.stringify({
        input_event: "file_uploaded",
        file_path: filePath,
      })
    );

  } catch (err) {
    console.error(err);
    addAIMessage("File upload failed. Try again.");
  }
};
