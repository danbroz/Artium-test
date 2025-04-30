document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const searchInput = document.getElementById('searchInput');
    const maxResults = document.getElementById('maxResults');
    const searchButton = document.getElementById('searchButton');
    const resultsContainer = document.getElementById('results');
    const loadingElement = document.getElementById('loading');
    const noResultsElement = document.getElementById('noResults');

    // Event listeners
    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    // Function to perform the search
    async function performSearch() {
        const query = searchInput.value.trim();
        if (!query) {
            alert('Please enter a search query');
            return;
        }

        // Show loading state
        loadingElement.style.display = 'block';
        noResultsElement.style.display = 'none';
        resultsContainer.innerHTML = '';

        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    topic: query,
                    max_results: parseInt(maxResults.value)
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            displayResults(data.papers);
        } catch (error) {
            console.error('Error:', error);
            resultsContainer.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    An error occurred while searching. Please try again later.
                </div>
            `;
        } finally {
            loadingElement.style.display = 'none';
        }
    }

    // Function to display search results
    function displayResults(papers) {
        if (!papers || papers.length === 0) {
            noResultsElement.style.display = 'block';
            return;
        }

        const papersHTML = papers.map(paper => `
            <div class="card paper-card">
                <div class="card-body">
                    <h5 class="card-title">
                        <a href="${paper.url}" class="paper-title" target="_blank" rel="noopener noreferrer">
                            ${paper.title}
                        </a>
                    </h5>
                    <p class="card-text">${paper.abstract || 'No abstract available'}</p>
                    <div class="paper-meta">
                        <div>Authors: ${paper.authors.join(', ')}</div>
                        <div>Published: ${paper.published_date || 'Unknown'}</div>
                        <div>Source: ${paper.source}</div>
                    </div>
                </div>
            </div>
        `).join('');

        resultsContainer.innerHTML = papersHTML;
    }
}); 