// Exercise of the Day functionality - Emotion-based recommendations

// Exercise database organized by emotion
// Each emotion has ONE placeholder exercise that you can fill in later
const exercisesByEmotion = {
    'neutral': {
    title: "5-Minute Mindful Check-In",
    category: "Mindfulness",
    icon: "🧘",
    duration: "5 minutes",
    description: "A grounding exercise that helps you check in with your body, thoughts, and surroundings to maintain emotional balance.",
    gif: "exercisegifs/neutral.gif",
    steps: [
        "Sit comfortably and take a slow, deep breath.",
        "Bring attention to your body—notice any tension or relaxation.",
        "Acknowledge your current thoughts without judgment.",
        "Observe the sounds, sensations, and environment around you."
    ],
    benefits: [
        "Improves self-awareness",
        "Promotes calm and clarity",
        "Enhances emotional balance"
    ],
    tips: [
        "Try doing this between tasks for a mental reset.",
        "Keep your breathing slow and steady."
    ]
}
,
    'joy': {
    title: "Gratitude Reflection",
    category: "Positivity",
    icon: "🌞",
    duration: "3–5 minutes",
    description: "A joyful exercise that deepens positive emotions by reflecting on things you appreciate.",
    gif: "exercisegifs/joy.gif",
    steps: [
        "Find a comfortable spot and take a deep breath.",
        "Think of three things that made you smile today.",
        "Write down why each one matters to you.",
        "Take a moment to feel that warmth in your chest."
    ],
    benefits: [
        "Boosts mood and positivity",
        "Strengthens emotional resilience",
        "Builds long-term happiness habits"
    ],
    tips: [
        "Focus on small, everyday moments.",
        "Try sharing one of your gratitudes with someone."
    ]
}
,
    'sadness': {
    title: "5-4-3-2-1 Grounding Technique",
    category: "Grounding",
    icon: "🌦️",
    duration: "2–4 minutes",
    description: "A soothing grounding method that helps you reconnect to the present moment during emotional heaviness.",
    gif: "exercisegifs/sadness.gif",
    steps: [
        "Name 5 things you can see around you.",
        "Name 4 things you can touch right now.",
        "Name 3 things you can hear.",
        "Name 2 things you can smell.",
        "Name 1 thing you can taste."
    ],
    benefits: [
        "Reduces overwhelming emotions",
        "Creates a sense of safety",
        "Helps refocus your mind"
    ],
    tips: [
        "Speak the steps out loud for stronger grounding.",
        "Move slowly and intentionally through each sense."
    ]
}
,
    'fear': {
    title: "4-7-8 Breathing",
    category: "Breathwork",
    icon: "🌙",
    duration: "3 minutes",
    description: "A calming breathing pattern designed to lower anxiety and steady your nervous system.",
    gif: "exercisegifs/fear.gif",
    steps: [
        "Inhale quietly through your nose for 4 seconds.",
        "Hold the breath for 7 seconds.",
        "Exhale slowly through your mouth for 8 seconds.",
        "Repeat the cycle 4–6 times."
    ],
    benefits: [
        "Reduces anxiety and tension",
        "Slows heart rate",
        "Promotes relaxation"
    ],
    tips: [
        "Keep your shoulders relaxed during breathing.",
        "Use this before stressful conversations or events."
    ]
}
,
    'anger': {
    title: "Box Breathing",
    category: "Anger Regulation",
    icon: "🔥",
    duration: "2–3 minutes",
    description: "A structured breathing exercise that helps release tension and regain emotional control when anger rises.",
    gif: "exercisegifs/anger.gif",
    steps: [
        "Inhale through your nose for 4 seconds.",
        "Hold your breath for 4 seconds.",
        "Exhale through your mouth for 4 seconds.",
        "Hold again for 4 seconds.",
        "Repeat for 4–5 rounds."
    ],
    benefits: [
        "Lowers physical symptoms of anger",
        "Enhances emotional control",
        "Improves focus and clarity"
    ],
    tips: [
        "Try matching your breath to a visual square.",
        "Relax your jaw and hands to release tension."
    ]
}

};

let currentEmotion = 'neutral';
let timerInterval = null;
let timerSeconds = 0;
let isTimerRunning = false;
let isTimerPaused = false;

// Fetch the most recent emotion from the API
function fetchMostRecentEmotion() {
    const emotion = localStorage.getItem("safe_emotion");

    console.log("Exercise emotion (from localStorage):", emotion);

    return emotion || 'neutral';
}

// Get exercise based on emotion
function getExerciseForEmotion(emotion) {
    return exercisesByEmotion[emotion] || exercisesByEmotion['neutral'];
}

