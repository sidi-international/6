let currentCard = null;
let currentPhotoId = null;
let startX = 0;
let startY = 0;
let currentX = 0;
let currentY = 0;
let isDragging = false;
let selectedBodyPart = null;
let pendingSwipeDirection = null;

// Carica la prima carta all'avvio
document.addEventListener('DOMContentLoaded', function() {
    loadNextHand();
});

// Carica la prossima mano
async function loadNextHand() {
    try {
        const response = await fetch('/api/next_hand');

        if (response.status === 404) {
            // Non ci sono più mani
            document.getElementById('cardStack').innerHTML = `
                <div class="no-more-cards">
                    <h2>😊 Non ci sono altre mani al momento</h2>
                    <p>Torna più tardi per vedere nuovi profili!</p>
                    <a href="/profile" class="btn btn-light mt-3">Vai al profilo</a>
                </div>
            `;
            return;
        }

        const data = await response.json();
        createCard(data);
    } catch (error) {
        console.error('Errore nel caricamento:', error);
    }
}

// Crea una carta
function createCard(data) {
    currentPhotoId = data.id;

    const cardStack = document.getElementById('cardStack');
    cardStack.innerHTML = '';

    const card = document.createElement('div');
    card.className = 'swipe-card';
    card.innerHTML = `
        <div class="like-overlay">LIKE</div>
        <div class="nope-overlay">NOPE</div>
        <img src="${data.photo_path}" alt="Hand photo">
        <div class="card-content">
            <p class="card-description">${data.description || 'Una bella mano...'}</p>
        </div>
    `;

    cardStack.appendChild(card);
    currentCard = card;

    // Aggiungi event listeners per il drag
    card.addEventListener('mousedown', handleDragStart);
    card.addEventListener('touchstart', handleDragStart);
}

// Gestione inizio drag
function handleDragStart(e) {
    if (e.type === 'mousedown') {
        startX = e.clientX;
        startY = e.clientY;
    } else {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
    }

    isDragging = true;

    document.addEventListener('mousemove', handleDragMove);
    document.addEventListener('touchmove', handleDragMove);
    document.addEventListener('mouseup', handleDragEnd);
    document.addEventListener('touchend', handleDragEnd);
}

// Gestione movimento drag
function handleDragMove(e) {
    if (!isDragging) return;

    if (e.type === 'mousemove') {
        currentX = e.clientX - startX;
        currentY = e.clientY - startY;
    } else {
        currentX = e.touches[0].clientX - startX;
        currentY = e.touches[0].clientY - startY;
    }

    const rotation = currentX / 20;

    currentCard.style.transform = `translate(${currentX}px, ${currentY}px) rotate(${rotation}deg)`;

    // Mostra overlay in base alla direzione
    const likeOverlay = currentCard.querySelector('.like-overlay');
    const nopeOverlay = currentCard.querySelector('.nope-overlay');

    if (currentX > 50) {
        likeOverlay.style.opacity = Math.min(currentX / 100, 1);
        nopeOverlay.style.opacity = 0;
    } else if (currentX < -50) {
        nopeOverlay.style.opacity = Math.min(Math.abs(currentX) / 100, 1);
        likeOverlay.style.opacity = 0;
    } else {
        likeOverlay.style.opacity = 0;
        nopeOverlay.style.opacity = 0;
    }
}

// Gestione fine drag
function handleDragEnd(e) {
    if (!isDragging) return;

    isDragging = false;

    document.removeEventListener('mousemove', handleDragMove);
    document.removeEventListener('touchmove', handleDragMove);
    document.removeEventListener('mouseup', handleDragEnd);
    document.removeEventListener('touchend', handleDragEnd);

    const threshold = 100;

    if (currentX > threshold) {
        // Swipe right (like)
        animateSwipe('right');
    } else if (currentX < -threshold) {
        // Swipe left (dislike)
        animateSwipe('left');
    } else {
        // Reset posizione
        currentCard.style.transform = '';
        currentCard.querySelector('.like-overlay').style.opacity = 0;
        currentCard.querySelector('.nope-overlay').style.opacity = 0;
    }

    currentX = 0;
    currentY = 0;
}

// Anima lo swipe
function animateSwipe(direction) {
    const moveX = direction === 'right' ? 1000 : -1000;
    const rotation = direction === 'right' ? 45 : -45;

    currentCard.style.transition = 'transform 0.5s ease';
    currentCard.style.transform = `translate(${moveX}px, ${currentY}px) rotate(${rotation}deg)`;

    setTimeout(() => {
        if (direction === 'right') {
            // Per i like, mostra il modal per la selezione della parte del corpo
            pendingSwipeDirection = direction;
            showBodyPartModal();
        } else {
            // Per i dislike, salva direttamente
            saveSwipe(direction, null);
        }
    }, 500);
}

// Mostra il modal per la selezione della parte del corpo
function showBodyPartModal() {
    document.getElementById('bodyPartModal').style.display = 'flex';
}

// Seleziona una parte del corpo
function selectBodyPart(bodyPart) {
    selectedBodyPart = bodyPart;
    document.getElementById('bodyPartModal').style.display = 'none';

    // Salva lo swipe con la preferenza
    saveSwipe(pendingSwipeDirection, selectedBodyPart);

    selectedBodyPart = null;
    pendingSwipeDirection = null;
}

// Salva lo swipe
async function saveSwipe(direction, bodyPart) {
    try {
        const response = await fetch('/api/swipe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                photo_id: currentPhotoId,
                direction: direction,
                body_part: bodyPart
            })
        });

        const data = await response.json();

        // Controlla se c'è un match
        if (data.match) {
            showMatchModal(data);
        }

        // Carica la prossima carta
        setTimeout(() => {
            loadNextHand();
        }, 300);

    } catch (error) {
        console.error('Errore nel salvataggio:', error);
        loadNextHand();
    }
}

// Mostra il modal del match
function showMatchModal(data) {
    const modal = document.getElementById('matchModal');
    document.getElementById('matchUsername').textContent = data.username;

    let preferenceText = `Vuoi vedere: ${data.your_preference}`;
    if (data.their_preference) {
        preferenceText += `\nLui/lei vuole vedere: ${data.their_preference}`;
    }
    document.getElementById('matchPreference').innerHTML = preferenceText.replace(/\n/g, '<br>');

    modal.style.display = 'flex';
}

// Chiudi il modal del match
function closeMatchModal() {
    document.getElementById('matchModal').style.display = 'none';
}

// Swipe programmato dai pulsanti
function swipe(direction) {
    if (!currentCard) return;

    const moveX = direction === 'right' ? 1000 : -1000;
    const rotation = direction === 'right' ? 45 : -45;

    // Mostra overlay
    if (direction === 'right') {
        currentCard.querySelector('.like-overlay').style.opacity = 1;
    } else {
        currentCard.querySelector('.nope-overlay').style.opacity = 1;
    }

    currentCard.style.transition = 'transform 0.5s ease';
    currentCard.style.transform = `translate(${moveX}px, 0px) rotate(${rotation}deg)`;

    setTimeout(() => {
        if (direction === 'right') {
            // Per i like, mostra il modal
            pendingSwipeDirection = direction;
            showBodyPartModal();
        } else {
            // Per i dislike, salva direttamente
            saveSwipe(direction, null);
        }
    }, 500);
}
