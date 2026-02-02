// Question form - choice management

const formset = document.getElementById('choice-formset');
const addButton = document.getElementById('add-choice');
const totalForms = document.getElementById('id_choices-TOTAL_FORMS');
const template = document.getElementById('choice-template');

let formIndex = parseInt(totalForms.value);

// Renumber form fields to match DOM order
function renumberForms() {
    const choices = formset.querySelectorAll('.choice-form');
    choices.forEach((choice, index) => {
        // Update all input/textarea names and IDs
        const inputs = choice.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            const name = input.getAttribute('name');
            const id = input.getAttribute('id');
            
            if (name) {
                // Replace choices-X- with choices-{index}-
                const newName = name.replace(/choices-\d+-/, `choices-${index}-`);
                input.setAttribute('name', newName);
            }
            
            if (id) {
                const newId = id.replace(/choices-\d+-/, `choices-${index}-`);
                input.setAttribute('id', newId);
            }
        });
        
        // Update label for attributes
        const labels = choice.querySelectorAll('label');
        labels.forEach(label => {
            const forAttr = label.getAttribute('for');
            if (forAttr) {
                const newFor = forAttr.replace(/choices-\d+-/, `choices-${index}-`);
                label.setAttribute('for', newFor);
            }
        });
    });
    
    // Update total forms count
    totalForms.value = choices.length;
}

// Update choice numbering and correct badge
function updateChoiceNumbers() {
    const choices = formset.querySelectorAll('.choice-form');
    choices.forEach((choice, index) => {
        // Update number badge
        const numberBadge = choice.querySelector('.choice-number');
        if (numberBadge) numberBadge.textContent = index + 1;
        
        // Show/hide correct answer badge
        const correctBadge = choice.querySelector('.correct-badge');
        if (correctBadge) {
            correctBadge.style.display = index === 0 ? 'inline-block' : 'none';
        }
        
        // Enable/disable move buttons
        const moveUp = choice.querySelector('.move-up');
        const moveDown = choice.querySelector('.move-down');
        if (moveUp) moveUp.disabled = index === 0;
        if (moveDown) moveDown.disabled = index === choices.length - 1;
    });
    
    // Renumber forms after updating
    renumberForms();
}

// Add new choice
addButton.addEventListener('click', function() {
    const newForm = template.content.cloneNode(true);
    const formDiv = newForm.querySelector('.choice-form');
    
    // Replace __prefix__ with actual index
    formDiv.innerHTML = formDiv.innerHTML.replace(/__prefix__/g, formIndex);
    formDiv.dataset.choiceIndex = formIndex;
    
    formset.appendChild(formDiv);
    formIndex++;
    
    updateChoiceNumbers();
    attachChoiceEvents(formDiv);
});

// Attach events to a choice form
function attachChoiceEvents(choiceForm) {
    // Move up
    choiceForm.querySelector('.move-up').addEventListener('click', function() {
        const prev = choiceForm.previousElementSibling;
        if (prev) {
            formset.insertBefore(choiceForm, prev);
            updateChoiceNumbers();
        }
    });
    
    // Move down
    choiceForm.querySelector('.move-down').addEventListener('click', function() {
        const next = choiceForm.nextElementSibling;
        if (next) {
            formset.insertBefore(next, choiceForm);
            updateChoiceNumbers();
        }
    });
    
    // Delete
    choiceForm.querySelector('.delete-choice').addEventListener('click', function() {
        if (formset.querySelectorAll('.choice-form').length <= 2) {
            alert('You must have at least 2 choices.');
            return;
        }
        choiceForm.remove();
        updateChoiceNumbers();
    });
}

// Attach events to existing choices
formset.querySelectorAll('.choice-form').forEach(attachChoiceEvents);

// Initial numbering
updateChoiceNumbers();
