/**
 * 15-Class HAR Catalog & Pipeline Visualizer Module
 * Connects with backend /api/dataset/classes and renders interactive cards and filters.
 */

export class DatasetView {
  constructor() {
    this.filterBar = document.getElementById('category-filter-bar');
    this.cardsGrid = document.getElementById('classes-grid-container');
    this.classesData = [];
    this.categoriesData = {};
    this.metadataMap = {};
    this.activeFilter = 'All';

    this.loadCatalog();
  }

  async loadCatalog() {
    try {
      const res = await fetch('/api/dataset/classes');
      const data = await res.json();
      this.classesData = data.classes || [];
      this.categoriesData = data.categories || {};
      this.metadataMap = data.metadata || {};

      this.renderFilterBar();
      this.renderClassCards();
    } catch (err) {
      console.error('Failed to load dataset classes:', err);
      this.cardsGrid.innerHTML = '<div style="color: var(--text-muted);">Failed to load classes catalog.</div>';
    }
  }

  renderFilterBar() {
    const categories = ['All', ...Object.keys(this.categoriesData)];
    
    this.filterBar.innerHTML = categories.map(cat => {
      const count = cat === 'All' ? this.classesData.length : (this.categoriesData[cat] || []).length;
      const isActive = cat === this.activeFilter ? 'active' : '';
      return `
        <button class="filter-chip-btn ${isActive}" data-category="${cat}">
          ${cat} (${count})
        </button>
      `;
    }).join('');

    const buttons = this.filterBar.querySelectorAll('.filter-chip-btn');
    buttons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        buttons.forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        this.activeFilter = e.target.getAttribute('data-category');
        this.renderClassCards();
      });
    });
  }

  renderClassCards() {
    let filtered = this.classesData;
    if (this.activeFilter !== 'All') {
      const validInCat = new Set(this.categoriesData[this.activeFilter] || []);
      filtered = this.classesData.filter(cls => validInCat.has(cls));
    }

    this.cardsGrid.innerHTML = filtered.map(clsName => {
      const meta = this.metadataMap[clsName] || {};
      const color = meta.color || '#00f2fe';
      const objects = meta.associated_objects || [];
      const cues = meta.posture_cues || [];

      return `
        <article class="class-catalog-card" style="border-top: 3px solid ${color};">
          <div class="class-card-top">
            <div class="class-card-title-group">
              <div class="class-card-icon-box" style="background: ${color}22; color: ${color};">
                ${this.getActionEmoji(clsName)}
              </div>
              <div>
                <h3 class="class-card-name">${meta.name || clsName}</h3>
                <span class="class-category-tag">${meta.category || 'General'}</span>
              </div>
            </div>
          </div>

          <p class="class-desc-text">${meta.description || 'Action behavior recognition profile.'}</p>

          <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 0.25rem;">
            <strong>Key Cues:</strong> ${cues.join(' • ') || 'General silhouette'}
          </div>

          <div class="class-card-footer">
            ${objects.map(obj => `<span class="class-obj-tag">📦 ${obj}</span>`).join('')}
          </div>
        </article>
      `;
    }).join('');
  }

  getActionEmoji(actionName) {
    const emojiMap = {
      calling: '📞',
      clapping: '👏',
      cycling: '🚴',
      dancing: '💃',
      drinking: '☕',
      eating: '🍽️',
      fighting: '🥊',
      hugging: '🫂',
      laughing: '😄',
      listeningtomusic: '🎧',
      running: '🏃',
      sitting: '🪑',
      sleeping: '💤',
      texting: '📱',
      using_laptop: '💻'
    };
    return emojiMap[actionName] || '🎯';
  }
}
