/**
 * Diagnostic Studio & Explainability Module
 * Handles single-image uploads, Grad-CAM attention visualizers, and top-5 probability spectrum.
 */

export class DiagnosticView {
  constructor(showToast = () => {}) {
    this.showToast = showToast;
    this.dropzone = document.getElementById('image-dropzone');
    this.fileInput = document.getElementById('diag-file-input');
    this.cropImg = document.getElementById('diag-crop-img');
    this.heatImg = document.getElementById('diag-heat-img');
    this.cropPlaceholder = document.getElementById('diag-crop-placeholder');
    this.heatPlaceholder = document.getElementById('diag-heat-placeholder');

    this.top1Action = document.getElementById('diag-top1-action');
    this.top1Category = document.getElementById('diag-top1-category');
    this.top1Conf = document.getElementById('diag-top1-conf');
    this.probSpectrum = document.getElementById('diag-prob-spectrum');
    this.cuesContainer = document.getElementById('diag-cues-container');

    this.initEvents();
  }

  initEvents() {
    // Dropzone Click
    this.dropzone.addEventListener('click', () => {
      this.fileInput.click();
    });

    // File Input Change
    this.fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        this.processImageFile(file);
      }
    });

    // Drag and Drop
    ['dragenter', 'dragover'].forEach(eventName => {
      this.dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        this.dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      this.dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        this.dropzone.classList.remove('dragover');
      });
    });

    this.dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const file = dt.files[0];
      if (file) {
        this.processImageFile(file);
      }
    });

    // Quick-test Presets
    const presetButtons = document.querySelectorAll('.preset-chip-btn');
    presetButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const actionType = e.target.getAttribute('data-preset');
        this.testWithSyntheticPreset(actionType);
      });
    });
  }

  async processImageFile(file) {
    this.showToast('Analyzing Image', `Running HAR inference and Grad-CAM on ${file.name}...`, 'info');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/predict/image', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();
      this.renderDiagnosticResults(data);
      this.showToast('Diagnostic Complete', `Classified as ${data.top_action} (${Math.round(data.confidence * 100)}%)`, 'success');
    } catch (err) {
      console.error('Diagnostic inference failed:', err);
      this.showToast('Analysis Error', 'Failed to process image inference.', 'critical');
    }
  }

  renderDiagnosticResults(data) {
    // 1. Display Crop & Heatmap Images
    this.cropImg.src = data.crop_b64;
    this.cropImg.style.display = 'block';
    this.cropPlaceholder.style.display = 'none';

    this.heatImg.src = data.heatmap_b64;
    this.heatImg.style.display = 'block';
    this.heatPlaceholder.style.display = 'none';

    // 2. Top-1 Banner
    this.top1Action.textContent = data.top_action.replace('_', ' ');
    const meta = data.metadata || {};
    this.top1Category.textContent = `${meta.category || 'Human Action'} • Associated objects: ${(meta.associated_objects || []).join(', ') || 'N/A'}`;
    this.top1Conf.textContent = `${Math.round(data.confidence * 100)}%`;

    // 3. Top-5 Probability Bars
    if (data.top5) {
      this.probSpectrum.innerHTML = data.top5.map(item => {
        const pct = Math.round(item.confidence * 100);
        const col = item.metadata ? item.metadata.color : '#00f2fe';
        return `
          <div class="prob-row">
            <div class="prob-meta-line">
              <span style="color: ${col};">${item.class.replace('_', ' ')}</span>
              <span><strong>${pct}%</strong></span>
            </div>
            <div class="prob-track-outer">
              <div class="prob-track-fill" style="width: ${pct}%; background: ${col};"></div>
            </div>
          </div>
        `;
      }).join('');
    }

    // 4. Posture Cues
    const cues = meta.posture_cues || [];
    if (cues.length > 0) {
      this.cuesContainer.innerHTML = cues.map(c => `
        <span class="cue-tag">✓ ${c}</span>
      `).join('');
    } else {
      this.cuesContainer.innerHTML = '<span class="cue-tag">Standard posture patterns observed.</span>';
    }
  }

  testWithSyntheticPreset(actionType) {
    // Generate a synthetic high-resolution diagnostic frame with the given action cues on an offscreen canvas
    const canvas = document.createElement('canvas');
    canvas.width = 400;
    canvas.height = 400;
    const ctx = canvas.getContext('2d');

    // Background gradient
    const grad = ctx.createLinearGradient(0, 0, 400, 400);
    grad.addColorStop(0, '#101726');
    grad.addColorStop(1, '#1e293b');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 400, 400);

    // Subject Body
    ctx.fillStyle = '#cbd5e1';
    // Head
    ctx.beginPath();
    ctx.arc(200, 110, 40, 0, Math.PI * 2);
    ctx.fill();

    // Torso
    ctx.fillStyle = '#3b82f6';
    ctx.fillRect(150, 160, 100, 140);

    // Specific Object Cues per action preset
    if (actionType === 'using_laptop') {
      ctx.fillStyle = '#94a3b8';
      ctx.fillRect(130, 270, 140, 20); // base
      ctx.fillStyle = '#00f2fe';
      ctx.fillRect(140, 210, 120, 60); // glowing screen
    } else if (actionType === 'calling') {
      ctx.fillStyle = '#1e293b';
      ctx.fillRect(235, 90, 18, 40); // Phone against ear
    } else if (actionType === 'drinking') {
      ctx.fillStyle = '#14b8a6';
      ctx.beginPath();
      ctx.arc(220, 125, 20, 0, Math.PI * 2); // Mug to lips
      ctx.fill();
    } else if (actionType === 'texting') {
      ctx.fillStyle = '#1e293b';
      ctx.fillRect(180, 220, 40, 60); // Phone held in hands at chest
    } else if (actionType === 'fighting') {
      // Second opponent
      ctx.fillStyle = '#ef4444';
      ctx.fillRect(230, 170, 90, 130);
      ctx.beginPath();
      ctx.arc(275, 120, 36, 0, Math.PI * 2);
      ctx.fill();
    } else if (actionType === 'running') {
      // Dynamic limbs
      ctx.strokeStyle = '#e11d48';
      ctx.lineWidth = 14;
      ctx.beginPath();
      ctx.moveTo(150, 290); ctx.lineTo(100, 370);
      ctx.moveTo(250, 290); ctx.lineTo(310, 360);
      ctx.stroke();
    }

    // Convert offscreen canvas to blob and run diagnostic
    canvas.toBlob((blob) => {
      const file = new File([blob], `${actionType}_sample.png`, { type: 'image/png' });
      this.processImageFile(file);
    }, 'image/png');
  }
}
