// Navigation functionality
document.addEventListener('DOMContentLoaded', () => {
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (navToggle) {
        navToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', (e) => {
        if (navLinks && navToggle && 
            !navLinks.contains(e.target) && 
            !navToggle.contains(e.target) &&
            navLinks.classList.contains('active')) {
            navLinks.classList.remove('active');
        }
    });
    
    // Highlight active nav link based on current page
    const currentPath = window.location.pathname;
    const navLinksList = document.querySelectorAll('.nav-link');
    
    navLinksList.forEach(link => {
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPath || 
            (currentPath === '/' && linkPath === '/') ||
            (currentPath === '/chat' && linkPath === '/chat') ||
            (currentPath === '/book' && linkPath === '/book') ||
            (currentPath === '/exercise' && linkPath === '/exercise')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
});