function displayExercise(exercise, emotion) {
    document.getElementById('exerciseTitle').textContent = exercise.title;
    document.getElementById('exerciseCategory').textContent = exercise.category;
    document.getElementById('exerciseIcon').textContent = exercise.icon;
    document.getElementById('exerciseDuration').textContent = exercise.duration;
    document.getElementById('exerciseDescription').textContent = exercise.description;
    
    // Display gif or placeholder
    const gifContainer = document.getElementById('exerciseGif');
    if (exercise.gif && exercise.gif !== 'placeholder-gif-url-neutral.gif') {
        gifContainer.innerHTML = `<img src="${exercise.gif}" alt="${exercise.title}" style="width: 100%; height: auto; border-radius: 8px; margin-bottom: 1rem;">`;
    } else {
        gifContainer.innerHTML = `<div style="width: 100%; height: 200px; background: var(--surface-light); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--text-muted); margin-bottom: 1rem; border: 2px dashed var(--border);">
            <div style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">${exercise.icon}</div>
                <div>GIF Placeholder</div>
            </div>
        </div>`;
    }
    
    // Display steps
    const stepsEl = document.getElementById('exerciseSteps');
    stepsEl.innerHTML = '';
    exercise.steps.forEach((step, index) => {
        const li = document.createElement('li');
        li.textContent = step;
        stepsEl.appendChild(li);
    });
    
    // Display benefits
    const benefitsEl = document.getElementById('exerciseBenefits');
    benefitsEl.innerHTML = '';
    exercise.benefits.forEach(benefit => {
        const li = document.createElement('li');
        li.textContent = benefit;
        benefitsEl.appendChild(li);
    });
    
    // Display tips
    const tipsEl = document.getElementById('exerciseTips');
    tipsEl.innerHTML = '';
    exercise.tips.forEach(tip => {
        const li = document.createElement('li');
        li.textContent = tip;
        tipsEl.appendChild(li);
    });
    
    // Update or create emotion badge
    let emotionBadge = document.querySelector('.emotion-badge-exercise');
    if (!emotionBadge) {
        emotionBadge = document.createElement('div');
        emotionBadge.className = 'emotion-badge-exercise';
        emotionBadge.style.cssText = 'padding: 0.5rem 1rem; background: var(--surface-light); border-radius: 8px; color: var(--text-secondary); font-size: 0.875rem; text-align: center;';
        const exerciseDetails = document.querySelector('.exercise-details');
        if (exerciseDetails) {
            exerciseDetails.appendChild(emotionBadge);
        }
    }
    emotionBadge.textContent = `Recommended based on: ${emotion.charAt(0).toUpperCase() + emotion.slice(1)}`;
}

function startTimer(durationMinutes = 5) {
    timerSeconds = durationMinutes * 60;
    isTimerRunning = true;
    isTimerPaused = false;
    document.getElementById('exerciseTimer').style.display = 'block';
    
    timerInterval = setInterval(() => {
        if (!isTimerPaused) {
            timerSeconds--;
            updateTimerDisplay();
            
            if (timerSeconds <= 0) {
                stopTimer();
                alert('Time\'s up! Great job completing the exercise.');
            }
        }
    }, 1000);
}

function pauseTimer() {
    isTimerPaused = !isTimerPaused;
    const btn = document.getElementById('pauseTimerBtn');
    btn.textContent = isTimerPaused ? 'Resume' : 'Pause';
}

function stopTimer() {
    clearInterval(timerInterval);
    timerInterval = null;
    isTimerRunning = false;
    isTimerPaused = false;
    document.getElementById('exerciseTimer').style.display = 'none';
    document.getElementById('pauseTimerBtn').textContent = 'Pause';
    timerSeconds = 0;
}

function updateTimerDisplay() {
    const minutes = Math.floor(timerSeconds / 60);
    const seconds = timerSeconds % 60;
    document.getElementById('timerMinutes').textContent = String(minutes).padStart(2, '0');
    document.getElementById('timerSeconds').textContent = String(seconds).padStart(2, '0');
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Fetch the most recent emotion
    currentEmotion = await fetchMostRecentEmotion();
    console.log('Most recent emotion for exercise:', currentEmotion);
    
    // Get and display exercise for this emotion
    const exercise = getExerciseForEmotion(currentEmotion);
    displayExercise(exercise, currentEmotion);
    
    // Event listeners
    document.getElementById('startExerciseBtn').addEventListener('click', () => {
        const duration = parseInt(prompt('How many minutes? (default: 5)', '5') || '5');
        startTimer(duration);
    });
    
    document.getElementById('newExerciseBtn').addEventListener('click', async () => {
        // Fetch fresh emotion and reload exercise
        currentEmotion = await fetchMostRecentEmotion();
        const exercise = getExerciseForEmotion(currentEmotion);
        displayExercise(exercise, currentEmotion);
    });
    
    document.getElementById('pauseTimerBtn').addEventListener('click', pauseTimer);
    document.getElementById('stopTimerBtn').addEventListener('click', stopTimer);
});
