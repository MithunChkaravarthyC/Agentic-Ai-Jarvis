// Get all the sections
const sections = document.querySelectorAll('section');

// Add event listeners to the buttons
document.getElementById('learn-more-btn').addEventListener('click', () => {
    // Add some animation to the learn more button
    gsap.to('#learn-more-btn', {
        scale: 1.1,
        duration: 0.5,
        ease: 'ease-out'
    });
});

document.getElementById('view-menu-btn').addEventListener('click', () => {
    // Add some animation to the view menu button
    gsap.to('#view-menu-btn', {
        scale: 1.1,
        duration: 0.5,
        ease: 'ease-out'
    });
});

document.getElementById('send-message-btn').addEventListener('click', () => {
    // Add some animation to the send message button
    gsap.to('#send-message-btn', {
        scale: 1.1,
        duration: 0.5,
        ease: 'ease-out'
    });
});

// Add event listeners to the sections
sections.forEach((section) => {
    section.addEventListener('click', (e) => {
        if (e.target.tagName === 'H1') {
            // Add some animation to the section
            gsap.to(section, {
                scale: 1.1,
                duration: 0.5,
                ease: 'ease-out'
            });
        }
    });
});