(function(){
  // Simple thumbnail handler for Yandex-like cards
  function onThumbClick(ev){
    const btn = ev.target.closest('.thumb-btn');
    if(!btn) return;
    try{
      const src = btn.getAttribute('data-src');
      const card = btn.closest('.menu-item-card');
      if(!card) return;
      const main = card.querySelector('.main-image');
      if(main && src){
        main.src = src;
        // update active thumb
        const siblings = card.querySelectorAll('.thumb-btn');
        siblings.forEach(s => s.classList.toggle('active', s === btn));
      }
    }catch(e){console.warn('yandex-cards thumb click', e)}
  }

  function init(){
    document.addEventListener('click', onThumbClick, true);
    // ensure default active thumb is set (first) on DOM ready
    document.querySelectorAll('.menu-item-card').forEach(card => {
      const thumbs = card.querySelectorAll('.thumb-btn');
      if(thumbs && thumbs.length){
        thumbs[0].classList.add('active');
      }
    });
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
