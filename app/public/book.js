// Book of the Day functionality - dynamic single-book recommendation (via FastAPI)

let currentEmotion = 'neutral';
let currentImportantWords = [];
let currentBookData = null;

const PLACEHOLDER_IMAGE = 'placeholder-image-url-1.jpg'; // keeps existing displayBook fallback behavior
const FASTAPI_BASE_URL = 'http://127.0.0.1:8000';
const RECOMMEND_BOOK_ENDPOINT = `${FASTAPI_BASE_URL}/recommend-book`;

// Fetch the most recent emotion from the API
async function fetchMostRecentEmotion() {
    try {
        const response = await fetch('/api/emotion');
        if (!response.ok) {
            throw new Error('Failed to fetch emotion');
        }
        const data = await response.json();
        return data.emotion || 'neutral';
    } catch (error) {
        console.error('Error fetching emotion:', error);
        return 'neutral'; // Default to neutral on error
    }
}

function getSessionId() {
    return localStorage.getItem('chatSessionId') || 'default';
}

function getLastEmotionFromStorage(sessionId) {
    const raw = localStorage.getItem(`lastEmotion_${sessionId}`);
    if (typeof raw === 'string' && raw.trim()) {
        return raw.trim();
    }
    return '';
}

function getImportantWordsFromStorage(sessionId) {
    try {
        const raw = localStorage.getItem(`lastImportantWords_${sessionId}`);
        const parsed = raw ? JSON.parse(raw) : [];
        return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
        return [];
    }
}

function getSeenTitlesStorageKey(sessionId) {
    return `recommendedBookTitles_${sessionId}`;
}

function getSeenTitlesFromStorage(sessionId) {
    try {
        const raw = localStorage.getItem(getSeenTitlesStorageKey(sessionId));
        const parsed = raw ? JSON.parse(raw) : [];
        if (!Array.isArray(parsed)) {
            return [];
        }
        return parsed.filter(t => typeof t === 'string' && t.trim());
    } catch (e) {
        return [];
    }
}

function saveSeenTitleToStorage(sessionId, title) {
    if (!title || typeof title !== 'string' || !title.trim()) {
        return;
    }
    const current = getSeenTitlesFromStorage(sessionId);
    const normalized = title.trim().toLowerCase();
    const exists = current.some(t => t.trim().toLowerCase() === normalized);
    if (!exists) {
        current.push(title.trim());
    }
    // Keep bounded.
    localStorage.setItem(getSeenTitlesStorageKey(sessionId), JSON.stringify(current.slice(-20)));
}

async function fetchSingleBook(emotion, important_words) {
    const sessionId = getSessionId();
    const seenTitles = getSeenTitlesFromStorage(sessionId);
    const response = await fetch(RECOMMEND_BOOK_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            emotion: emotion || 'neutral',
            important_words: Array.isArray(important_words) ? important_words : [],
            session_id: sessionId,
            seen_titles: seenTitles
        })
    });
    if (!response.ok) {
        let details = '';
        try {
            const errJson = await response.json();
            if (errJson && errJson.detail) {
                details = ` - ${errJson.detail}`;
            }
        } catch (e) {}
        throw new Error(`Book recommendation API error: ${response.status}${details}`);
    }

    const data = await response.json();
    saveSeenTitleToStorage(sessionId, data.title);
    // Adapt backend response into the existing UI format.
    return {
        title: data.title,
        author: data.author,
        description: data.description || 'No description available',
        rating: typeof data.rating === 'number' ? data.rating : 4,
        tags: Array.isArray(data.tags) && data.tags.length ? data.tags : ['Mental Health', 'Self-Help'],
        reason: data.reason || `Recommended based on: ${emotion}`,
        icon: '📖',
        image: data.image || PLACEHOLDER_IMAGE
    };
}

