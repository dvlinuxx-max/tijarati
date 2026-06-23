// قائمة الجوال
const burger = document.getElementById('burger');
const navLinks = document.getElementById('navLinks');
burger.addEventListener('click', () => navLinks.classList.toggle('open'));
navLinks.querySelectorAll('a').forEach(a =>
  a.addEventListener('click', () => navLinks.classList.remove('open')));

// ظل شريط التنقل عند التمرير
const nav = document.getElementById('nav');
window.addEventListener('scroll', () => {
  nav.style.boxShadow = window.scrollY > 10 ? '0 6px 24px rgba(0,0,0,.4)' : 'none';
});

// نموذج الطلب (عرض توضيحي — يربط لاحقاً بخدمة بريد/واتساب)
const form = document.getElementById('orderForm');
const note = document.getElementById('formNote');
if (form) {
  form.addEventListener('submit', () => {
    const inputs = form.querySelectorAll('input[required]');
    let ok = true;
    inputs.forEach(i => { if (!i.value.trim()) ok = false; });
    if (!ok) { note.style.color = '#EF4444'; note.textContent = 'يرجى تعبئة الاسم ورقم الهاتف.'; return; }
    note.style.color = '#2ECC71';
    note.textContent = '✓ تم استلام طلبك! سنتواصل معك قريباً عبر الهاتف أو الواتساب.';
    form.reset();
    setTimeout(() => note.textContent = '', 6000);
  });
}

// ظهور تدريجي للعناصر عند التمرير
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.style.opacity = 1;
      e.target.style.transform = 'translateY(0)';
      io.unobserve(e.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('.feature, .plan, .screen, .faq details').forEach(el => {
  el.style.opacity = 0;
  el.style.transform = 'translateY(24px)';
  el.style.transition = 'opacity .6s ease, transform .6s ease';
  io.observe(el);
});
