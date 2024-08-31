console.log("Sanity check!");

// Get Stripe publishable key
fetch("/config/")
.then((result) => { return result.json(); })
.then((data) => {
  const stripe = Stripe(data.publicKey);
  document.querySelector("#submitBtn").addEventListener("click", () => {
    fetch("/create_checkout_session/")
    .then((result) => { return result.json(); })
    .then((data) => {
      console.log(data);
      // Redirect to Stripe Checkout
      return stripe.redirectToCheckout({sessionId: data.sessionId})
    })
    .then((res) => {
      console.log(res);
    });
  });
});


// toggle code

document.addEventListener('DOMContentLoaded', function () {
  const menuButton = document.getElementById('menu');
  const sidebar = document.getElementById('sidebar');
  
  // Toggle the sidebar visibility when the menu button is clicked
  menuButton.addEventListener('click', function (event) {
    event.stopPropagation(); // Prevent the click event from bubbling up to the document
    if (sidebar.classList.contains('d-none')) {
      sidebar.classList.remove('d-none');
      sidebar.style.display = 'block'; // Ensure the sidebar is visible
    } else {
      sidebar.classList.add('d-none');
      sidebar.style.display = 'none'; // Ensure the sidebar is hidden
    }
  });
  
  // Function to handle clicks outside the sidebar
  function handleClickOutside(event) {
    // Check if the clicked target is outside the sidebar and not the menu button
    if (!sidebar.contains(event.target) && event.target !== menuButton) {
      sidebar.classList.add('d-none');
      sidebar.style.display = 'none'; // Hide the sidebar
    }
  }
  
  // Add event listener for clicks on the document
  document.addEventListener('click', handleClickOutside);

  // Add event listener to prevent closing the sidebar when clicking inside it
  sidebar.addEventListener('click', function(event) {
    event.stopPropagation(); // Prevent the click event from bubbling up to the document
  });
});