function displayBook(bookData) {
    const { book, emotion } = bookData;
    
    document.getElementById('bookTitle').textContent = book.title;
    document.getElementById('bookAuthor').textContent = `by ${book.author}`;
    document.getElementById('bookDescription').textContent = book.description;
    document.getElementById('bookReason').textContent = book.reason;
    
    // Update book cover - if image exists, use it, otherwise use icon
    const coverEl = document.getElementById('bookCover');
    if (book.image && book.image !== 'placeholder-image-url-1.jpg') {
        coverEl.innerHTML = `<img src="${book.image}" alt="${book.title}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 8px;">`;
    } else {
        coverEl.textContent = book.icon;
        coverEl.style.fontSize = '4rem';
    }
    
    // Display rating
    const ratingEl = document.getElementById('bookRating');
    ratingEl.innerHTML = '';
    for (let i = 0; i < book.rating; i++) {
        const star = document.createElement('span');
        star.className = 'star';
        star.textContent = '⭐';
        ratingEl.appendChild(star);
    }
    
    // Display tags
    const tagsEl = document.getElementById('bookTags');
    tagsEl.innerHTML = '';
    book.tags.forEach(tag => {
        const tagEl = document.createElement('span');
        tagEl.className = 'book-tag';
        tagEl.textContent = tag;
        tagsEl.appendChild(tagEl);
    });
    
    // Update find book link
    const findBookBtn = document.getElementById('findBookBtn');
    findBookBtn.href = `https://www.google.com/search?q=${encodeURIComponent(book.title + ' ' + book.author)}`;
    
    // Show which emotion this recommendation is based on
    const emotionDisplay = document.querySelector('.emotion-badge-recommendation');
    if (emotionDisplay) {
        emotionDisplay.textContent = `Recommended based on: ${emotion.charAt(0).toUpperCase() + emotion.slice(1)}`;
    }
}

function setLoadingState(isLoading) {
    const refreshBtn = document.getElementById('refreshBookBtn');
    if (refreshBtn) {
        refreshBtn.disabled = isLoading;
        refreshBtn.style.opacity = isLoading ? '0.6' : '1';
    }

    if (isLoading) {
        document.getElementById('bookTitle').textContent = 'Loading...';
        document.getElementById('bookAuthor').textContent = 'Loading...';
        document.getElementById('bookDescription').textContent = 'Loading book recommendation...';
        document.getElementById('bookReason').textContent = 'Finding a relevant book for you...';
        document.getElementById('bookRating').innerHTML = '';
        document.getElementById('bookTags').innerHTML = '';
        const coverEl = document.getElementById('bookCover');
        if (coverEl) {
            coverEl.textContent = '📖';
            coverEl.style.fontSize = '4rem';
        }
    }
}

async function loadRecommendation() {
    setLoadingState(true);
    try {
        const sessionId = getSessionId();
        // Prefer the latest chat emotion saved by the chat page; fall back to Node's /api/emotion bucket.
        currentEmotion = getLastEmotionFromStorage(sessionId) || await fetchMostRecentEmotion();
        currentImportantWords = getImportantWordsFromStorage(sessionId);

        const book = await fetchSingleBook(currentEmotion, currentImportantWords);
        currentBookData = { book, emotion: currentEmotion, index: 0 };
        displayBook(currentBookData);
    } catch (error) {
        console.error('Error loading book recommendation:', error);
        // Keep UI stable with a graceful fallback single-book object.
        const fallbackBook = {
            title: 'Unable to fetch a book right now',
            author: 'Please try again',
            description: 'No description available',
            rating: 4,
            tags: ['Mental Health', 'Self-Help'],
            reason: `Recommended based on: ${currentEmotion}`,
            icon: '📖',
            image: PLACEHOLDER_IMAGE
        };
        currentBookData = { book: fallbackBook, emotion: currentEmotion, index: 0 };
        displayBook(currentBookData);
    } finally {
        setLoadingState(false);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadRecommendation();

    // Refresh button - fetches a new dynamic recommendation
    document.getElementById('refreshBookBtn').addEventListener('click', loadRecommendation);
    
    // Add emotion badge to show why this book was recommended
    const bookDetails = document.querySelector('.book-details');
    if (bookDetails && !document.querySelector('.emotion-badge-recommendation')) {
        const emotionBadge = document.createElement('div');
        emotionBadge.className = 'emotion-badge-recommendation';
        emotionBadge.style.cssText = 'margin-top: 1rem; padding: 0.5rem 1rem; background: var(--surface-light); border-radius: 8px; color: var(--text-secondary); font-size: 0.875rem;';
        emotionBadge.textContent = `Recommended based on: ${currentEmotion.charAt(0).toUpperCase() + currentEmotion.slice(1)}`;
        bookDetails.appendChild(emotionBadge);
    }
});
