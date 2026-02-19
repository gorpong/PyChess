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

        // Don't intercept if dialog is open (except Escape)
        if (isDialogOpen() && event.key !== 'Escape') {
            return;
        }

        switch (event.key.toLowerCase()) {
            case 'u':
                // Undo
                event.preventDefault();
                htmxPost('/api/undo', '#game-container');
                break;

            case 'escape':
                // Clear selection or close dialog
                event.preventDefault();
                if (isDialogOpen()) {
                    // Try to cancel save dialog
                    htmxPost('/api/cancel-save', '#game-container');
                } else {
                    // Clear selection by clicking empty area - just refresh state
                    htmxPost('/api/cancel-save', '#game-container');
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
