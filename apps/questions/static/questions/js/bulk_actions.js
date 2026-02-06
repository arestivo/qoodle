/**
 * Bulk actions for question template list.
 * Handles selection state, action bar visibility, and form submissions.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Selection state - persists across pagination using sessionStorage
    const STORAGE_KEY = 'bulkTemplateSelection';
    let selectedIds = new Set(JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '[]'));

    // DOM elements
    const checkboxes = document.querySelectorAll('.template-checkbox');
    const selectAllBtn = document.getElementById('selectAllBtn');
    const selectNoneBtn = document.getElementById('selectNoneBtn');
    const bulkActionBar = document.getElementById('bulkActionBar');
    const selectedCountEl = document.getElementById('selectedCount');
    const clearSelectionBtn = document.getElementById('clearSelectionBtn');
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    const deleteConfirmModal = document.getElementById('deleteConfirmModal');
    const deleteCountEl = document.getElementById('deleteCount');
    const bulkMoveForm = document.getElementById('bulkMoveForm');
    const bulkDeleteForm = document.getElementById('bulkDeleteForm');

    // Initialize checkboxes from stored state
    function initializeCheckboxes() {
        checkboxes.forEach(checkbox => {
            const templateId = checkbox.dataset.templateId;
            checkbox.checked = selectedIds.has(templateId);
        });
        updateUI();
    }

    // Save selection state to sessionStorage
    function saveSelection() {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...selectedIds]));
    }

    // Update UI based on selection state
    function updateUI() {
        const count = selectedIds.size;

        // Update count display
        if (selectedCountEl) {
            selectedCountEl.textContent = count;
        }
        if (deleteCountEl) {
            deleteCountEl.textContent = count;
        }

        // Show/hide action bar
        if (bulkActionBar) {
            if (count > 0) {
                bulkActionBar.classList.remove('d-none');
            } else {
                bulkActionBar.classList.add('d-none');
            }
        }
    }

    // Handle checkbox change
    function handleCheckboxChange(event) {
        const checkbox = event.target;
        const templateId = checkbox.dataset.templateId;

        if (checkbox.checked) {
            selectedIds.add(templateId);
        } else {
            selectedIds.delete(templateId);
        }

        saveSelection();
        updateUI();
    }

    // Select all visible templates
    function selectAll() {
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            selectedIds.add(checkbox.dataset.templateId);
        });
        saveSelection();
        updateUI();
    }

    // Deselect all templates
    function selectNone() {
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        selectedIds.clear();
        saveSelection();
        updateUI();
    }

    // Clear selection (same as select none)
    function clearSelection() {
        selectNone();
    }

    // Add hidden inputs with selected IDs to a form
    function addSelectedIdsToForm(form) {
        // Remove any existing template_ids inputs
        form.querySelectorAll('input[name="template_ids"]').forEach(el => el.remove());

        // Add hidden inputs for each selected ID
        selectedIds.forEach(id => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'template_ids';
            input.value = id;
            form.appendChild(input);
        });
    }

    // Handle move form submission
    function handleMoveSubmit(event) {
        if (selectedIds.size === 0) {
            event.preventDefault();
            alert('Please select at least one template.');
            return;
        }

        const subjectSelect = document.getElementById('moveSubjectSelect');
        if (!subjectSelect.value) {
            event.preventDefault();
            alert('Please select a destination subject.');
            return;
        }

        addSelectedIdsToForm(bulkMoveForm);
        // Clear selection after successful submission
        sessionStorage.removeItem(STORAGE_KEY);
    }

    // Handle delete button click - show confirmation modal
    function handleDeleteClick() {
        if (selectedIds.size === 0) {
            alert('Please select at least one template.');
            return;
        }

        // Update count in modal
        if (deleteCountEl) {
            deleteCountEl.textContent = selectedIds.size;
        }

        // Show modal
        const modal = new bootstrap.Modal(deleteConfirmModal);
        modal.show();
    }

    // Handle delete form submission
    function handleDeleteSubmit(event) {
        addSelectedIdsToForm(bulkDeleteForm);
        // Clear selection after successful submission
        sessionStorage.removeItem(STORAGE_KEY);
    }

    // Event listeners
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleCheckboxChange);
    });

    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', selectAll);
    }

    if (selectNoneBtn) {
        selectNoneBtn.addEventListener('click', selectNone);
    }

    if (clearSelectionBtn) {
        clearSelectionBtn.addEventListener('click', clearSelection);
    }

    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', handleDeleteClick);
    }

    if (bulkMoveForm) {
        bulkMoveForm.addEventListener('submit', handleMoveSubmit);
    }

    if (bulkDeleteForm) {
        bulkDeleteForm.addEventListener('submit', handleDeleteSubmit);
    }

    // Initialize on page load
    initializeCheckboxes();
});
