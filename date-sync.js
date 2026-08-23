'use strict';

(() => {
  let sourceDate = null;
  let initialized = false;

  function parseSourceDate() {
    const text = document.getElementById('updatedAt')?.textContent?.trim() || '';
    const datePart = text.split(' ')[0] || '';
    const pieces = datePart.split('/');
    if (pieces.length !== 3) return null;
    const [day, month, year] = pieces;
    if (!day || !month || !year || year.length !== 4) return null;
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
  }

  function applySourcePeriod() {
    if (!sourceDate) return false;
    const from = document.getElementById('from');
    const to = document.getElementById('to');
    if (!from || !to) return false;

    const year = sourceDate.slice(0, 4);
    const desiredFrom = `${year}-01-01`;
    let changed = false;

    if (from.value !== desiredFrom) {
      from.value = desiredFrom;
      changed = true;
    }
    if (to.value !== sourceDate) {
      to.value = sourceDate;
      changed = true;
    }

    if (changed) to.dispatchEvent(new Event('change', { bubbles: true }));
    return changed;
  }

  function captureAndInitialize() {
    const parsed = parseSourceDate();
    if (!parsed) return;
    sourceDate = parsed;
    if (!initialized) {
      initialized = true;
      applySourcePeriod();
    }
  }

  window.addEventListener('DOMContentLoaded', () => {
    const updatedAt = document.getElementById('updatedAt');
    if (!updatedAt) return;

    const observer = new MutationObserver(captureAndInitialize);
    observer.observe(updatedAt, { childList: true, subtree: true, characterData: true });
    captureAndInitialize();

    const reset = document.getElementById('reset');
    if (reset) {
      reset.addEventListener('click', () => {
        setTimeout(() => applySourcePeriod(), 0);
      });
    }
  });
})();
