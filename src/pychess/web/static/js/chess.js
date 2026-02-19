/**
 * PyChess Web UI - Keyboard shortcuts and UI enhancements
 */

(function() {
    'use strict';

    /**
     * Check if we're on the game page (has the game board)
     */
    function isGamePage() {
        return document.getElementById('board') !== null;
    }

    /**
     * Check if user is typing in an input field
     */
    function isTyping(event) {
        const target = event.target;
        const tagName = target.tagName.toLowerCase();
        return tagName === 'input' || tagName === 'textarea' || target.isContentEditable;
    }

    /**
     * Check if a modal/dialog is open
     */
    function isDialogOpen() {
        return document.querySelector('.save-dialog-overlay') !== null ||
               document.querySelector('.promotion-overlay') !== null ||
               document.querySelector('.game-over-overlay') !== null;
    }

    /**
     * Trigger an HTMX POST request programmatically
     */
    function htmxPost(url, target) {
        const targetEl = document.querySelector(target);
        if (targetEl && window.htmx) {
            htmx.ajax('POST', url, {target: target, swap: 'innerHTML'});
        }
    }

    /**
     * Handle keyboard shortcuts
     */
    function handleKeydown(event) {
        // Only on game page
        if (!isGamePage()) {
            return;
        }

        // Don't intercept if typing in input
        if (isTyping(event)) {
            return;
        }

        switch (event.key) {
            case 'u':
            case 'U':
                // Undo - but not if dialog is open
                if (!isDialogOpen()) {
                    event.preventDefault();
                    htmxPost('/api/undo', '#game-container');
                }
                break;

            case 'Escape':
                event.preventDefault();
                if (isDialogOpen()) {
                    // Cancel save dialog
                    htmxPost('/api/cancel-save', '#game-container');
                } else {
                    // Clear piece selection
                    htmxPost('/api/clear-selection', '#game-container');
                }
                break;
        }
    }

    /**
     * Initialize keyboard shortcuts
     */
    function init() {
        document.addEventListener('keydown', handleKeydown);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
