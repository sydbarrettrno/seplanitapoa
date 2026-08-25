(() => {
  function applyInstitutionalHeader() {
    const brand = document.querySelector('.brand');
    if (!brand || brand.dataset.institutional === '1') return;
    brand.dataset.institutional = '1';
    brand.innerHTML = `
      <img class="municipio-brand-logo" src="/assets/logo-municipio-itapoa.png" alt="Município de Itapoá">
      <div class="seplan-brand">
        <strong>SEPLAN</strong>
        <small>Secretaria de Planejamento Urbano</small>
      </div>`;
  }

  applyInstitutionalHeader();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyInstitutionalHeader, { once: true });
  }
})();
