(function(){
	let audioContext;
	let mediaStream;
	let sourceNode;
	let processorNode;
	let recordedBuffers = [];
	let recordingSampleRate = 44100;

	function mergeBuffers(buffers) {
		let length = 0;
		for (const b of buffers) length += b.length;
		const result = new Float32Array(length);
		let offset = 0;
		for (const b of buffers) {
			result.set(b, offset);
			offset += b.length;
		}
		return result;
	}

	function floatTo16BitPCM(float32Array) {
		const buffer = new ArrayBuffer(float32Array.length * 2);
		const view = new DataView(buffer);
		let offset = 0;
		for (let i = 0; i < float32Array.length; i++, offset += 2) {
			let s = Math.max(-1, Math.min(1, float32Array[i]));
			view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
		}
		return view;
	}

	function writeWavHeader(samplesLength, sampleRate, numChannels) {
		const buffer = new ArrayBuffer(44);
		const view = new DataView(buffer);
		function writeString(view, offset, string) {
			for (let i = 0; i < string.length; i++) {
				view.setUint8(offset + i, string.charCodeAt(i));
			}
		}
		const bytesPerSample = 2;
		writeString(view, 0, 'RIFF');
		view.setUint32(4, 36 + samplesLength * bytesPerSample, true);
		writeString(view, 8, 'WAVE');
		writeString(view, 12, 'fmt ');
		view.setUint32(16, 16, true); // PCM
		view.setUint16(20, 1, true); // PCM format
		view.setUint16(22, numChannels, true);
		view.setUint32(24, sampleRate, true);
		view.setUint32(28, sampleRate * numChannels * bytesPerSample, true);
		view.setUint16(32, numChannels * bytesPerSample, true);
		view.setUint16(34, 16, true);
		writeString(view, 36, 'data');
		view.setUint32(40, samplesLength * bytesPerSample, true);
		return view;
	}

	function encodeWavMono(float32Samples, sampleRate) {
		const header = writeWavHeader(float32Samples.length, sampleRate, 1);
		const pcm = floatTo16BitPCM(float32Samples);
		const wavBuffer = new Uint8Array(44 + pcm.byteLength);
		wavBuffer.set(new Uint8Array(header.buffer), 0);
		wavBuffer.set(new Uint8Array(pcm.buffer), 44);
		return new Blob([wavBuffer], { type: 'audio/wav' });
	}

	async function startRecording() {
		mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
		audioContext = new (window.AudioContext || window.webkitAudioContext)();
		recordingSampleRate = audioContext.sampleRate;
		sourceNode = audioContext.createMediaStreamSource(mediaStream);
		processorNode = audioContext.createScriptProcessor(4096, 1, 1);
		recordedBuffers = [];
		processorNode.onaudioprocess = (e) => {
			const channelData = e.inputBuffer.getChannelData(0);
			recordedBuffers.push(new Float32Array(channelData));
		};
		sourceNode.connect(processorNode);
		processorNode.connect(audioContext.destination);
	}

	function stopRecording() {
		return new Promise((resolve) => {
			if (processorNode) {
				processorNode.disconnect();
				processorNode.onaudioprocess = null;
			}
			if (sourceNode) sourceNode.disconnect();
			if (mediaStream) mediaStream.getTracks().forEach(t => t.stop());
			if (audioContext) audioContext.close();

			const merged = mergeBuffers(recordedBuffers);
			const wavBlob = encodeWavMono(merged, recordingSampleRate);
			resolve(wavBlob);
		});
	}

	async function init() {
		const recordBtn = document.getElementById('recordBtn');
		const stopBtn = document.getElementById('stopBtn');
		const submitBtn = document.getElementById('submitBtn');
		const audioInput = document.getElementById('audioInput');
		const preview = document.getElementById('preview');

		recordBtn.addEventListener('click', async () => {
			try {
				await startRecording();
				recordBtn.disabled = true;
				stopBtn.disabled = false;
			} catch (e) {
				console.error(e);
				alert('Microphone permission denied or unavailable.');
			}
		});

		stopBtn.addEventListener('click', async () => {
			stopBtn.disabled = true;
			try {
				const blob = await stopRecording();
				const url = URL.createObjectURL(blob);
				preview.src = url;
				const dt = new DataTransfer();
				const file = new File([blob], 'recording.wav', { type: 'audio/wav' });
				dt.items.add(file);
				audioInput.files = dt.files;
				submitBtn.disabled = false;
			} catch (e) {
				console.error(e);
				alert('Failed to process audio.');
			}
			recordBtn.disabled = false;
		});
	}

	document.addEventListener('DOMContentLoaded', init);
})();
