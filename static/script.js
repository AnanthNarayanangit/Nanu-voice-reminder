let mediaRecorder;
let audioChunks = [];
let audioBlob = null;

// ---------------- START RECORDING ----------------
function startRecording() {
    const language = document.getElementById("language").value;

    navigator.mediaDevices.getUserMedia({
        audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            channelCount: 1,
            sampleRate: 44100
        }
    })
    .then(stream => {
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: "audio/webm;codecs=opus",
            audioBitsPerSecond: 128000
        });

        audioChunks = [];

        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            // Create audio blob
            audioBlob = new Blob(audioChunks, { type: "audio/webm" });

            // Speech to text
            const recognition = new webkitSpeechRecognition();
            recognition.lang = language;
            recognition.interimResults = false;

            recognition.onresult = event => {
                document.getElementById("text").value =
                    event.results[0][0].transcript;
            };

            recognition.onerror = () => {
                alert("Speech recognition failed. Please try again.");
            };

            recognition.start();
        };

        mediaRecorder.start();

        // Auto-stop after 5 seconds
        setTimeout(() => {
            if (mediaRecorder.state !== "inactive") {
                mediaRecorder.stop();
            }
        }, 5000);
    })
    .catch(() => {
        alert("Microphone access denied or not available.");
    });
}

// ---------------- DELETE / RESET ----------------
function deleteRecording() {
    document.getElementById("text").value = "";
    audioBlob = null;
}

// ---------------- SAVE REMINDER ----------------
function saveReminder() {
    const text = document.getElementById("text").value.trim();
    const datetime = document.getElementById("datetime").value;

    if (!text) {
        alert("Please record or type a reminder message.");
        return;
    }

    if (!datetime) {
        alert("Please select date and time.");
        return;
    }

    const formData = new FormData();
    formData.append("text", text);
    formData.append("datetime", datetime);

    // Audio is optional (text-only reminder allowed)
    if (audioBlob) {
        formData.append("audio", audioBlob);
    }

    fetch("/save", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);

        // Reset after save
        deleteRecording();
        document.getElementById("datetime").value = "";
    })
    .catch(() => {
        alert("Error saving reminder. Please try again.");
    });
}
