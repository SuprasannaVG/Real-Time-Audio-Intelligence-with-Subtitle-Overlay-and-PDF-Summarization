let recognition;
let isRecording = false;
let finalTranscript = '';
const startButton = document.getElementById('start-recording');
const stopButton = document.getElementById('stop-recording');
const transcriptionBox = document.getElementById('transcription-box');
const inputTextArea = document.getElementById('input-text');
const audioTypeInput = document.getElementById('audio-type');
const customPromptTextArea = document.getElementById('custom-prompt');

if ('webkitSpeechRecognition' in window) {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onstart = () => {
    transcriptionBox.innerHTML = "Listening...";
    transcriptionBox.style.color = "green";
  };

  recognition.onresult = (event) => {
    let interimTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += transcript + ' ';
      } else {
        interimTranscript += transcript;
      }
    }
    transcriptionBox.innerHTML = finalTranscript + '<span style="color: #999;">' + interimTranscript + '</span>';
    inputTextArea.value = finalTranscript;
  };

  recognition.onerror = (event) => {
    console.error('Speech recognition error:', event.error);
    transcriptionBox.innerHTML = "Error occurred: " + event.error;
    transcriptionBox.style.color = "red";
  };

  recognition.onend = () => {
    transcriptionBox.innerHTML = finalTranscript || "No text recorded.";
    transcriptionBox.style.color = "black";
  };
} else {
  alert('Your browser does not support speech recognition.');
}

startButton.addEventListener('click', () => {
  if (!isRecording) {
    finalTranscript = '';
    recognition.start();
    isRecording = true;
    startButton.classList.add('hidden');
    stopButton.classList.remove('hidden');
  }
});

stopButton.addEventListener('click', () => {
  if (isRecording) {
    recognition.stop();
    isRecording = false;
    startButton.classList.remove('hidden');
    stopButton.classList.add('hidden');
  }
});

const audioOptions = document.querySelectorAll('.audio-option');
audioOptions.forEach(option => {
  option.addEventListener('click', () => {
    audioOptions.forEach(opt => opt.classList.remove('selected'));
    option.classList.add('selected');

    audioTypeInput.value = option.dataset.type;
    customPromptTextArea.style.display = option.dataset.type === 'custom' ? 'block' : 'none';
  });
});
