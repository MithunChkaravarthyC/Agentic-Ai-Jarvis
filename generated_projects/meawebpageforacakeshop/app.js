// Get the elements
const headerNav = document.querySelector('header nav ul');
const productsList = document.querySelector('#products ul');
const imagesList = document.querySelector('#images ul');

// Add event listener to toggle products list
productsList.addEventListener('click', function(event) {
    if (event.target.tagName === 'LI') {
        const product = event.target.textContent;
        // Add JavaScript functionality here if needed
    }
});

// Add event listener to toggle images list
imagesList.addEventListener('click', function(event) {
    if (event.target.tagName === 'LI') {
        const image = event.target.querySelector('img').src;
        // Add JavaScript functionality here if needed
    }
});