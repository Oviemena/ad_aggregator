function trackClick(adId) {
    const data = {
        ad_id: adId,
    };
    
    console.log('Sending tracking data:', data);  // Debug log
    
    fetch('http://localhost:5000/track', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => console.log('Track success:', result))
    .catch(err => console.error('Track error:', err));
}

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Tracker script loaded');  // Debug log
    
    document.querySelectorAll('.ad').forEach(ad => {
        console.log('Found ad:', ad.dataset.adId);  // Debug log
        ad.addEventListener('click', () => {
            console.log('Ad clicked:', ad.dataset.adId);  // Debug log
            trackClick(ad.dataset.adId);
        });
    });
});