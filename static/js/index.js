function setActiveTab(el) {
    const tab = el.dataset.tab;

    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('tab-btn--active'));
    el.classList.add('tab-btn--active');

    document.querySelectorAll('.feature-panel-wrap').forEach(panel => {
        panel.classList.toggle('feature-panel-wrap--hidden', panel.dataset.panel !== tab);
    });
}
