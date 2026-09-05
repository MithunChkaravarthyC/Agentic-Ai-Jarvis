// Get the kanban board container
const kanbanBoard = document.getElementById('kanban-board');

// Initialize the columns
const todoColumn = document.getElementById('todo-column');
const doingColumn = document.getElementById('doing-column');
const doneColumn = document.getElementById('done-column');

// Initialize the card container
const cardContainer = document.getElementById('cards');

// Initialize the card array
let cards = [];

// Function to create a new card
function createCard(text) {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = text;
    cardContainer.appendChild(card);

    // Initialize the card's position
    card.style.top = '0px';
    card.style.left = '0px';

    // Add the drag handle
    const dragHandle = document.createElement('span');
    dragHandle.className = 'drag-handle';
    card.appendChild(dragHandle);

    // Initialize the card's position
    cards.push(card);
}

// Function to move a card to a new column
function moveCard(card, newColumn) {
    // Remove the card from its current column
    card.parentNode.removeChild(card);

    // Add the card to the new column
    newColumn.appendChild(card);

    // Update the card's position
    card.style.top = '0px';
    card.style.left = '0px';
}

// Function to handle drag events
function handleDrag(event) {
    // Get the card being dragged
    const card = event.target;

    // Update the card's position
    card.style.top = event.clientY + 'px';
    card.style.left = event.clientX + 'px';
}

// Function to handle drop events
function handleDrop(event) {
    // Get the card being dropped
    const card = event.dataTransfer.getData('text');

    // Get the new column
    const newColumn = event.target.parentNode;

    // Move the card to the new column
    moveCard(card, newColumn);
}

// Add event listeners for drag and drop
kanbanBoard.addEventListener('dragstart', handleDrag);
cardContainer.addEventListener('dragover', handleDrag);
cardContainer.addEventListener('drop', handleDrop);

// Create some sample cards
createCard('Card 1');
createCard('Card 2');
createCard('Card 3');

// Initialize the columns
todoColumn.addEventListener('drop', handleDrop);
doingColumn.addEventListener('drop', handleDrop);
doneColumn.addEventListener('drop', handleDrop);