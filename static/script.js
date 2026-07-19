document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('navMenu');
    hamburger?.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('open');
    });
    navMenu?.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('active');
            navMenu.classList.remove('open');
        });
    });

    // Carousel functionality
    const carouselInner = document.getElementById('carouselInner');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    let currentIndex = 0;
    let items = [];

    async function loadCarouselImages() {
        const res = await fetch('/api/carrousel/list');
        const files = await res.json();
        carouselInner.innerHTML = files.map(f =>
            `<div class="carousel-item">
                <img src="/static/image carrousel/${encodeURIComponent(f.filename)}" alt="${f.filename}">
            </div>`
        ).join('');
        items = carouselInner.querySelectorAll('.carousel-item');
        currentIndex = 0;
        updateCarousel();
    }

    function updateCarousel() {
        if (!items.length) return;
        carouselInner.style.transform = `translateX(-${currentIndex * 100}%)`;
    }

    if (carouselInner) loadCarouselImages();

    prevBtn?.addEventListener('click', () => {
        if (!items.length) return;
        currentIndex = (currentIndex - 1 + items.length) % items.length;
        updateCarousel();
    });

    nextBtn?.addEventListener('click', () => {
        if (!items.length) return;
        currentIndex = (currentIndex + 1) % items.length;
        updateCarousel();
    });

    setInterval(() => {
        if (!items.length) return;
        currentIndex = (currentIndex + 1) % items.length;
        updateCarousel();
    }, 5000);

    const form = document.querySelector('form');

    if (form) {
        form.addEventListener('submit', async function(event) {
            event.preventDefault();

            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const phone = document.getElementById('phone').value.trim();
            const message = document.getElementById('message').value.trim();

            if (!name || !email || !message) {
                alert('Veuillez remplir tous les champs.');
                return;
            }

            const btn = form.querySelector('.btn-primary');
            btn.textContent = 'Envoi en cours...';
            btn.disabled = true;

            try {
                const res = await fetch('/api/contact', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name, email, phone, message})
                });
                const data = await res.json();
                if (data.success) {
                    alert(`Merci ${name} ! Votre message a bien été envoyé. Nous vous répondrons sous 24h ouvrées.`);
                    form.reset();
                }
            } catch (e) {
                alert('Une erreur est survenue. Veuillez réessayer.');
            } finally {
                btn.textContent = 'Envoyer';
                btn.disabled = false;
            }
        });
    }

    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    const toggle = document.getElementById('chatbotToggle');
    const chatbox = document.getElementById('chatbotWindow');
    const close = document.getElementById('chatbotClose');
    const input = document.getElementById('chatbotInput');
    const send = document.getElementById('chatbotSend');
    const messages = document.getElementById('chatbotMessages');

    if (toggle && chatbox) {
        toggle.addEventListener('click', () => {
            chatbox.classList.toggle('open');
            if (chatbox.classList.contains('open')) {
                input.focus();
                messages.scrollTop = messages.scrollHeight;
            }
        });
        close.addEventListener('click', () => chatbox.classList.remove('open'));
    }

    document.getElementById('heroChatBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        chatbox?.classList.add('open');
        input?.focus();
        if (messages) messages.scrollTop = messages.scrollHeight;
    });

    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;
        input.value = '';

        const userDiv = document.createElement('div');
        userDiv.className = 'chatbot-msg user';
        userDiv.textContent = text;
        messages.appendChild(userDiv);

        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'chatbot-msg loading';
        loadingDiv.textContent = 'Réflexion en cours...';
        messages.appendChild(loadingDiv);
        messages.scrollTop = messages.scrollHeight;

        try {
            const res = await fetch('/api/rag', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: text})
            });
            const data = await res.json();
            loadingDiv.remove();
            const botDiv = document.createElement('div');
            botDiv.className = 'chatbot-msg bot';
            botDiv.textContent = data.answer;
            messages.appendChild(botDiv);
        } catch (e) {
            loadingDiv.remove();
            const errDiv = document.createElement('div');
            errDiv.className = 'chatbot-msg bot';
            errDiv.textContent = 'Désolé, une erreur est survenue. Veuillez réessayer.';
            messages.appendChild(errDiv);
        }
        messages.scrollTop = messages.scrollHeight;
    }

    if (send && input) {
        send.addEventListener('click', sendMessage);
        input.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMessage(); });
    }
});