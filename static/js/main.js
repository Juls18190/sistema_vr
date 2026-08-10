/* ============================================================
   LIGHTBOX DE IMÁGENES — reutilizable para todas las vacantes
   (Landing y /vacantes, principal y secundarias, todas las categorías)
   Acepta un arreglo de URLs para soportar galería a futuro
   (hoy cada vacante tiene una sola imagen, pero la lógica ya
   queda lista para cuando el modelo permita varias).
   ============================================================ */
var _lbImagenes = [];
var _lbIndex = 0;

function abrirLightbox(urls, indiceInicial) {
  if (!urls) return;
  _lbImagenes = Array.isArray(urls) ? urls.filter(Boolean) : [urls];
  if (!_lbImagenes.length) return;
  _lbIndex = indiceInicial || 0;

  var lb = document.getElementById('vacLightbox');
  if (!lb) return;
  _lbRender();
  lb.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function _lbRender() {
  var img = document.getElementById('vacLightboxImg');
  var nav = document.getElementById('vacLightboxNav');
  if (!img) return;
  img.src = _lbImagenes[_lbIndex];
  if (nav) nav.style.display = _lbImagenes.length > 1 ? 'flex' : 'none';
}

function lightboxSiguiente(dir) {
  if (_lbImagenes.length < 2) return;
  _lbIndex = (_lbIndex + dir + _lbImagenes.length) % _lbImagenes.length;
  _lbRender();
}

function cerrarLightbox() {
  var lb = document.getElementById('vacLightbox');
  if (!lb) return;
  lb.classList.remove('open');
  document.body.style.overflow = '';
}

document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') cerrarLightbox();
  if (e.key === 'ArrowRight') lightboxSiguiente(1);
  if (e.key === 'ArrowLeft') lightboxSiguiente(-1);
});