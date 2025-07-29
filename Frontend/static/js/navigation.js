// Navigation highlighting script
console.log('Navigation script file loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('Navigation script loaded');
    
    // Get current path
    const currentPath = window.location.pathname;
    console.log('Current path:', currentPath);
    
    // Get all navigation links
    const navLinks = document.querySelectorAll('nav a[href]');
    console.log('Navigation links found:', navLinks.length);
    
    if (navLinks.length === 0) {
        console.warn('No navigation links found!');
        return;
    }
    
    // Function to highlight a link
    function highlightLink(link) {
        console.log('Highlighting link:', link.getAttribute('href'));
        
        // Remove all possible styling classes
        link.classList.remove('text-[#A0AEC0]', 'hover:text-white', 'text-[#DC4918]', 'hover:text-[#FF6B35]');
        
        // Add active styling classes
        link.classList.add('text-[#DC4918]', 'hover:text-[#FF6B35]');
        
        // Also set inline style as backup
        link.style.color = '#DC4918';
        link.style.fontWeight = '600';
        
        // Add a visual indicator
        link.style.borderBottom = '2px solid #DC4918';
    }
    
    // Function to reset a link to default
    function resetLink(link) {
        console.log('Resetting link:', link.getAttribute('href'));
        
        // Remove active styling classes
        link.classList.remove('text-[#DC4918]', 'hover:text-[#FF6B35]');
        
        // Add default styling classes
        link.classList.add('text-[#A0AEC0]', 'hover:text-white');
        
        // Remove inline styles
        link.style.color = '';
        link.style.fontWeight = '';
        link.style.borderBottom = '';
    }
    
    // Reset all links first
    navLinks.forEach(resetLink);
    
    // Find and highlight the current page
    let foundMatch = false;
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        console.log('Checking link:', href, 'against current path:', currentPath);
        
        // Check if this link matches the current path
        if (href === currentPath || 
            (currentPath === '/' && href === '/') ||
            (currentPath === '/viewer' && href === '/') ||
            (currentPath === '/' && href === '/viewer')) {
            
            console.log('Found match! Highlighting:', href);
            highlightLink(link);
            foundMatch = true;
        }
    });
    
    if (!foundMatch) {
        console.warn('No matching navigation link found for current path:', currentPath);
        console.log('Available links:', Array.from(navLinks).map(link => link.getAttribute('href')));
    } else {
        console.log('Navigation highlighting applied successfully');
    }
}); 