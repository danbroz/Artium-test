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

    function formatAuthors(authors) {
        if (!authors || authors.length === 0) return 'Unknown Authors';
        
        if (authors.length === 1) {
            return authors[0];
        } else if (authors.length === 2) {
            return `${authors[0]} & ${authors[1]}`;
        } else {
            return `${authors[0]} et al.`;
        }
    }

    function formatYear(year) {
        return year ? `(${year})` : '(n.d.)';
    }

    function formatAPA(paper) {
        const authors = formatAuthors(paper.authors);
        const year = formatYear(paper.year);
        const title = paper.title.endsWith('.') ? paper.title : `${paper.title}.`;
        
        // Create the base citation
        let citation = `${authors} ${year} ${title}`;
        
        // Add DOI if available
        if (paper.doi) {
            citation += ` <a href="https://doi.org/${paper.doi}" target="_blank" class="text-primary">DOI: ${paper.doi}</a>`;
        }
        
        return citation;
    }

    // Function to display search results
    function displayResults(papers) {
        if (!papers || papers.length === 0) {
            noResultsElement.style.display = 'block';
            return;
        }

        const papersHTML = papers.map((paper, index) => `
            <div class="card paper-card mb-4">
                <div class="card-body">
                    <h5 class="card-title">${index + 1}. ${formatAPA(paper)}</h5>
                    
                    <div class="paper-abstract mb-3">
                        <strong>Abstract:</strong> ${paper.abstract || 'No abstract available.'}
                    </div>
                    
                    <div class="paper-annotation mb-3">
                        <strong>Annotation:</strong> This paper explores ${paper.title.toLowerCase().replace(/\.$/, '')}. 
                        ${paper.abstract ? `The research ${paper.abstract.length > 200 ? 'covers a broad range of topics' : 'focuses on specific aspects'} related to the subject matter.` : ''}
                        ${paper.citations ? `It has been cited ${paper.citations} times, indicating its ${paper.citations > 100 ? 'significant' : 'moderate'} impact in the field.` : ''}
                    </div>
                </div>
            </div>
        `).join('');

        resultsContainer.innerHTML = `
            <div class="results-header mb-4">
                <h3>Search Results (${papers.length} papers found)</h3>
                <p class="text-muted">Results are formatted in APA style with annotations.</p>
            </div>
            ${papersHTML}
        `;
    }
}); 