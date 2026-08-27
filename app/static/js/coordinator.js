document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.camera-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const wrap = document.getElementById(btn.dataset.target);
      wrap.classList.toggle('active');
    });
  });

  document.querySelectorAll('.camera-wrap').forEach(wrap => {
    const video = wrap.querySelector('.cam-video');
    const canvas = wrap.querySelector('.cam-canvas');
    const dataInput = wrap.querySelector('.cam-data-input');
    const startBtn = wrap.querySelector('.cam-start');
    const shotBtn = wrap.querySelector('.cam-shot');
    const submitBtn = wrap.querySelector('.cam-submit');
    let stream = null;

    startBtn.addEventListener('click', async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
        video.srcObject = stream;
      } catch (err) {
        alert('Could not access the camera: ' + err.message);
      }
    });

    shotBtn.addEventListener('click', () => {
      if (!stream) { alert('Start the camera first.'); return; }
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
      dataInput.value = canvas.toDataURL('image/jpeg', 0.9);
      canvas.style.display = 'block';
      video.style.display = 'none';
    });

    submitBtn.addEventListener('click', () => {
      if (!dataInput.value) { alert('Capture a photo first.'); return; }
      wrap.closest('form').submit();
    });
  });
});
