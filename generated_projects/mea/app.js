// Set the hotel details
const hotelName = "The Grand Plaza";
const location = "New York, USA";
const amenities = ["Fitness Center", "Sauna and Steam Room", "Swimming Pool", "Restaurant and Bar"];

// Set the available rooms
const rooms = [
    {
        name: "Deluxe Room",
        description: "King-size bed, city view, and luxurious amenities",
        price: 150
    },
    {
        name: "Standard Room",
        description: "Double bed, comfortable amenities, and a great view",
        price: 100
    }
];

// Set the booking form fields
const checkInField = document.getElementById("check-in");
const checkOutField = document.getElementById("check-out");

// Add event listener to the booking form
document.querySelector("form").addEventListener("submit", (e) => {
    e.preventDefault();
    // Get the booking details
    const checkIn = checkInField.value;
    const checkOut = checkOutField.value;
    // Send the booking request to the server
    fetch("/book", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ checkIn, checkOut }),
    });
});