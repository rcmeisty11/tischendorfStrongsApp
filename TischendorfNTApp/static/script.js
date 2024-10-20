document.addEventListener('DOMContentLoaded', function () {
    // Fetch content data from the server and populate dropdowns
    const bookDropdown = document.getElementById('bookDropdown');
    const chapterContainer = document.getElementById('chapterContainer');
    const detailsBox = document.getElementById('detailsBox');

    fetch('/load_content')
        .then(response => response.json())
        .then(data => {
            // Create an array of books in the order received from the server
            const bookTitles = Object.keys(data);

            // Ensure books are added to dropdown in the order received from the server
            bookTitles.forEach((bookTitle) => {
                const option = document.createElement('option');
                option.value = bookTitle;
                option.textContent = bookTitle.replace(/_/g, '.'); // Revert sanitization for display
                bookDropdown.appendChild(option);
            });

            // Handle book selection change
            bookDropdown.addEventListener('change', function () {
                const selectedBook = bookDropdown.value;
                chapterContainer.innerHTML = ''; // Clear previous chapters

                if (selectedBook && data[selectedBook]) {
                    const chapters = Object.keys(data[selectedBook]);

                    // Sort chapters numerically
                    chapters.sort((a, b) => {
                        const numA = parseInt(a.split('_').pop(), 10);
                        const numB = parseInt(b.split('_').pop(), 10);
                        return numA - numB;
                    });

                    // Display chapters
                    chapters.forEach(chapterId => {
                        const chapterItem = document.createElement('div');
                        chapterItem.classList.add('accordion-item');

                        const chapterHeader = document.createElement('h2');
                        chapterHeader.classList.add('accordion-header');
                        chapterHeader.id = `heading-${chapterId}`;

                        const button = document.createElement('button');
                        button.classList.add('accordion-button', 'collapsed');
                        button.setAttribute('type', 'button');
                        button.setAttribute('data-bs-toggle', 'collapse');
                        button.setAttribute('data-bs-target', `#collapse-${chapterId}`);
                        button.setAttribute('aria-expanded', 'false');
                        button.setAttribute('aria-controls', `collapse-${chapterId}`);
                        button.textContent = `Chapter ${chapterId.split('_').pop()}`;

                        const chapterCollapse = document.createElement('div');
                        chapterCollapse.id = `collapse-${chapterId}`;
                        chapterCollapse.classList.add('accordion-collapse', 'collapse');
                        chapterCollapse.setAttribute('aria-labelledby', `heading-${chapterId}`);
                        chapterCollapse.setAttribute('data-bs-parent', '#chapterContainer');

                        const chapterBody = document.createElement('div');
                        chapterBody.classList.add('accordion-body');

                        // Add verses to the chapter body
                        const verses = data[selectedBook][chapterId];
                        verses.forEach(verse => {
                            const verseElement = document.createElement('p');
                            verseElement.innerHTML = `<strong>${verse.verse_id}</strong>: ${formatVerseText(verse.words_info)}`;
                            chapterBody.appendChild(verseElement);
                        });

                        chapterCollapse.appendChild(chapterBody);
                        chapterHeader.appendChild(button);
                        chapterItem.appendChild(chapterHeader);
                        chapterItem.appendChild(chapterCollapse);
                        chapterContainer.appendChild(chapterItem);
                    });

                    // Initialize Bootstrap tooltips
                    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
                        new bootstrap.Tooltip(tooltipTriggerEl);
                    });
                }
            });
        })
        .catch(error => console.error('Error loading content:', error));
});

// Helper function to format verse text with tooltips for each word and click event listener
function formatVerseText(wordsInfo) {
    return wordsInfo.map(word => {
        const tooltipText = `
            Lemma: ${word.lemma || 'N/A'}<br>
            Morphology: ${word.morph || 'N/A'}<br>
            Strong's Number: ${word.strong || 'N/A'}<br>
            Definition: ${word.definition || 'N/A'}
        `;
        return `<span class="word" data-bs-toggle="tooltip" data-bs-html="true" title="${tooltipText}" onclick="showWordDetails('${word.text}', '${word.lemma}', '${word.morph}', '${word.strong}', '${word.definition}')">${word.text}</span>`;
    }).join(' ');
}

